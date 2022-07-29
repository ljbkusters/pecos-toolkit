#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
f1ftec_syndrome_correction_check.py
@author Luc Kusters
@date 27-07-2022
"""

from pecos_toolkit.error_generator_toolkit import ErrorGenerator
from pecos_toolkit.error_generator_toolkit.ErrorGenerator import \
        GeneralErrorGen, ErrorProneGateCollection, IdleErrorCollection
from pecos_toolkit.qecc_codes.steane.protocols import SteaneProtocol
from pecos_toolkit.qecc_codes.steane.protocols import F1FTECProtocol
from pecos_toolkit.qecc_codes.steane.circuits import Steane
from pecos_toolkit.qecc_codes.steane.circuits import Measurement
from pecos_toolkit.qecc_codes.steane.circuits import Logical
from pecos_toolkit.qecc_codes.steane.data_types import Syndrome


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
                            state, stab, *args, **kwargs)
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


x_stabs = Steane.BaseSteaneData.x_stabilizers
z_stabs = Steane.BaseSteaneData.z_stabilizers


def get_circ(stab):
    circ = Measurement.F1FTECStabMeasCircuit(stab)
    circ.insert(4, ({"X": {7}}, {}))
    return circ

def get_circ_2(stab):
    circ = Measurement.F1FTECStabMeasCircuit(stab)
    circ.insert(1, ({"X": {8}}, {}))
    return circ

print("Error propagates to fault line, qubits 2 and qubit 3 (counting from 0)"
      " of the plaquette")
print("- The best correction should be X_2X_3")

for stab in x_stabs:

    print("placed X error such that weight 2 error will occur")
    error_circuit = get_circ(stab)
    logical_zero = Logical.LogicalZeroInitialization().run().state
    res = error_circuit.run(logical_zero)
    state = res.state
    print("\nsimulating:")
    print("flagged" if res.measurements.last().syndrome[8] == 1 else "not flagged")
    print("decoded state (copy):",
          SteaneProtocol.decode_state(state, copy_state=True))
    print("stabilizer qubits:", stab.qubits)

    x_steane_round = SteaneProtocol.measure_stabilizers(state, z_stabs)
    normal_decoder = Syndrome.SteaneSyndromeDecoder()
    print("normal LOT", normal_decoder.LOT)
    f1ftec_decoder = Syndrome.FlaggedSyndromeDecoder(stab)
    print("f1ftec LOT", f1ftec_decoder.LOT)

    syndrome = x_steane_round.syndrome
    print("normal decoder:", normal_decoder.lot_decoder(syndrome))
    print("f1ftec decoder:", f1ftec_decoder.lot_decoder(syndrome))
    print("ideal:", stab.qubits[2:4])


for stab in x_stabs:

    print("placed X error such that NO weight 2 error will occur but the"
          "circuit flags")
    error_circuit = get_circ_2(stab)
    logical_zero = Logical.LogicalZeroInitialization().run().state
    res = error_circuit.run(logical_zero)
    state = res.state
    print("\nsimulating:")
    print("flagged" if res.measurements.last().syndrome[8] == 1 else "not flagged")
    print("decoded state (copy):",
          SteaneProtocol.decode_state(state, copy_state=True))
    print("stabilizer qubits:", stab.qubits)

    x_steane_round = SteaneProtocol.measure_stabilizers(state, z_stabs)
    normal_decoder = Syndrome.SteaneSyndromeDecoder()
    print("normal LOT", normal_decoder.LOT)
    f1ftec_decoder = Syndrome.FlaggedSyndromeDecoder(stab)
    print("f1ftec LOT", f1ftec_decoder.LOT)

    syndrome = x_steane_round.syndrome
    print("normal decoder:", normal_decoder.lot_decoder(syndrome))
    print("f1ftec decoder:", f1ftec_decoder.lot_decoder(syndrome))
    print("ideal:", None)
