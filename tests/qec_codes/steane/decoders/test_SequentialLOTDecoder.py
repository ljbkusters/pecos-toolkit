#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_SequentialLOTDecoder.py
@author Luc Kusters
@date 30-08-2022
"""

import numpy
import unittest

from pecos_toolkit.qecc_codes.steane.data_types import RNNDataTypes
from pecos_toolkit.qecc_codes.steane.decoders import SequentialLOTDecoder


class TestSequentialLOTDecoder(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.decoder = SequentialLOTDecoder.SequentialLOTDecoder()
        self.sample_correction_vector = numpy.asarray([0, 0, 1, 0, 0, 1, 1])
        self.sample_qubits = numpy.asarray((2, 5, 6))
        self.sample_sequence = RNNDataTypes.RNNSyndromeData()

        self.sample_sequence.append("X", [0, 0, 0], [0, 0, 0])
        self.sample_sequence.append("Z", [0, 0, 0], [0, 0, 0])
        self.sample_sequence_corrections = [(
            numpy.array((0, 0, 0, 0, 0, 0, 0)),
            numpy.array((0, 0, 0, 0, 0, 0, 0)))]

        # qubits counted from 0
        #     0
        #   1 T 3    T = 0, L = 1, R = 2
        #  /L 2 R\
        # 4 - 5 - 6
        self.sample_sequence.append("X", [1, 1, 0], [0, 0, 0])  # qubit 1 errs
        self.sample_sequence.append("Z", [0, 0, 1], [0, 0, 0])  # qubit 6 errs
        self.sample_sequence_corrections.append((
            numpy.asarray((0, 1, 0, 0, 0, 0, 0)),
            numpy.asarray((0, 0, 0, 0, 0, 0, 1))
            ))

        self.sample_sequence.append("X", [1, 1, 0], [0, 0, 0])  # no errors
        self.sample_sequence.append("Z", [0, 0, 1], [0, 0, 0])  # no errors
        self.sample_sequence_corrections.append((
            numpy.asarray((0, 0, 0, 0, 0, 0, 0)),
            numpy.asarray((0, 0, 0, 0, 0, 0, 0))
            ))

        self.sample_sequence.append("X", [1, 0, 0], [0, 0, 0])  # err on qb 4
        self.sample_sequence.append("Z", [0, 0, 1], [1, 0, 0])  # 0 circ flags
        self.sample_sequence_corrections.append((
            numpy.asarray((0, 0, 0, 0, 1, 0, 0)),
            numpy.asarray((0, 0, 0, 0, 0, 0, 0))
            ))

        # Z 0 circ causes weight 2 error on qubits 2, 3, activates 2nd X plaq
        # the modified correction for this is a correction on 2, 3
        self.sample_sequence.append("X", [1, 1, 0], [0, 0, 0])
        self.sample_sequence.append("Z", [0, 0, 1], [0, 0, 0])
        self.sample_sequence_corrections.append((
            numpy.asarray((0, 0, 1, 1, 0, 0, 0)),
            numpy.asarray((0, 0, 0, 0, 0, 0, 0))
            ))

    def tearDown(self):
        pass

    def test_correction_vector_to_qubits(self):
        qubits = self.decoder.correction_vector_to_qubits(
                self.sample_correction_vector)
        self.assertTrue(numpy.alltrue(
            qubits == self.sample_qubits))

    def test_qubits_to_correction_vector(self):
        correction_vector = self.decoder.qubits_to_correction_vector(
               self.sample_qubits)
        self.assertTrue(numpy.alltrue(
            correction_vector == self.sample_correction_vector))

    def test_compile_errors(self):
        corrections = [numpy.array((True, False, False), dtype=bool),
                       numpy.array((True, False, True), dtype=bool)]
        compiled = self.decoder.compile_corrections(corrections)
        self.assertTrue(numpy.alltrue(compiled == numpy.array([0, 0, 1])))

    def test_correction_for_syndrome_data(self):
        synincs = ([0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
                   [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1])
        flags_0 = ([0, 0, 0],)
        flags_1 = ([1, 0, 0], [0, 1, 0], [0, 0, 1])
        flags_2 = ([1, 1, 0], [0, 1, 1], [1, 0, 1])
        flags_3 = ([1, 1, 1],)
        for syninc in synincs:
            for flag in flags_0:
                self.decoder.correction_for_syndrome_data(syninc, flag)
            for flag in flags_1:
                self.decoder.correction_for_syndrome_data(syninc, flag)
            for flag in flags_2:
                self.decoder.correction_for_syndrome_data(syninc, flag)
            for flag in flags_3:
                self.decoder.correction_for_syndrome_data(syninc, flag)
            self.decoder.correction_for_syndrome_data(syninc, None)

    def test_unpack_sequence_step(self):
        print(self.decoder.unpack_sequence_step(self.sample_sequence, 0))

    def test_correction_per_time_step(self):
        for i in range(5):
            x, z = self.decoder.correction_per_time_step(
                    self.sample_sequence, i)
            self.assertTrue(numpy.alltrue(
                x == self.sample_sequence_corrections[i][0]))
            self.assertTrue(numpy.alltrue(
                z == self.sample_sequence_corrections[i][1]))

    def test_decode_sequence(self):
        corrections = self.decoder.decode_sequence(self.sample_sequence)
        print(corrections)
        lw = self.decoder.corrections_dict_logical_weight(corrections)
        print(lw)



if __name__ == "__main__":
    unittest.main()
