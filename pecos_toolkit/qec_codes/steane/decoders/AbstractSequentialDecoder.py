#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AbstractSequentialDecoder.py
@author Luc Kusters
@date 26-09-2022
"""


class AbstractSequentialDecoder(object):
    """Abstract sequential data decoder interface"""

    NotImplementedMethodError = NotImplementedError(
                    "Deriving classes should implement this method")

    def decode_sequence_to_parity(self, sequence_data):
        raise self.NotImplementedMethodError

    def decode_sequence_to_correction(self, sequence_data):
        raise self.NotImplementedMethodError
