#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_BasicLOTDecoder.py
@author Luc Kusters
@date 31-08-2022
"""

import unittest

from pecos_toolkit.qecc_codes.steane.decoders import BasicLOTDecoder

class TestBasicLOTDecoder(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.decoder = BasicLOTDecoder.SteaneSyndromeDecoder()
        self.classical_state = [0, 1, 1, 1, 1, 0, 0]

    def tearDown(self):
        pass

    def test_classical_BasicLOTDecoder(self):
        p = self.decoder.corrected_classical_logical_parity(
                self.classical_state)
        self.assertEqual(p, 1)


if __name__ == "__main__":
    unittest.main()
