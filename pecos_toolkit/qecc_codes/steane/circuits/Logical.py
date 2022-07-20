#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialization.py
@author Luc Kusters
@date 06-06-2022
"""


from pecos_toolkit.qecc_codes.steane.circuits import Steane
from pecos_toolkit.qecc_codes.steane.circuits import Measurement


class LogicalZeroInitialization(Steane.BaseSteaneCirc):
    """Logical initalization circuit"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append("init |0>", set(self.DATA_QUBITS))
        self.append("H", {self.CORNER_TOP_QUBIT})
        self.update("H", {self.CORNER_LEFT_QUBIT})
        self.update("H", {self.CORNER_RIGHT_QUBIT})
        self.append("CNOT", {(self.CORNER_TOP_QUBIT, self.EDGE_LEFT_QUBIT)})
        self.append("CNOT", {(self.CORNER_TOP_QUBIT, self.CENTER_QUBIT)})
        self.append("CNOT", {(self.CORNER_TOP_QUBIT, self.EDGE_RIGHT_QUBIT)})
        self.append("CNOT", {(self.CORNER_LEFT_QUBIT, self.EDGE_LEFT_QUBIT)})
        self.append("CNOT", {(self.CORNER_LEFT_QUBIT, self.CENTER_QUBIT)})
        self.append("CNOT", {(self.CORNER_LEFT_QUBIT, self.EDGE_BOTTOM_QUBIT)})
        self.append("CNOT", {(self.CORNER_RIGHT_QUBIT,
                              self.EDGE_BOTTOM_QUBIT)})
        self.append("CNOT", {(self.CORNER_RIGHT_QUBIT, self.CENTER_QUBIT)})
        self.append("CNOT", {(self.CORNER_RIGHT_QUBIT, self.EDGE_RIGHT_QUBIT)})


class CompactLogicalZeroInitialization(Steane.BaseSteaneCirc):
    """Higly parallelized version of the LogicalZeroInitialization circuit

    This version has fewer idle locations
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append("init |0>", set(self.DATA_QUBITS))
        self.append("H", {self.CORNER_TOP_QUBIT})
        self.update("H", {self.CORNER_LEFT_QUBIT})
        self.update("H", {self.CORNER_RIGHT_QUBIT})
        self.append("CNOT", {(self.CORNER_TOP_QUBIT, self.EDGE_LEFT_QUBIT)})
        self.update("CNOT", {(self.CORNER_LEFT_QUBIT, self.CENTER_QUBIT)})
        self.update("CNOT", {(self.CORNER_RIGHT_QUBIT,
                              self.EDGE_BOTTOM_QUBIT)})
        self.append("CNOT", {(self.CORNER_TOP_QUBIT, self.CENTER_QUBIT)})
        self.update("CNOT", {(self.CORNER_LEFT_QUBIT, self.EDGE_LEFT_QUBIT)})
        self.update("CNOT", {(self.CORNER_RIGHT_QUBIT, self.EDGE_RIGHT_QUBIT)})
        self.append("CNOT", {(self.CORNER_TOP_QUBIT, self.EDGE_RIGHT_QUBIT)})
        self.update("CNOT", {(self.CORNER_LEFT_QUBIT, self.EDGE_BOTTOM_QUBIT)})
        self.update("CNOT", {(self.CORNER_RIGHT_QUBIT, self.CENTER_QUBIT)})


class LogicalPauli(Steane.BaseSteaneCirc):
    LOGICALS = {
            "edge_left": (0, 1, 4),
            "edge_right": (0, 3, 6),
            "edge_bottom": (4, 5, 6),
            "center_vertical": (0, 2, 5),
            "center_left": (4, 2, 3),
            "center_right": (6, 2, 1),
            }

    def __init__(self, pauli_type, logical="edge_left", *args, **kwargs):
        super().__init__(*args, **kwargs)
        if logical == "all":
            self.append("pauli_type", set(self.LOGICALS[logical]))
