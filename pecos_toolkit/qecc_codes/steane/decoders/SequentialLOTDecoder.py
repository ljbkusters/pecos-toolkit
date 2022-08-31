#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Syndrome.py
@author Luc Kusters
@date 07-06-2022
"""

import collections
import numpy

from pecos_toolkit.qecc_codes.steane.circuits import Steane
from pecos_toolkit.qecc_codes.steane.data_types import RNNDataTypes
from pecos_toolkit.qecc_codes.steane.data_types import Syndrome
from pecos_toolkit.qecc_codes.steane.data_types import Plaquette
from pecos_toolkit.qecc_codes.steane.decoders import BasicLOTDecoder


class SequentialLOTDecoder(object):

    CODE_DATA = Steane.BaseSteaneData

    def __init__(self):
        self.basic_lot_decoder = BasicLOTDecoder.SteaneSyndromeDecoder()

    def decode_sequence(self, sequence_data):
        seq_data_len = len(sequence_data)
        num_data_qubits = len(self.CODE_DATA.DATA_QUBITS)
        corrections = numpy.zeros((seq_data_len, 2, num_data_qubits),
                                  dtype=bool)
        print(corrections)
        for time_step in range(seq_data_len):
            correction = self.correction_per_time_step(sequence_data,
                                                       time_step)
            corrections[time_step, :, :] = numpy.asarray(correction)
        compiled_corrections = {
                "X": self.compile_corrections(corrections[:, 0, :]),
                "Z": self.compile_corrections(corrections[:, 1, :])
            }
        return compiled_corrections

    def unpack_sequence_step(self, sequence_data, time_step):
        """Unpack the sequence data for a time_step
        """
        if isinstance(sequence_data, RNNDataTypes.RNNSyndromeData):
            return self.unpack_RNNSyndromeData(sequence_data, time_step)
        elif isinstance(sequence_data, numpy.ndarray):
            return self.unpack_vectorized_sequence(sequence_data, time_step)

    def unpack_RNNSyndromeData(self, sequence_data, time_step):
        return (sequence_data.x_syndrome_increments(time_step),
                sequence_data.x_flags(time_step),
                sequence_data.z_syndrome_increments(time_step),
                sequence_data.z_flags(time_step))

    def unpack_vectorized_sequence(self, sequence_data, time_step):
        return (sequence_data[time_step][:3],
                sequence_data[time_step][3:6],
                sequence_data[time_step][6:9],
                sequence_data[time_step][9:12])

    def correction_per_time_step(self, sequence_data, time_step):
        x_syninc, _, z_syninc, _ = \
            self.unpack_sequence_step(sequence_data, time_step)
        if time_step == 0:
            x_flags_last = None
            z_flags_last = None
        else:
            _, x_flags_last, _, z_flags_last = \
                self.unpack_sequence_step(sequence_data, time_step - 1)
        x_correction = self.correction_for_syndrome_data(x_syninc,
                                                         z_flags_last)
        z_correction = self.correction_for_syndrome_data(z_syninc,
                                                         x_flags_last)
        return x_correction, z_correction

    def correction_for_syndrome_data(self, syninc, flags_last):
        if flags_last is None or sum(flags_last) == 0 or sum(flags_last) > 1:
            # return default decoder
            decoder = self.basic_lot_decoder
        elif sum(flags_last) == 1:
            plaq_idx = numpy.where(numpy.asarray(flags_last) == 1)[0][0]
            plaq = self.CODE_DATA.plaquettes[plaq_idx]
            decoder = BasicLOTDecoder.FlaggedSyndromeDecoder(plaq)
            # return default flagged decoder
        else:
            raise NotImplementedError("This should not occur!")
        syndrome = Syndrome.Syndrome(None, *syninc)
        qubits = decoder.cor_qubit(syndrome)
        if not hasattr(qubits, "__iter__"):
            qubits = (qubits,)
        return self.qubits_to_correction_vector(qubits)

    def compile_corrections(self, corrections):
        corrections = numpy.sum(numpy.asarray(corrections), axis=0) % 2
        return corrections

    def correction_vector_to_qubits(self, correction_vector):
        """return a tuple qubits on which a correction should be applied"""
        x = numpy.where(numpy.asarray(correction_vector) == 1)[0]
        return x

    def qubits_to_correction_vector(self, qubits):
        """return an array of bits representing if a correction on this
        qubit must be applied"""
        return numpy.fromiter(
                (1 if i in qubits else 0
                 for i in self.CODE_DATA.DATA_QUBITS), dtype=bool)

    def correction_logical_weight(self, correction):
        """Wrapper around basic_lot_dict.corrected_classical_logical_parity"""
        return self.basic_lot_decoder.corrected_classical_logical_parity(
                correction)

    def corrections_dict_logical_weight(self, corrections_dict):
        logical_weight_dict = {key: self.correction_logical_weight(val)
                               for key, val in corrections_dict.items()}
        return logical_weight_dict
