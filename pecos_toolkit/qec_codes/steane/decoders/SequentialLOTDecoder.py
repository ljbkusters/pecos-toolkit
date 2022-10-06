#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Syndrome.py
@author Luc Kusters
@date 07-06-2022
"""

import collections
import enum
import numpy

from pecos_toolkit.qec_codes.steane.circuits import Steane
from pecos_toolkit.qec_codes.steane.data_types import RNNDataTypes
from pecos_toolkit.qec_codes.steane.data_types import Syndrome
from pecos_toolkit.qec_codes.steane.data_types import Plaquette
from pecos_toolkit.qec_codes.steane.decoders import AbstractSequentialDecoder
from pecos_toolkit.qec_codes.steane.decoders import BasicLOTDecoder


class SequentialLOTDecoder(AbstractSequentialDecoder
                           .AbstractSequentialDecoder):
    """
    Decode sequence:

    0 -E- S1 - - S2 -E- S3 - - S4
    ^ D01    D12    D23    D34

    0 -E- S1 - - S2 -E- S3 - - S4
      D01 ^  D12    D23
         syndrome increment detected in DS01 goto next
         (signal)

    0 -E- S1 - - S2 -E- S3 - - S4
      DS01  DS12 ^  DS23
        S1 = S2, apply C based on S2

                 C
    0 -E- S1 - - S2 -E- S3 - - S4
      DS01  DS12   DS23 ^
                    since a correction was applied in the last round
                    compare syndrome S3 with S1 and correct based on that

    LOOP OVER DATA:
        o - - o - - o - - o (- - o)

    Chamberland F1FTEC Condition:

    Measure S1, S2
    ([L0]: if S1=S2, and S1, S2 = 0 do nothing)
    [CH1]: if S1=S2, correct with S = S1 = S2
    [CH2]: if S1=/=S2, measure S3 and correct with S3
    [CH3]: if at any point a circuit flags, measure once more
           and correct with modified lookup table

    in delta S image:

    Add S0 = 0
    [D0]: if D01 = 0, do nothing  (SIGNAL NONE)
    [D1]: if D01 > 0, (S0=/=S1)  (SIGNAL INCREMENTED)
                      measure S2 (giving D12) and correct with S2
                      DS12 = S2 - S1, DS01 = S1 - S0
                      DS12 + DS01 = S2 - S1 + S1 - S0 = S2
                      i.e. correct with S2 = DS12 + DS01
    [D2]: if FLAGGED, (SIGNAL FLAG) measure one more S and correct with CF(S)
    [D2.1]: if the last measurement is Flagged, ignore the flags
    [D3]: After a correction, update the next delta by adding D0,x to Dx,x+1
          (This )



        SIGNAL = None, FLAG, INCREMENT
    

    Algorithm:
    # data = P_stab, NOT-P_flag (i.e. X_stab, Z_flag and v.v.)
    for data in (X, Z): 

        s0 = 0
        signal = NONE

        for step in data:
            if signal == NONE:
                # determine new signal from data
            elif signal == FLAG:
                # correct flag event
            elif signal == INCREMENT:
                # correct syndrome increment
    """

    CODE_DATA = Steane.BaseSteaneData

    class Signal(enum.Enum):
        NONE = 0
        INCREMENT = 1
        FLAG = 2

    class SequenceData(collections.namedtuple(
            "SequenceData", ("x_inc x_flg z_inc z_flg"))):

        @property
        def x_syndrome_data(self):
            return self.x_inc, self.z_flg

        @property
        def z_syndrome_data(self):
            return self.z_inc, self.x_flg

    def __init__(self, verbose=False):
        self.basic_lot_decoder = BasicLOTDecoder.SteaneSyndromeDecoder()
        self.verbose = verbose

    def decode_sequence_to_parity(self, sequence_data, input_parity,
                                  basis=None):
        """Decode a sequence of data to logical error parity

        Wraps around the decode_sequence_to_corrections and determines
        the logical weight of the suggested correction.
        """
        compiled_corrections = self.decode_sequence_to_correction(
                sequence_data)
        correction_parities = {key: self.correction_logical_weight(val)
                               for key, val in compiled_corrections.items()}
        expected_logical_parities = {key: (input_parity + val) % 2
                                     for key, val
                                     in correction_parities.items()}
        if basis is None:
            return expected_logical_parities
        elif basis in ("X", "Z"):
            return expected_logical_parities[basis]
        else:
            raise ValueError("Basis should be one of (None, 'X', 'Z')")

    def decode_sequence_to_correction(self, sequence_data):
        """Decode a sequence of data to corrections

        Determines the best correction based on reasonable assumptions
        about the error model and syndrome data.
        """
        if isinstance(sequence_data, numpy.ndarray):
            # remove -1 mask if present
            sequence_data = sequence_data[(sequence_data >= 0).all(axis=1)]

        seq_data_len = len(sequence_data)
        corrections = {"X": [], "Z": []}

        for error_basis, corr_list in corrections.items():
            increments, flags = self.unpack_sequence(sequence_data,
                                                     error_basis)
            # print(error_basis)
            # print(f"increments\n{increments}\nflags\n{flags}")
            signal = self.Signal.NONE
            s0 = 0
            for time_step in range(seq_data_len):
                if signal == self.Signal.NONE:
                    signal, s0 = self._handle_signal_NONE(
                            error_basis, increments, flags, time_step, s0)
                    continue
                else:
                    if signal == self.Signal.FLAG:
                        correction = self._handle_signal_FLAG(
                            error_basis, increments, flags, time_step, s0)
                    elif signal == self.Signal.INCREMENT:
                        correction = self._handle_signal_INCREMENT(
                            error_basis, increments, flags, time_step, s0)
                    corr_list.append(correction)
                    # reset signal after correction
                    signal = self.Signal.NONE
                    s0 = time_step
                    continue

        compiled_corrections = {basis: self.compile_corrections(c)
                                for basis, c in corrections.items()}
        return compiled_corrections

    def relative_increment(self, increments, *t):
        if self.verbose:
            print(t)
            for t_ in t:
                print(increments[t_])
        return numpy.sum(increments[t_] for t_ in t).astype(int) % 2

    def _handle_signal_FLAG(self, basis, increments, flags, time_step, s0):
        # print("handling flag")
        if self.verbose:
            print(increments)
            print(flags)
        flag = flags[time_step - 1]
        inc = self.relative_increment(increments,
                                      *list(range(s0, time_step+1)))
        syndrome = Syndrome.Syndrome(None, *inc)
        plaq_idx = numpy.where(flag == 1)[0][0]
        plaq = self.CODE_DATA.plaquettes[plaq_idx]
        modified_decoder = BasicLOTDecoder.FlaggedSyndromeDecoder(plaq)
        qubits = modified_decoder.cor_qubit(syndrome)
        if self.verbose:
            print(inc, qubits)
        return self.qubits_to_correction_vector(qubits)

    def _handle_signal_INCREMENT(self, basis, increments,
                                 flags, time_step, s0):
        # print("handling increment")
        inc = self.relative_increment(increments,
                                      *list(range(s0, time_step+1)))
        syndrome = Syndrome.Syndrome(None, *inc)
        qubits = (self.basic_lot_decoder.cor_qubit(syndrome),)
        return self.qubits_to_correction_vector(qubits)

    def _handle_signal_NONE(self, basis, increments, flags, time_step, s0):
        # print("handling none")
        if numpy.sum(flags[time_step]) == 1:
            signal = self.Signal.FLAG
        elif numpy.sum(increments[time_step]) == 1:
            signal = self.Signal.INCREMENT
        else:
            signal = self.Signal.NONE
            s0 = time_step
        return signal, s0

    def unpack_sequence(self, sequence_data, error_basis=None):
        """Unpack the sequence data for a time_step"""
        if isinstance(sequence_data, RNNDataTypes.RNNSyndromeData):
            sequence_data = sequence_data.to_vector(dtype=bool)
        sequence = self.unpack_vectorized_sequence(sequence_data)
        if error_basis is None:
            return sequence
        elif error_basis == "X":
            return sequence.z_syndrome_data
        elif error_basis == "Z":
            return sequence.x_syndrome_data

    def unpack_vectorized_sequence(self, sequence_data):
        return self.SequenceData(
                sequence_data[:, :3],
                sequence_data[:, 3:6],
                sequence_data[:, 6:9],
                sequence_data[:, 9:12])

    def compile_corrections(self, corrections):
        if len(corrections) == 0:
            return numpy.zeros(len(list(self.CODE_DATA.DATA_QUBITS)),
                               dtype=int)
        else:
            return numpy.sum(numpy.asarray(corrections).astype(int),
                             axis=0) % 2

    def correction_vector_to_qubits(self, correction_vector):
        """return a tuple qubits on which a correction should be applied"""
        return numpy.where(numpy.asarray(correction_vector) == 1)[0]

    def qubits_to_correction_vector(self, qubits):
        """return an array of bits representing if a correction on this
        qubit must be applied"""
        if qubits is None:
            return numpy.zeros(len(self.CODE_DATA.DATA_QUBITS), dtype=bool)
        else:
            return numpy.fromiter(
                    (1 if i in qubits else 0
                     for i in self.CODE_DATA.DATA_QUBITS), dtype=bool)

    def correction_logical_weight(self, correction):
        """Wrapper around basic_lot_dict.corrected_classical_logical_parity"""
        return self.basic_lot_decoder.corrected_classical_logical_parity(
                correction)

        """
        for time_step in range(seq_data_len):
            print(f"time_step: {time_step}")
            print(f"signal: {self.signal}")
            if self.signal is None:
                if numpy.sum(step_data.x_flg) == 1:
                    # a flag occured, correct with CF(S) in next round
                    print("setting signal to FLAG")
                elif numpy.sum(step_data.z_inc) > 0:
                    # syndormes did not match, correct with C(S) in next round
                    self.signal = "INC"
                    print("setting signal to INC")
                    continue
                else:
                    # nothing happened, do nothing
                    print(f"setting signal to None, s0 to {time_step}")
                    s0 = time_step
                    self.signal = None
                    continue
            elif self.signal == "FLAG":
                print("Correcting for FLAG")
                # correct with CF(S) relative to s0, then set s0 to this index
                flags_last = self.unpack_sequence_step(
                        sequence_data, time_step - 1).x_flag
                syndrome = numpy.sum(
                        self.unpack_sequence_step(sequence_data, x).z_inc
                        for x in range(s0, time_step + 1)) % 2
                syndrome = Syndrome.Syndrome(None, *syndrome)
                plaq_idx = numpy.where(numpy.asarray(flags_last) == 1)[0][0]
                plaq = self.CODE_DATA.plaquettes[plaq_idx]
                modified_decoder = BasicLOTDecoder.FlaggedSyndromeDecoder(plaq)
                qubits = modified_decoder.cor_qubits(syndrome)
                x_corrections.append(
                        self.qubits_to_correction_vector(qubits))
                s0 = time_step
                self.signal = None
            elif self.signal == "INC":
                print("Correcting for INC")
                # correct with C(S) relative to s0, then set s0 to this index
                print(s0, time_step)
                syndromes = numpy.fromiter(
                        (self.unpack_sequence_step(sequence_data, x).z_inc
                         .astype(int)
                         for x in (s0, time_step)), dtype=object)
                print("syndromes")
                print(syndromes)
                syndrome = numpy.sum(syndromes) % 2
                print("final syndrome")
                print(syndrome)
                syndrome = Syndrome.Syndrome(None, *syndrome)
                qubits = (self.basic_lot_decoder.cor_qubit(syndrome),)
                print(qubits)
                print(f"setting s0 to {time_step}")
                s0 = time_step
                x_corrections.append(
                        self.qubits_to_correction_vector(qubits))
                s0 = time_step
                self.signal = None

        z_corrections = []
        s0 = 0
        self.signal = None
        print(10*"=")
        print("Correcting Z errors on X syndrome...")
        for time_step in range(seq_data_len):
            print(f"time_step: {time_step}")
            print(f"signal: {self.signal}")
            step_data = self.unpack_sequence_step(sequence_data, time_step)
            if self.signal is None:
                if numpy.sum(step_data.z_flg) == 1:
                    print("setting signal to FLAG")
                    # a flag occured, correct with CF(S) in next round
                    self.signal = "FLAG"
                    continue
                elif numpy.sum(step_data.x_inc) > 0:
                    print("setting signal to INC")
                    # syndormes did not match, correct with C(S) in next round
                    self.signal = "INC"
                    continue
                else:
                    print(f"setting signal to None, s0 to {time_step}")
                    # nothing happened, do nothing
                    s0 = time_step
                    self.signal = None
                    continue
            elif self.signal == "FLAG":
                print("Correcting for FLAG")
                # correct with CF(S) relative to s0, then set s0 to this index
                flags_last = self.unpack_sequence_step(
                        sequence_data, time_step - 1).z_flag
                syndrome = numpy.sum(
                        self.unpack_sequence_step(sequence_data, x).x_inc
                        .astype(int)
                        for x in range(s0, time_step + 1)) % 2
                syndrome = Syndrome.Syndrome(None, *syndrome)
                plaq_idx = numpy.where(numpy.asarray(flags_last) == 1)[0][0]
                plaq = self.CODE_DATA.plaquettes[plaq_idx]
                modified_decoder = BasicLOTDecoder.FlaggedSyndromeDecoder(plaq)
                qubits = modified_decoder.cor_qubits(syndrome)
                z_corrections.append(
                        self.qubits_to_correction_vector(qubits))
                s0 = time_step
                self.signal = None
            elif self.signal == "INC":
                print("Correcting for INC")
                # correct with C(S) relative to s0, then set s0 to this index
                syndromes = numpy.fromiter(
                        (self.unpack_sequence_step(sequence_data, x).x_inc
                         for x in (s0, time_step)), dtype=object)
                print("syndromes:", syndromes)
                syndrome = numpy.sum(syndromes)
                print("syndrome:", syndrome)
                syndrome = numpy.sum(syndromes) % 2
                print("syndrome % 2:", syndrome)
                syndrome = Syndrome.Syndrome(None, *syndrome)
                qubits = (self.basic_lot_decoder.cor_qubit(syndrome),)
                print("qubits:", qubits)
                print("setting s0 to", time_step)
                z_corrections.append(
                        self.qubits_to_correction_vector(qubits))
                s0 = time_step
                self.signal = None
                """
