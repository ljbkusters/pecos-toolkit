#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Syndrome.py
@author Luc Kusters
@date 07-06-2022
"""

import collections

Syndrome = collections.namedtuple("Syndrome", "syndrome_type top left right")


class SteaneSyndromeDecoder(object):

    LOT = {"000": None,
           "001": 6,
           "010": 4,
           "011": 5,
           "100": 0,
           "101": 3,
           "110": 1,
           "111": 2,
           }

    @staticmethod
    def bits_to_lot_key(top, left, right):
        return "{:}{:}{:}".format(top, left, right)

    def syndrome_to_lot_key(self, syndrome: Syndrome):
        return self.bits_to_lot_key(syndrome.top,
                                    syndrome.left,
                                    syndrome.right)

    @staticmethod
    def pauli_correction_type(syndrome: Syndrome):
        if syndrome.syndrome_type == "X":
            return "Z"
        elif syndrome.syndrome_type == "Z":
            return "X"
        elif syndrome.syndrome_type == "flag":
            raise ValueError("'flag' syndromes have to be decoded using the"
                             " FlagSyndromeDecoder.")
        else:
            raise ValueError("Unknown syndrome.syndrome_type: no corrections"
                             " specified. syndrome_type must be one of"
                             " ('X', 'Z') but syndrome.syndrome_type was"
                             f" {syndrome.syndrome_type}")

    def lot_decoder(self, syndrome: Syndrome):
        lot_key = self.syndrome_to_lot_key(syndrome)
        corr_type = self.pauli_correction_type(syndrome)
        return self.LOT[lot_key], corr_type

    def classical_lot_decoder(self, top, left, right):
        lot_key = self.bits_to_lot_key(top, left, right)
        return self.LOT[lot_key]


class FlaggedSyndromeDecoder(SteaneSyndromeDecoder):

    LOT = {"000": None,
           "001": (6, ),
           "010": (4, ),
           "011": (5, ),
           "100": (0, ),
           "101": (3, ),
           "110": (1, ),
           "111": (2, ),
           }

    KEY_FROM_CORRECTION = {
            (2, 3): "010",
            (3, 2): "010",
            (1, 2): "001",
            (2, 1): "001",
            (2, 5): "100",
            (5, 2): "100",
            }

    def __init__(self, stab, *args, **kwargs):
        super().__init__(*args, **kwargs)
        correction = stab.qubits[1:3]
        key = self.KEY_FROM_CORRECTION[correction]
        self.LOT[key] = correction
