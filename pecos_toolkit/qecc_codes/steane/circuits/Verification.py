#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification.py
@author Luc Kusters
@date 23-06-2022
"""

from pecos_toolkit.qecc_codes.steane.circuits import Steane


class VerifyLogicalZeroStateCirc(Steane.BaseSteaneCirc):
    """Steane logical 0 init verification circuit based on [1]

    [1] Demonstration of fault-tolerant universal quantum gate operations
        Lukas Postler, Sascha Heussen, Nature, 2022
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.FLAG_QUBIT = self.FLAG_QUBITS[0]
        self.append("init |0>", {self.FLAG_QUBIT})
        self.append("CNOT", {(self.EDGE_LEFT_QUBIT, self.FLAG_QUBIT)})
        self.append("CNOT", {(self.EDGE_BOTTOM_QUBIT, self.FLAG_QUBIT)})
        self.append("CNOT", {(self.EDGE_RIGHT_QUBIT, self.FLAG_QUBIT)})
        self.append("measure Z", {self.FLAG_QUBIT})
