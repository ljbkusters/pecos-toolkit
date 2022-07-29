#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
steane.py
@author Luc Kusters
@date 01-06-2022
"""


class Plaquette(object):
    """Data type for defining a steane code plaquette"""

    def __init__(self, q1: int, q2: int, q3: int, q4: int):
        """Initialize a steane code plaquette

        Steane code plaquettes are stabilizers within the steane code
        and consist of 4 qubit locations.

        Args:
            q1, qubit location 1
            q2, qubit location 2
            q3, qubit location 3
            q4, qubit location 4
        """
        self.q1 = q1
        self.q2 = q2
        self.q3 = q3
        self.q4 = q4

    @property
    def qubits(self):
        return (self.q1, self.q2, self.q3, self.q4)


class Stabilizer(Plaquette):
    """Plaquette defining a specific stabilizer

    The StabilizerPlaquette is defined on a plaquette and has a stabilizer
    type. Stabilizers can either be X stabilizers or Z stabilizers.
    """
    def __init__(self, pauli_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pauli_type = pauli_type

    @classmethod
    def from_plaquette(cls, plaquette, pauli_type):
        if not isinstance(plaquette, Plaquette):
            raise TypeError("This method requires a 'Plaquette' instance for"
                            " initialization.")
        return cls(pauli_type, *plaquette.qubits)

    def __repr__(self):
        return f"{self.pauli_type} Stabilizer on qubits {self.qubits}"


class XStabilizer(Stabilizer):
    def __init__(self, *args, **kwargs):
        super().__init__("X", *args, **kwargs)


class ZStabilizer(Stabilizer):
    def __init__(self, *args, **kwargs):
        super().__init__("Z", *args, **kwargs)
