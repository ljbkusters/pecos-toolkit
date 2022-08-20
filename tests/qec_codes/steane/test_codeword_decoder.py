#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_codeword_decoder.py
@author Luc Kusters
@date 01-07-2022
"""

import copy
import unittest

from pecos_toolkit.qecc_codes.steane import protocols
import testsuite


class TestCodeWordDecoder(testsuite.LoggedTestCase):

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.logger.debug("Initializing a steane logical zero and one state")
        self.zero_state = protocols.SteaneProtocol.init_logical_zero().state
        self.one_state = copy.deepcopy(self.zero_state)
        self.one_state.run_gate("X", {0, 1, 4})
        self.num_reps = 5

    def tearDown(self):
        pass

    def check_parity(self, state, expected):
        parity = protocols.SteaneProtocol.decode_state(
                  state, copy_state=True)
        self.logger.debug(f"Logical parity: {parity}")
        self.assertEqual(parity, expected)

    def check_error(self, state, error, expected_parity):
        state = copy.deepcopy(state)
        state.run_gate("X", set(error))
        self.check_parity(state, expected_parity)

    def test_perfect_codewords(self):
        self.logger.debug(f"testing {self.num_reps} runs of decoding perfect"
                          " zero states")
        self.logger.debug(f"testing {self.num_reps} runs of decoding perfect"
                          " one states")
        for i in range(self.num_reps):
            self.check_parity(self.zero_state, 0)
            self.check_parity(self.one_state, 1)

    def test_wt1_erred_codewords(self):
        self.logger.debug("Testing weight one erred states")
        for i in range(self.num_reps):
            self.check_error(self.zero_state, {0}, 0)
            self.check_error(self.one_state, {0}, 1)

    def test_wt2_erred_codewords(self):
        self.logger.debug("Testing weight 2 erred states")
        for i in range(self.num_reps):
            self.check_error(self.zero_state, {0, 1}, 1)
            self.check_error(self.one_state, {0, 1}, 0)

    def test_wt3_logical_erred_codewords(self):
        self.logger.debug("Testing weight 2 erred states")
        for i in range(self.num_reps):
            self.check_error(self.zero_state, {0, 1, 4}, 1)
            self.check_error(self.one_state, {0, 1, 4}, 0)

    def test_wt3_correctible_erred_codewords(self):
        self.logger.debug("Testing weight 2 erred states")
        for i in range(self.num_reps):
            self.check_error(self.zero_state, {0, 1, 2}, 0)
            self.check_error(self.one_state, {0, 1, 2}, 1)

    def test_wt4_correctible_erred_codewords(self):
        self.logger.debug("Testing weight 2 erred states")
        for i in range(self.num_reps):
            self.check_error(self.zero_state, {0, 1, 2, 3}, 0)
            self.check_error(self.one_state, {0, 1, 2, 3}, 1)


if __name__ == "__main__":
    unittest.main()
