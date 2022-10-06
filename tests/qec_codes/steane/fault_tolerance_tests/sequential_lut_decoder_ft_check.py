#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sequential_lut_decoder_ft_check.py
@author Luc Kusters
@date 30-09-2022
"""

import copy
import numpy

from pecos_toolkit.error_generator_toolkit import ErrorGenerator
from pecos_toolkit.error_generator_toolkit.error_placer_toolkit import \
        ErrorPlacer
from pecos_toolkit.qec_codes.steane.circuits import Steane
from pecos_toolkit.qec_codes.steane.circuits import Measurement
from pecos_toolkit.qec_codes.steane.circuits import Logical
from pecos_toolkit.qec_codes.steane.decoders import SequentialLOTDecoder
from pecos_toolkit.qec_codes.steane.protocols import SteaneProtocol

epgc_list = [
        ErrorGenerator.ErrorProneGateCollection(
            symbol="two_qubit_gate_errors",
            ep_gates=ErrorGenerator._TWO_QUBIT_GATES,
            param="two_qubit",
            error_gates=ErrorGenerator._PAULI_ERROR_TWO,
            before=False,
            after=True,
            ),
        ]

N = 2
x_stabilizers = Steane.BaseSteaneData().x_stabilizers
z_stabilizers = Steane.BaseSteaneData().z_stabilizers
x_stab_circs = list(Measurement.F1FTECStabMeasCircuit(s)
                    for s in x_stabilizers)
z_stab_circs = list(Measurement.F1FTECStabMeasCircuit(s)
                    for s in z_stabilizers)
circuits_per_step = [*x_stab_circs, *z_stab_circs]
circuits = []
for _ in range(N):
    circuits.extend(circuits_per_step)

single_step_circ = Steane.BaseSteaneCirc()
for circ in circuits_per_step:
    single_step_circ._ticks.extend(circ._ticks)

full_circuit = Steane.BaseSteaneCirc()
for circ in circuits:
    full_circuit._ticks.extend(circ._ticks)

logical_zero = Logical.LogicalZeroInitialization().run().state


def extract_data_from_res(res, N):
    data = numpy.zeros((N, 12), dtype=bool)
    syndromes = []
    flags = []
    for i, (tick, meas) in enumerate(res.measurements.items()):
        syndromes.append(meas[7])
        flags.append(meas[8])
    syndromes = numpy.array(syndromes).reshape((N, 6))
    flags = numpy.array(flags).reshape((N, 6))
    for i, (syndrome, flag) in enumerate(zip(syndromes, flags)):
        data[i][:3] = syndrome[:3]
        data[i][3:6] = flag[:3]
        data[i][6:9] = syndrome[3:]
        data[i][9:12] = flag[3:]
    return data


print("generating error circuits...")
generator = ErrorPlacer(full_circuit, epgc_list)
error_circs = generator.generate_error_circuits(order=1)


def syndrome_increments(data):
    increments = numpy.zeros(data.shape)
    increments[:, 3:6] = data[:, 3:6]  # copy flag info
    increments[:, 9:12] = data[:, 9:12]
    increments[0, :3] = data[0, :3]    # copy first syndrome
    increments[0, 6:9] = data[0, 6:9]
    # calc deltas
    deltas = numpy.abs(numpy.diff(data, axis=0))
    increments[1:, :3] = deltas[:, :3]
    increments[1:, 6:9] = deltas[:, 6:9]
    return increments.astype(int)


decoder = SequentialLOTDecoder.SequentialLOTDecoder()
verbose_decoder = SequentialLOTDecoder.SequentialLOTDecoder(verbose=True)

print("simulating all error circuits...")
for i, circ in enumerate(error_circs):

    zero_state = copy.deepcopy(logical_zero)
    plus_state = Logical.TransverseSingleQubitGate("H").run(
            logical_zero, copy_state=True).state
    for in_state, decoding_basis in zip((zero_state, plus_state), ("Z", "X")):
        res = circ.circuit.run(state=in_state)
        state = res.state
        data = extract_data_from_res(res, N)
        incs = syndrome_increments(data)
        linc = incs[-1, :]
        if (numpy.sum(linc[0:3]) > 0 or numpy.sum(linc[6:9]) > 0
                or (numpy.sum(linc[3:6]) == 1 or numpy.sum(linc[9:12]) == 1)):
            # print("+1")
            l_res = single_step_circ.run(state)
            l_data = extract_data_from_res(l_res, 1)
            total_data = numpy.concatenate((data, l_data), axis=0)
            data = total_data
            incs = syndrome_increments(total_data)
            state = l_res.state

        final_parity = SteaneProtocol.decode_state(
                state, copy_state=True, measure_basis=decoding_basis)

        basis = "Z" if decoding_basis == "X" else "X"
        corr_p = decoder.decode_sequence_to_parity(incs, 0, basis)
        passed = corr_p == final_parity

        if not passed:
            print("\n\n")
            print(circ.error_locations)
            print("round", circ.error_locations[0].tick_idx // 8 // 6 + 1)
            print("stab", circ.error_locations[0].tick_idx // 8 % 6 + 1)
            print("gate", circ.error_locations[0].tick_idx % 8 + 1)
            print(2*"==================================")
            print("raw syndrome data")
            print("[Za Zb Zc FZa FZb FZc Xa Xb Xc FXa FXb FXc]")
            print(data)
            print(incs)
            print(2*"==================================")
            print("suggested correction")
            corr = verbose_decoder.decode_sequence_to_correction(incs)
            print(corr)
