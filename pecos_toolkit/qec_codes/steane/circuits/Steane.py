#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steane.py
@author Luc Kusters
@date 06-06-2022
"""

import numpy
import itertools

import pecos.circuits
import pecos.simulators

from pecos_toolkit.qec_codes.steane.data_types import Plaquette
from pecos_toolkit import circuit_runner


def distance(array_1, array_2):
    if len(array_1) != len(array_2):
        raise RuntimeError("Input arrays must be of equal length for"
                           " distance calculation but were of lengths"
                           f"{len(array_1)}, {len(array_2)}")
    return sum([i != j for i, j in zip(array_1, array_2)])


class BinaryArray(list):

    def distance_to(self, other):
        return distance(self, other)

    @classmethod
    def from_qubit_set(cls, qubit_set, length):
        return cls([1 if q in qubit_set else 0 for q in range(length)])

    def to_qubit_set(self):
        qubit_set = set()
        for q in self:
            if q == 1:
                qubit_set.add(q)
        return qubit_set


class BinaryStabilizerGenerator(object):
    BINARY_STAB_GEN = tuple()
    VALID_LOGICALS = tuple()
    LOGICAL_ZERO_CODEWORDS_MAGIC_STRINGS = ("zero", 0, "logical_zero")
    LOGICAL_ONE_CODEWORDS_MAGIC_STRINGS = ("one", 1, "logical_one")

    @property
    def stabilizers(self):
        stab_set = set()
        # add identity
        stab_set.add(tuple(self.element_wise_xor(
            self.BINARY_STAB_GEN[0], self.BINARY_STAB_GEN[0])))

        N_generators = len(self.BINARY_STAB_GEN)
        generator_idx = range(N_generators)
        for i in generator_idx:
            combinations = itertools.combinations(generator_idx, i + 1)
            for combination in combinations:
                stabilizers = numpy.array(list(self.BINARY_STAB_GEN))
                stab_combination = stabilizers[list(combination)]
                stab_set.add(tuple(self.n_xor(*stab_combination)))
        return tuple(stab_set)

    @property
    def logical_zero_codewords(self):
        return self.stabilizers

    @property
    def logical_one_codewords(self):
        codewords = list(self.logical_zero_codewords)
        logical = BinaryArray.from_qubit_set(self.VALID_LOGICALS[0],
                                             length=len(codewords[0]))
        for i, codeword in enumerate(codewords):
            codewords[i] = tuple(self.element_wise_xor(codeword, logical))
        return tuple(codewords)

    def min_distance_to_logical_codewords(self, syndrome, logical_codewords):
        if logical_codewords in self.LOGICAL_ZERO_CODEWORDS_MAGIC_STRINGS:
            logical_codewords = self.logical_zero_codewords
        elif logical_codewords in self.LOGICAL_ONE_CODEWORDS_MAGIC_STRINGS:
            logical_codewords = self.logical_one_codewords
        return min([distance(syndrome, codeword)
                    for codeword in logical_codewords])

    @staticmethod
    def element_wise_xor(array_1, array_2):
        return [x ^ y for x, y in zip(array_1, array_2)]

    def n_xor(self, *arrays):
        out = [0 for _ in range(len(arrays[0]))]
        for array in arrays:
            out = self.element_wise_xor(out, array)
        return out


class SteaneBinaryStabilzerGenerator(BinaryStabilizerGenerator):
    BINARY_STAB_GEN = (
                [1, 1, 1, 1, 0, 0, 0],
                [0, 1, 1, 0, 1, 1, 0],
                [0, 0, 1, 1, 0, 1, 1],
            )
    VALID_LOGICALS = (
            {0, 1, 4}, {0, 2, 5}, {0, 3, 6},
            {4, 2, 3}, {4, 5, 6},
            {6, 2, 1},
            )


class BaseSteaneData(SteaneBinaryStabilzerGenerator):
    DATA_QUBITS = range(0, 7)  # TODO qubit register type?
    MEAS_QUBITS = range(7, 8)
    FLAG_QUBITS = range(8, 9)

    CORNER_TOP_QUBIT = 0    # repr . 0 .
    CORNER_LEFT_QUBIT = 4   # #   1 . . 3
    CORNER_RIGHT_QUBIT = 6  # #  /   2    \
    EDGE_LEFT_QUBIT = 1     # # 4  _ 5  _  6
    EDGE_BOTTOM_QUBIT = 5
    EDGE_RIGHT_QUBIT = 3
    CENTER_QUBIT = 2

    top_plaquette = Plaquette.Plaquette(
                CORNER_TOP_QUBIT, EDGE_LEFT_QUBIT,
                CENTER_QUBIT, EDGE_RIGHT_QUBIT)
    bottom_left_plaquette = Plaquette.Plaquette(
            CORNER_LEFT_QUBIT, EDGE_BOTTOM_QUBIT,
            CENTER_QUBIT, EDGE_LEFT_QUBIT
            )
    bottom_right_plaquette = Plaquette.Plaquette(
            CORNER_RIGHT_QUBIT, EDGE_RIGHT_QUBIT,
            CENTER_QUBIT, EDGE_BOTTOM_QUBIT
            )
    plaquettes = (top_plaquette, bottom_left_plaquette, bottom_right_plaquette)
    x_stabilizers = tuple(Plaquette.Stabilizer.from_plaquette(plaq, "X")
                          for plaq in plaquettes)
    z_stabilizers = tuple(Plaquette.Stabilizer.from_plaquette(plaq, "Z")
                          for plaq in plaquettes)


class BaseSteaneCirc(pecos.circuits.QuantumCircuit, BaseSteaneData):
    """Steane circuit baseclass defining some commonly used constants

    This baseclass may be inherited (instead of pecos base QuantumCircuits)
    to access the constants necessary for working with the steane code
    """

    def __init__(self, runner=circuit_runner.ImprovedRunner(random_seed=True),
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._runner = runner

    @property
    def set_of_qubits(self):
        """Set of qubits (numbered from 0 to n) in the circuit"""
        return set.union(set(self.DATA_QUBITS),
                         set(self.MEAS_QUBITS),
                         set(self.FLAG_QUBITS))

    @property
    def num_qubits(self):
        """Number of qubits in the circuit"""
        return len(self.set_of_qubits)

    def simulator(self):
        """Simulator corresponding for this circuit and deriving circuits"""
        return pecos.simulators.SparseSim(self.num_qubits)

    def run(self, state=None, *args, **kwargs):
        if state is None:
            state = self.simulator()
        return self._runner.run(state, self, *args, **kwargs)


class InitPhysicalZero(BaseSteaneCirc):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append("init |0>", set(self.DATA_QUBITS))


class SingleQubitPauli(BaseSteaneCirc):
    def __init__(self, pauli_type, qubit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if qubit is not None:
            self.append(pauli_type, {qubit})


class IdleDataBlock(BaseSteaneCirc):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append("I", set(self.DATA_QUBITS))
