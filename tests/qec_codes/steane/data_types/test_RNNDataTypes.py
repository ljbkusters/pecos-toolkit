#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_RNNDataTypes.py
@author Luc Kusters
@date 18-08-2022
"""

import numpy
import unittest

from pecos_toolkit.qecc_codes.steane.data_types import RNNDataTypes


class Test_BaseSyndromeData(unittest.TestCase):

    def setUp(self):
        self.cls = RNNDataTypes.BaseSyndromeData()

    def tearDown(self):
        pass

    def test_BaseSyndromeData(self):
        self.assertIsInstance(self.cls.syndrome, list)
        self.assertIsInstance(self.cls.syndrome_increments, list)
        self.assertIsInstance(self.cls.flags, list)


class Test_RNNSyndromeData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """code hook to run before ALL tests"""
        pass

    @classmethod
    def tearDownClass(cls):
        """code hook to run after ALL tests"""
        pass

    def setUp(self):
        """code hook to run before EACH tests"""
        pass

    def tearDown(self):
        """code hook to run after EACH tests"""
        pass

    def test_RNNSyndromeData_append(self):
        cls = RNNDataTypes.RNNSyndromeData()
        for key in cls.KEYS:
            self.assertIsInstance(cls[key], RNNDataTypes.BaseSyndromeData)
        N = 10
        for i in range(N):
            for basis in cls.KEYS:
                syndrome = numpy.random.randint(0, 1, 3, dtype=int)
                flags = numpy.random.randint(0, 1, 3, dtype=int)
                cls.append(basis=basis, syndrome=syndrome, flags=flags)
        for basis in cls.KEYS:
            self.assertEqual(len(cls[basis].syndrome), N)
            self.assertEqual(len(cls[basis].syndrome_increments), N)
            self.assertEqual(len(cls[basis].flags), N)

        with self.assertRaises(cls.NonAllowedValueError):
            cls.append("Y", [0, 0, 0], [0, 0, 0])

        with self.assertRaises(cls.NotAnIterableError):
            cls.append("X", 0, [0, 0, 0])

        with self.assertRaises(cls.NotAnIterableError):
            cls.append("X", [0, 0, 0], "[0, 0, 0]")

    def test_RNNSyndromeData_extend(self):
        cls1 = RNNDataTypes.RNNSyndromeData()
        cls2 = RNNDataTypes.RNNSyndromeData()
        N = 2
        for i in range(N):
            for basis in cls1.KEYS:
                syndrome = numpy.ones(3, dtype=int)
                flags = numpy.ones(3, dtype=int)
                cls1.append(basis=basis, syndrome=syndrome, flags=flags)
        for i in range(N):
            for basis in cls2.KEYS:
                syndrome = numpy.zeros(3, dtype=int)
                flags = numpy.zeros(3, dtype=int)
                cls2.append(basis=basis, syndrome=syndrome, flags=flags)

        # extend two non empty classes
        cls1.extend(cls2)
        for basis in cls1.KEYS:
            self.assertEqual(len(cls1[basis].syndrome), 2*N)
            self.assertEqual(len(cls1[basis].syndrome_increments), 2*N)
            self.assertEqual(len(cls1[basis].flags), 2*N)
            self.assertEqual(cls1[basis].syndrome,
                             [[1, 1, 1], [1, 1, 1], [0, 0, 0], [0, 0, 0]])
            self.assertEqual(cls1[basis].flags,
                             [[1, 1, 1], [1, 1, 1], [0, 0, 0], [0, 0, 0]])
            self.assertEqual(cls1[basis].syndrome_increments,
                             [[1, 1, 1], [0, 0, 0], [1, 1, 1], [0, 0, 0]])

        # extend an empty class
        cls3 = RNNDataTypes.RNNSyndromeData()
        cls3.extend(cls1)

        # extend by an empty class
        cls4 = RNNDataTypes.RNNSyndromeData()
        cls3.extend(cls4)

        with self.assertRaises(TypeError):
            cls4.extend("")

    def test_RNNSyndromeData_last_flagged(self):
        cls = RNNDataTypes.RNNSyndromeData()
        cls.append("X", [0, 0, 0], [0, 0, 0])
        cls.append("Z", [0, 0, 0], [0, 0, 0])
        cls.append("X", [0, 0, 0], [0, 0, 0])
        cls.append("Z", [0, 1, 0], [0, 1, 0])
        self.assertTrue(cls.last_flagged())

        cls = RNNDataTypes.RNNSyndromeData()
        cls.append("X", [0, 0, 0], [0, 1, 0])
        cls.append("Z", [0, 0, 0], [0, 0, 0])
        cls.append("X", [0, 1, 0], [0, 0, 0])
        cls.append("Z", [0, 0, 0], [0, 0, 0])
        self.assertFalse(cls.last_flagged())

    def test_RNNSyndromeData_last_incremented(self):
        cls = RNNDataTypes.RNNSyndromeData()
        cls.append("X", [0, 0, 0], [0, 0, 0])
        cls.append("Z", [0, 0, 0], [0, 0, 0])
        cls.append("X", [0, 0, 0], [0, 0, 0])
        cls.append("Z", [0, 1, 0], [0, 1, 0])
        self.assertTrue(cls.last_incremented())

        cls = RNNDataTypes.RNNSyndromeData()
        cls.append("X", [0, 1, 0], [0, 0, 0])
        cls.append("Z", [0, 0, 1], [0, 1, 0])
        cls.append("X", [0, 1, 0], [0, 0, 0])
        cls.append("Z", [0, 0, 1], [0, 0, 0])
        self.assertFalse(cls.last_incremented())

    def test_RNNSyndromeData_to_vector(self):
        cls = RNNDataTypes.RNNSyndromeData()
        cls.append("X", [0, 1, 0], [0, 0, 0])
        cls.append("Z", [0, 0, 1], [0, 1, 0])
        cls.append("X", [1, 0, 0], [0, 0, 0])
        cls.append("Z", [0, 0, 1], [1, 0, 0])
        vector = cls.to_vector()
        wanted_vector = numpy.array(
                [[0, 1, 0,
                  0, 0, 0,
                  0, 0, 1,
                  0, 1, 0],
                 [1, 1, 0,
                  0, 0, 0,
                  0, 0, 0,
                  1, 0, 0],
                 ]
                )
        self.assertTrue((wanted_vector == vector).all())


if __name__ == "__main__":
    unittest.main()