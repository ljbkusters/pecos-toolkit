#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
steane.py
@author Luc Kusters
@date 07-06-2022
"""

import collections

# from toolkits.error_generator_toolkit import ErrorGenerator
from pecos_toolkit.circuit_runner import ImprovedRunner
from pecos_toolkit.qecc_codes.steane.circuits import Logical
from pecos_toolkit.qecc_codes.steane.circuits import Measurement
from pecos_toolkit.qecc_codes.steane.circuits import Steane
from pecos_toolkit.qecc_codes.steane.circuits import Verification
from pecos_toolkit.qecc_codes.steane.data_types import Syndrome


RUNNER = ImprovedRunner(random_seed=True)


class SteaneProtocol(object):
    """Namespace for basic steane code"""

    SyndromeMeasResults = collections.namedtuple(
            "SyndromeMeasResults", "syndrome faults")

    @staticmethod
    def init_physical_zero(*args, **kwargs):
        circ = Steane.InitPhysicalZero()
        return RUNNER.run(circ.simulator(), circ, *args, **kwargs)

    @staticmethod
    def init_logical_zero(*args, **kwargs):
        circ = Logical.LogicalZeroInitialization()
        return RUNNER.run(circ.simulator(), circ, *args, **kwargs)

    @staticmethod
    def init_logical_one(*args, **kwargs):
        state = SteaneProtocol.init_logical_zero(*args, **kwargs).state
        return RUNNER.run(Logical.LogicalPauli("X"), state, *args, **kwargs)

    @staticmethod
    def idle_data_qubits(state, *args, **kwargs):
        circ = Steane.IdleDataBlock()
        return RUNNER.run(state, circ, *args, **kwargs)

    @staticmethod
    def measure_stabilizers(state, stabilizers, *args, **kwargs):
        """Measure a set of stabilizers on a given state

        Args:
            state: pecos simulator state
            stabilizers: iterable of stabilizers
            *args, **kwargs passed to RUNNER.run()
        Returns:
            list of measurements (measurement qubit only)
            list of faults (if error generator was used)
        """
        syndromes = []
        faults = []
        for stab in stabilizers:
            circ = Measurement.StabMeasCircuit(stab)
            res = RUNNER.run(state, circ, *args, **kwargs)
            meas = res.measurements.first()
            syndromes.append(meas.syndrome[circ.ANCILLA_QUBIT])
            faults.append(res.faults)
        syndrome = Syndrome.Syndrome(stabilizers[0].pauli_type, *syndromes)
        return SteaneProtocol.SyndromeMeasResults(syndrome, faults)

    @staticmethod
    def measure_x_stabilizers(state, *args, **kwargs):
        return SteaneProtocol.measure_stabilizers(
                state, Steane.BaseSteaneData.x_stabilizers, *args, **kwargs)

    @staticmethod
    def measure_z_stabilizers(state, *args, **kwargs):
        return SteaneProtocol.measure_stabilizers(
                state, Steane.BaseSteaneData.z_stabilizers, *args, **kwargs)

    @staticmethod
    def correct_from_syndrome(state, syndrome: Syndrome.Syndrome,
                              *args, **kwargs):
        decoder = Syndrome.SteaneSyndromeDecoder()
        corr_qubit, corr_pauli_type = decoder.lot_decoder(syndrome)
        if corr_qubit is not None:
            circ = Steane.SingleQubitPauli(corr_pauli_type, corr_qubit)
        else:
            circ = Steane.BaseSteaneCirc()
        res = RUNNER.run(state, circ, *args, **kwargs)
        return res

    @staticmethod
    def x_steane_round(state, *args, **kwargs):
        meas_res = SteaneProtocol.measure_x_stabilizers(state, *args, **kwargs)
        return SteaneProtocol.correct_from_syndrome(state, meas_res.syndrome,
                                                    *args, **kwargs)

    @staticmethod
    def z_steane_round(state, *args, **kwargs):
        meas_res = SteaneProtocol.measure_z_stabilizers(state, *args, **kwargs)
        return SteaneProtocol.correct_from_syndrome(state, meas_res.syndrome,
                                                    *args, **kwargs)

    @staticmethod
    def full_steane_round(state, *args, **kwargs):
        state, meas, fault = SteaneProtocol.x_steane_round(state, *args,
                                                           **kwargs)
        state, meas, fault = SteaneProtocol.z_steane_round(state, *args,
                                                           **kwargs)
        return state, meas, fault

    @staticmethod
    def measure_data_state(state, *args, **kwargs):
        circ = Measurement.DataStateMeasurement()
        res = RUNNER.run(state, circ, *args, **kwargs)
        return res

    def classical_correction_decoding(data_syndrome):
        """ decode a codeword with classical correction

        a minimum_distance correction is applied to simulate a round
        of classical error correction. If the distance to a logical 0
        codeword is smaller than the distance to a logical 1 codeword,
        one can assume that the state should have encoded a logical 0
        (and vice versa).  If both distances are 2, None is again
        returned because no clear preference can be made for either
        a logical 0 or logical 1.
        """
        data = Steane.BaseSteaneData()
        zero_code_word_distance = \
            data.min_distance_to_logical_codewords(data_syndrome, 0)
        one_code_word_distance = \
            data.min_distance_to_logical_codewords(data_syndrome, 1)
        if zero_code_word_distance < one_code_word_distance:
            return 0
        elif zero_code_word_distance > one_code_word_distance:
            return 1
        elif (zero_code_word_distance == 2 and
              one_code_word_distance == 2):
            return None
        else:
            raise RuntimeError("I think this case should not occur but"
                               " maybe it does???")

    @staticmethod
    def decode_data_codeword(syndrome, with_classical_correction=False):
        """Get the codeword type from the data state measurement

        If a measurement syndrome is a logical 0 or logical 1 codeword
        (defined by the stabilizers for logical 0 and a stabilizer +
        logical for logical 1) it will return  0 or 1 respectively.
        Otherwise it will return None (as it is neither a logical 0 or
        1 state).

        If with_classical_correction is set to True, the classical
        correction decoder is used as well

        Args:
            syndrome, measurement syndrome of data qubits
            with_classical_correction, bool to switch on classical error
                                       correction simulation
        Returns:
            best guess for logical state (0 or 1) or None if no preference
            can be determined.
        """
        data = Steane.BaseSteaneData()
        min_qubit = min(data.DATA_QUBITS)
        max_qubit = max(data.DATA_QUBITS)
        data_syndrome = tuple(syndrome[min_qubit:max_qubit+1])
        if data_syndrome in data.logical_zero_codewords:
            return 0
        elif data_syndrome in data.logical_one_codewords:
            return 1
        else:
            if with_classical_correction:
                return SteaneProtocol.classical_correction_decoding(
                        data_syndrome)
            else:
                return None


class F1FTECProtocol(object):
    """Namespace for F1FTEC Protocol"""

    SyndromeMeasResults = collections.namedtuple(
            "SyndromeMeasResults", "syndrome flag_syndrome faults")

    @staticmethod
    def verified_init_logical_zero(*args, **kwargs):
        verification_circ = Verification.VerifyLogicalZeroStateCirc()
        flag_bit = verification_circ.FLAG_QUBIT
        while True:
            state = SteaneProtocol.init_logical_zero(*args, **kwargs).state
            res = RUNNER.run(state, verification_circ, *args, **kwargs)
            flagged = bool(res.measurements.last().syndrome[flag_bit])
            if not flagged:
                break
        return res

    @staticmethod
    def flag_measure_stabilizer(state, stab, *args, **kwargs):
        circ = Measurement.F1FTECStabMeasCircuit(stab)
        return RUNNER.run(state, circ, *args, **kwargs)

    @staticmethod
    def f1ftec_round(state, *args, **kwargs):
        syndrome = {}
        ancilla_qubit = Measurement.F1FTECStabMeasCircuitData.ANCILLA_QUBIT
        x_stabs = Steane.BaseSteaneData.x_stabilizers
        z_stabs = Steane.BaseSteaneData.z_stabilizers
        for pauli_type, stabs in {"X": x_stabs, "Z": z_stabs}.items():
            syndrome[pauli_type] = []
            for i in range(2):
                syndrome[pauli_type].append([])
                for stab in stabs:
                    res = F1FTECProtocol.flag_measure_stabilizer(
                        state, stab, *args, **kwargs)
                    bit = res.measurements.last().syndrome[ancilla_qubit]
                    syndrome[pauli_type][i].append(bit)
                    # if a flag occurs, stop and do non-FT meas + modified
                    # correction based on which circuit (stab) flagged
                    if F1FTECProtocol.is_flagged(res):
                        # print("detected flag")
                        return F1FTECProtocol.correct_from_flagged_circuit(
                                state, stabs, stab, *args, **kwargs)
                syndrome[pauli_type][i] = \
                    Syndrome.Syndrome(pauli_type, *syndrome[pauli_type][i])
        # no flags occured, check if syndromes were different
        # if so, measure non-FT and correct with normal steane correction
        # print(syndrome)
        if syndrome[pauli_type][0] != syndrome[pauli_type][1]:
            # print("no flag, syndromes don't match")
            return F1FTECProtocol.correct_non_flagged_erred_circuit(
                    state, stabs, *args, **kwargs)
        # if not, do standard correction on the syndrome
        else:
            # print("no flag, syndromes match")
            return SteaneProtocol.correct_from_syndrome(
                    state, syndrome[pauli_type][0], *args, **kwargs)

    @staticmethod
    def correct_from_flagged_circuit(state, stabs, stab, *args, **kwargs):
        decoder = Syndrome.FlaggedSyndromeDecoder(stab)
        syndrome, faults = SteaneProtocol.measure_stabilizers(
                state, stabs, *args, **kwargs)
        corr_qubits, corr_pauli_type = decoder.lot_decoder(syndrome)
        circ = Steane.BaseSteaneCirc()
        if corr_qubits is not None:
            circ.append(corr_pauli_type, set(corr_qubits))
        return RUNNER.run(state, circ, *args, **kwargs)

    @staticmethod
    def correct_non_flagged_erred_circuit(state, stabs, *args, **kwargs):
        if stabs[0].pauli_type == "X":
            return SteaneProtocol.x_steane_round(state, *args, **kwargs)
        if stabs[0].pauli_type == "Z":
            return SteaneProtocol.z_steane_round(state, *args, **kwargs)
        else:
            raise ValueError("pauli type could not be identified in erred"
                             "f1ftec non-flagged syndrome")

    @staticmethod
    def is_flagged(res):
        flag_qubit = Measurement.F1FTECStabMeasCircuitData.FLAG_QUBIT
        flag = res.measurements.last().syndrome[flag_qubit]
        return bool(flag)
