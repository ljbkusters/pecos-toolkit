#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fault_tolerance_check.py
@author Luc Kusters
@date 21-07-2022

A few fault tolerance checks using the error placer. Single error
circuits are initialized and then checked against for logical errors.
"""

import termcolor
import copy

from pecos_toolkit.qecc_codes.steane.circuits import Steane
from pecos_toolkit.qecc_codes.steane.circuits import Measurement
from pecos_toolkit.qecc_codes.steane.circuits import Logical
from pecos_toolkit.qecc_codes.steane.circuits import Verification
from pecos_toolkit.qecc_codes.steane.protocols import SteaneProtocol
from pecos_toolkit.qecc_codes.steane.protocols import F1FTECProtocol
# from pecos_toolkit.qecc_codes.steane.protocols import F1FTECProtocol
from pecos_toolkit.error_generator_toolkit import ErrorGenerator
from pecos_toolkit.error_placer_toolkit import ErrorPlacer


epgc_list = [
        ErrorGenerator.FlipZInit,
        ErrorGenerator.FlipXInit,
        ErrorGenerator.FlipZMeasurement,
        ErrorGenerator.FlipXMeasurement,
        ErrorGenerator.ErrorProneGateCollection(
            symbol="single_qubit_gates",
            ep_gates=ErrorGenerator._ONE_QUBIT_GATES,
            param="two_qubit",
            error_gates=ErrorGenerator._PAULI_ERRORS,
            before=False,
            after=True,
            ),
        ErrorGenerator.ErrorProneGateCollection(
            symbol="two_qubit_gate_errors",
            ep_gates=ErrorGenerator._TWO_QUBIT_GATES,
            param="two_qubit",
            error_gates=ErrorGenerator._PAULI_ERROR_TWO,
            before=False,
            after=True,
            ),
        #ErrorGenerator.IdleErrorCollection(
        #    symbol="idle_errors",
        #    param="idle",
        #    error_gates=ErrorGenerator._PAULI_ERRORS,
        #    before=False,
        #    after=True,
        #    ),
        ]


def check_init_circ():
    logical_errors = 0
    circ = Logical.LogicalZeroInitialization()
    init_ft_checker = ErrorPlacer(circ, epgc_list)
    error_circs = init_ft_checker.generate_error_circuits(order=1)
    for error_circ, error_params in error_circs:
        state = error_circ.run().state
        output_codeword = SteaneProtocol.decode_state(state)
        if output_codeword == 1:
            print("Logical error for error params:")
            print(error_params)
            logical_errors += 1
    print(f"Final result: {logical_errors} logical errors")
    if logical_errors > 0:
        print("The circuit is NOT fault tolerant against the supplied error"
              " model")
    else:
        print("The circuit is fault tolerant against the supplied error model")


def check_verified_init_circ():
    logical_errors = 0

    def modified_verified_init_logical_zero(
            init_circ=Logical.LogicalZeroInitialization(),
            verification_circ=Verification.VerifyLogicalZeroStateCirc(),
            *args, **kwargs):
        flag_bit = verification_circ.FLAG_QUBIT
        while True:
            state = init_circ.run(*args, **kwargs).state
            res = verification_circ.run(state, *args, **kwargs)
            flagged = bool(res.measurements.last().syndrome[flag_bit])
            if flagged:
                return None
            else:
                break
        return res

    init_circ = Logical.LogicalZeroInitialization()
    verif_circ = Verification.VerifyLogicalZeroStateCirc()

    init_ft_checker = ErrorPlacer(init_circ, epgc_list)
    init_error_circs = init_ft_checker.generate_error_circuits()
    print("all errors on the init circ")
    # erred init circs
    for error_circ, error_params in init_error_circs:
        res = modified_verified_init_logical_zero(
                init_circ=error_circ, verification_circ=verif_circ)
        if res is None:  # fault correctly caught by flag!
            print("Error caught by flag:")
            print(error_params)
            continue
        output_codeword = SteaneProtocol.decode_state(res.state)
        if output_codeword == 1:
            print("Logical error for error params:")
            print(error_params)
            logical_errors += 1
    print()
    print("all errors on the verification circ")
    # erred verif circs
    verif_ft_checker = ErrorPlacer(verif_circ, epgc_list)
    verif_error_circs = verif_ft_checker.generate_error_circuits()
    for error_circ, error_params in verif_error_circs:
        res = modified_verified_init_logical_zero(
                init_circ=init_circ, verification_circ=error_circ)
        if res is None:  # fault correctly caught by flag!
            print("Error caught by flag (if a logical error could have occured"
                  " it was prevented):")
            print(error_params)
            continue
        output_codeword = SteaneProtocol.decode_state(res.state)
        if output_codeword == 1:
            print("Logical error for error params:")
            print(error_params)
            logical_errors += 1
    print(f"Final result: {logical_errors} logical errors")
    if logical_errors > 0:
        print("The circuit is NOT fault tolerant against the supplied error"
              " model")
    else:
        print("The circuit is fault tolerant against the supplied error model")


def check_syndrome_decoding():
    """standard syndrome decoding"""
    init_circ = Logical.LogicalZeroInitialization()
    logical_hadamard = Logical.TransverseSingleQubitGate(gate="H")
    noop_circ = Steane.BaseSteaneCirc()
    x_stab = Steane.BaseSteaneData.x_stabilizers[0]
    z_stab = Steane.BaseSteaneData.z_stabilizers[0]
    logical_zero_state = init_circ.run().state
    logical_hadamard_state = logical_hadamard.run(logical_zero_state).state
    for stab, state, end_circ in \
            zip((x_stab, z_stab),
                (logical_zero_state, logical_hadamard_state),
                (noop_circ, logical_hadamard)):
        print(f"testing readout circ for stabilizer {stab}")
        logical_errors = 0
        stab_meas_circ = Measurement.StabMeasCircuit(stab)
        ft_checker = ErrorPlacer(stab_meas_circ, epgc_list)
        erred_circs = ft_checker.generate_error_circuits()
        print(len(erred_circs))
        for circ, error_params in erred_circs:
            out_state = circ.run(state, copy_state=True).state
            modified_out_state = end_circ.run(out_state).state
            output_codeword = SteaneProtocol.decode_state(modified_out_state)
            if output_codeword == 1:
                print("Logical error for error params:")
                print(error_params)
                logical_errors += 1
        print(f"Final result: {logical_errors} logical errors")
        if logical_errors > 0:
            print("The circuit is NOT fault tolerant against the supplied"
                  " error model")
        else:
            print("The circuit is fault tolerant against the supplied error"
                  " model")


def check_flag_syndrome_decoding():
    init_circ = Logical.LogicalZeroInitialization()
    zero_state = init_circ.run().state
    logical_hadamard = Logical.TransverseSingleQubitGate(gate="H")
    hadamard_state = logical_hadamard.run(zero_state, copy_state=True).state
    x_stabs = Steane.BaseSteaneData.x_stabilizers
    z_stabs = Steane.BaseSteaneData.z_stabilizers
    # check each stabilizer
    for stab in (*x_stabs, *z_stabs):
        print(f"Checking stabilizer circuit: {stab}")
        logical_error_counter = 0
        stab_meas_circ = Measurement.F1FTECStabMeasCircuit(stab)
        error_placer = ErrorPlacer(stab_meas_circ, epgc_list)
        erred_circs = error_placer.generate_error_circuits()
        # check each error circuit for the stabilizer
        for circ, err_params in erred_circs:
            # check in both |0_L> and |+_L> basis for bit and phase flips
            for in_state, meas_basis in zip(
                    (copy.deepcopy(zero_state),
                     copy.deepcopy(hadamard_state),
                     ), ("Z", "X")
                    ):
                res = circ.run(in_state)
                out_state = res.state
                flag_bit = res.measurements.last().syndrome[circ.FLAG_QUBIT]
                if flag_bit == 1:
                    out_state = F1FTECProtocol.correct_from_flagged_circuit(
                            state=out_state,
                            stab=stab,
                            ).state
                    outcome = SteaneProtocol.decode_state(
                            out_state, measure_basis=meas_basis)
                    if outcome == 1:
                        print(termcolor.colored(
                            f"error occured for: {err_params}",
                            "red"))
                        print("ERROR: Modified correction did not prevent a"
                              " logical error")
                        logical_error_counter += 1
                    print()
                else:
                    outcome = SteaneProtocol.decode_state(
                                out_state, measure_basis=meas_basis)
                    if outcome == 1:
                        print(termcolor.colored(
                              f"A logical error occured for {err_params}",
                              "red"))
                        print("the circuit did NOT flag")
                        logical_error_counter += 1
        if logical_error_counter > 0:
            print("Circuit is NOT fault tolerant against the provided "
                  "error model")
        else:
            print("Circuit is fault tolerant against the provided error model")
        print(80*"=")
        input("wating for next stabilizer... press [ENTER]")



if __name__ == "__main__":
    #check_init_circ()
    #check_verified_init_circ()
    #check_syndrome_decoding()
    check_flag_syndrome_decoding()
