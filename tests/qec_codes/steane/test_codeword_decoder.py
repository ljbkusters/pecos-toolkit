#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_codeword_decoder.py
@author Luc Kusters
@date 01-07-2022
"""

import copy

from pecos_toolkit.qecc_codes.steane import protocols

zero_state = protocols.SteaneProtocol.init_logical_zero().state
one_state = copy.deepcopy(zero_state)
one_state.run_gate("X", {0, 1, 4})

N = 5

print(f"testing {N} runs of decoding perfect zero states")
for i in range(N):
    print("zero state",
          protocols.SteaneProtocol.decode_state(zero_state, copy_state=True))

print(f"testing {N} runs of decoding perfect one states")
for i in range(N):
    print("one state",
          protocols.SteaneProtocol.decode_state(one_state, copy_state=True))

erred_zero = copy.deepcopy(zero_state)
erred_zero.run_gate("X", {0})
erred_one = copy.deepcopy(one_state)
erred_one.run_gate("X", {0})

print(f"testing {N} runs of decoding zero states with wt 1 error")
for i in range(N):
    print("zero state",
          protocols.SteaneProtocol.decode_state(erred_zero, copy_state=True))

print(f"testing {N} runs of decoding one states with wt 1 error")
for i in range(N):
    print("one state",
          protocols.SteaneProtocol.decode_state(erred_one, copy_state=True))

logical_erred_zero = copy.deepcopy(erred_zero)
logical_erred_zero.run_gate("X", {1})
logical_erred_one = copy.deepcopy(erred_one)
logical_erred_one.run_gate("X", {1})

print(f"testing {N} runs of decoding zero states with wt 2 error")
for i in range(N):
    print("zero state",
          protocols.SteaneProtocol.decode_state(logical_erred_zero,
                                                copy_state=True))

print(f"testing {N} runs of decoding one states with wt 2 error")
for i in range(N):
    print("one state",
          protocols.SteaneProtocol.decode_state(logical_erred_one,
                                                copy_state=True))
