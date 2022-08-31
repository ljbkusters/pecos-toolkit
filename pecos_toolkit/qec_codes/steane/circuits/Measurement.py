#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Measurements.py
@author Luc Kusters
@date 01-06-2022
"""

from pecos_toolkit.qec_codes.steane.circuits import Steane


class StabMeasCircuitData(object):
    ANCILLA_QUBIT = 7


class StabMeasCircuit(Steane.BaseSteaneCirc, StabMeasCircuitData):

    def __init__(self, stabilizer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stabilizer = stabilizer
        if stabilizer.pauli_type == "X":
            self.entangling_gate = "CNOT"
        elif stabilizer.pauli_type == "Z":
            self.entangling_gate = "CZ"
        self.append("init |+>", {self.ANCILLA_QUBIT})
        self.append(self.entangling_gate, {(self.ANCILLA_QUBIT,
                                            self.stabilizer.q1)})
        self.append(self.entangling_gate, {(self.ANCILLA_QUBIT,
                                            self.stabilizer.q2)})
        self.append(self.entangling_gate, {(self.ANCILLA_QUBIT,
                                            self.stabilizer.q3)})
        self.append(self.entangling_gate, {(self.ANCILLA_QUBIT,
                                            self.stabilizer.q4)})
        self.append("measure X", {self.ANCILLA_QUBIT})


class DataStateMeasurement(Steane.BaseSteaneCirc):
    ALLOWED_BASES = ("Z", "X")

    def __init__(self, measure_basis="Z",  *args, **kwargs):
        super().__init__(*args, **kwargs)
        if measure_basis not in self.ALLOWED_BASES:
            raise ValueError("keyword argument measure_basis should be one of"
                             f"{self.ALLOWED_BASES}")
        self.measure_basis = measure_basis
        self.append(f"measure {self.measure_basis}", set(self.DATA_QUBITS))


class F1FlagCircData(object):
    """Data structure for saving variables for a flag circuit

    Also contains an injection method to inject the flag circuit into an
    existing "parent" circuit
    """

    def __init__(self, flag_qubit, flag_from_qubit, gutter_1, gutter_2,
                 init_loc, meas_loc, meas_type="measure Z",
                 init_type="init |0>"):
        self.flag_qubit = flag_qubit
        self.flag_from_qubit = flag_from_qubit
        self.gutter_1 = gutter_1
        self.gutter_2 = gutter_2
        self.meas_loc = meas_loc
        self.init_loc = init_loc
        self.meas_type = meas_type
        self.init_type = init_type

    def inject_flag_circuit(self, parent_circ):
        parent_circ.update(
                self.meas_type, {self.flag_qubit}, tick=self.meas_loc)
        parent_circ.insert(
                self.gutter_2,
                ({"CNOT": {(self.flag_from_qubit, self.flag_qubit)}}, {}))
        parent_circ.insert(
                self.gutter_1,
                ({"CNOT": {(self.flag_from_qubit, self.flag_qubit)}}, {}))
        parent_circ.update(
                self.init_type, {self.flag_qubit}, tick=self.init_loc)


class F1FTECStabMeasCircuitData(StabMeasCircuitData):
    FLAG_QUBIT = 8
    FLAG_INIT_TYPE = "init |0>"
    FLAG_MEAS_TYPE = "measure Z"


class F1FTECStabMeasCircuit(StabMeasCircuit, F1FTECStabMeasCircuitData):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.f1_flag_circ = F1FlagCircData(flag_qubit=self.FLAG_QUBIT,
                                           flag_from_qubit=self.ANCILLA_QUBIT,
                                           gutter_1=2, gutter_2=4,
                                           init_loc=0, meas_loc=5,
                                           meas_type=self.FLAG_MEAS_TYPE,
                                           init_type=self.FLAG_INIT_TYPE)
        self.f1_flag_circ.inject_flag_circuit(self)
