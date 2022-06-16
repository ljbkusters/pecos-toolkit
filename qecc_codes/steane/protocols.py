#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
steane.py
@author Luc Kusters
@date 07-06-2022
"""

import collections

# from toolkits.error_generator_toolkit import ErrorGenerator
from toolkits.circuit_runner import ImprovedRunner
from toolkits.qecc_codes.steane.circuits import Logical
from toolkits.qecc_codes.steane.circuits import Measurement
from toolkits.qecc_codes.steane.circuits import Steane
from toolkits.qecc_codes.steane.data_types import Syndrome


RUNNER = ImprovedRunner(random_seed=True)


class SteaneProtocol(object):
    """Namespace for basic steane code"""

    SyndromeMeasResults = collections.namedtuple(
            "SyndromeMeasResults", "syndrome faults")

    @staticmethod
    def init_logical_zero(*args, **kwargs):
        circ = Logical.LogicalZeroInitialization()
        return RUNNER.run(circ.simulator(), circ, *args, **kwargs)

    @staticmethod
    def idle_data_qubits(*args, **kwargs):
        circ = Steane.IdleDataBlock()
        return RUNNER.run(circ.simulator(), circ, *args, **kwargs)

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
            # "I", Steane.BaseSteaneCirc.set_of_qubits)
        state, meas, fault = RUNNER.run(state, circ, *args, **kwargs)
        return state, meas, fault

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
    def verfied_init_logical_zero():
        # TODO a circuit class still has to be made for this
        pass

    @staticmethod
    def flag_measure_stabilizers(state, stabilizers, *args, **kwargs):
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
        flags = []
        faults = []
        for stab in stabilizers:
            circ = Measurement.F1FTECStabMeasCircuit(stab)
            res = RUNNER.run(state, circ, *args, **kwargs)
            print(res.measurements)
            print(type(res.measurements))
            syndromes.append(res.measurements.simplified().syndrome[circ.ANCILLA_QUBIT])
            flags.append(res.measurements.simplified().syndrome[circ.FLAG_QUBIT])
            faults.append(res.faults)
        syndrome = Syndrome.Syndrome(stabilizers[0].pauli_type, *syndromes)
        flag_syndrome = Syndrome.Syndrome("flag", *syndromes)
        return F1FTECProtocol.SyndromeMeasResults(syndrome, flag_syndrome,
                                                  faults)

    @staticmethod
    def flag_measure_x_stabilizers(state, *args, **kwargs):
        return F1FTECProtocol.flag_measure_stabilizers(
                state, Steane.BaseSteaneData.x_stabilizers, *args, **kwargs)

    @staticmethod
    def flag_measure_z_stabilizers(state, *args, **kwargs):
        return F1FTECProtocol.flag_measure_stabilizers(
                state, Steane.BaseSteaneData.z_stabilizers, *args, **kwargs)

    @staticmethod
    def flag_measure_all_stabilizers(state, *args, **kwargs):
        x_meas_res = F1FTECProtocol.flag_measure_x_stabilizers(
                state, *args, **kwargs)
        z_meas_res = F1FTECProtocol.flag_measure_z_stabilizers(
                state, *args, **kwargs)
        return x_meas_res, z_meas_res

    @staticmethod
    def flag_correct_from_syndrome():
        pass

    @staticmethod
    def is_flagged(meas_res):
        return any(val == 1 for val in meas_res.flag_syndrome)

    @staticmethod
    def f1ftec_on_flag_action(state, steane_meas_f, *args, **kwargs):
        res = steane_meas_f(state, *args, **kwargs)
        syndrome = res.syndrome


    @staticmethod
    def f1ftec_round(state, meas_f, *args, **kwargs):
        if meas_f == F1FTECProtocol.flag_measure_x_stabilizers:
            steane_meas_f = SteaneProtocol.measure_x_stabilizers
        elif meas_f == F1FTECProtocol.flag_measure_z_stabilizers:
            steane_meas_f = SteaneProtocol.measure_z_stabilizers
        else:
            raise TypeError("meas_f has to be one of (SteaneProtocol."
                            "measure_x_stabilizers, SteaneProtocol."
                            "measure_z_stabilizers)")
        meas_res_1 = meas_f(state, *args, **kwargs)
        if F1FTECProtocol.is_flagged(meas_res_1):
            return F1FTECProtocol.f1ftec_on_flag_action(
                    state, steane_meas_f, *args, **kwargs)
        meas_res_2 = meas_f(state, *args, **kwargs)
        if F1FTECProtocol.is_flagged(meas_res_2):
            return F1FTECProtocol.f1ftec_on_flag_action(
                    state, steane_meas_f, *args, **kwargs)
        # no flags occured
        if meas_res_1.syndrome == meas_res_2.syndrome:
            # correct E(s)
            SteaneProtocol.correct_from_syndrome(state, meas_res_1.syndrome,
                                                 *args, **kwargs)
        else:
            # measure once more non-FT and correct E(s) (i.e. Steane round)
            SteaneProtocol.x_steane_round(state, *args, **kwargs)

    @staticmethod
    def f1ftec_x_round(state, *args, **kwargs):
        return F1FTECProtocol.f1ftec_round(
                state, meas_f=F1FTECProtocol.flag_measure_x_stabilizers,
                *args, **kwargs)

    @staticmethod
    def f1ftec_z_round(state, *args, **kwargs):
        return F1FTECProtocol.f1ftec_round(
                state, meas_f=F1FTECProtocol.flag_measure_x_stabilizers,
                *args, **kwargs)

    @staticmethod
    def full_f1ftec_round(state, *args, **kwargs):
        x_res = F1FTECProtocol.f1ftec_x_round(state, *args, **kwargs)
        z_res = F1FTECProtocol.f1ftec_z_round(state, *args, **kwargs)
        return x_res, z_res
