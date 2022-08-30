#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RNNDataTypes.py
@author Luc Kusters
@date 17-08-2022
"""

import numpy
import collections


class BaseSyndromeData(collections.namedtuple(
                       "BaseSyndromeData",
                       ("syndrome", "flags"))):

    @classmethod
    def empty(cls):
        return cls([], [])

    @staticmethod
    def calc_increment(this, last):
        return [abs(b - a) for a, b in zip(this, last)]

    @property
    def syndrome_increments(self):
        increments = []
        if len(self.syndrome) > 0:
            increments.append(self.syndrome[0])
        for idx in range(1, len(self.syndrome)):
            increments.append(self.calc_increment(
                self.syndrome[idx], self.syndrome[idx-1]))
        return increments


class RNNSyndromeData(dict):

    KEYS = ("X", "Z")

    class NonAllowedValueError(ValueError):
        def __init__(self, arg, val, allowed_vals):
            err_str = (f"Supplied value '{val}' for argument '{arg}' must be"
                       f" one of {allowed_vals}")
            super().__init__(err_str)

    class NotAnIterableError(TypeError):
        def __init__(self, arg, val):
            err_str = (f"Supplied value '{val}' for argument"
                       f"'{arg}' must be an iterable")
            super().__init__(err_str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.KEYS:
            self[key] = BaseSyndromeData.empty()

    def __len__(self):
        if len(self["X"].syndrome) == len(self["Z"].syndrome):
            return len(self["X"].syndrome)
        else:
            raise RuntimeError("X and Z syndrome data does not have"
                               "equal length and no valid length could be"
                               "determined")

    def append(self, basis, syndrome, flags):
        if basis not in self.KEYS:
            raise self.NonAllowedValueError("basis", basis, self.KEYS)
        if not isinstance(syndrome, (list, tuple, numpy.ndarray)):
            raise self.NotAnIterableError("syndrome", syndrome)
        if not isinstance(flags, (list, tuple, numpy.ndarray)):
            raise self.NotAnIterableError("flags", flags)
        syndrome = list(syndrome)
        flags = list(flags)
        self[basis].syndrome.append(syndrome)
        self[basis].flags.append(flags)

    def extend(self, other):
        if not isinstance(other, RNNSyndromeData):
            raise TypeError("extension should also be of type"
                            f" {type(self).__name__}")
        for (s_basis, s_val), (o_basis, o_val) in \
                zip(self.items(), other.items()):
            # bridge
            self[s_basis].syndrome.extend(other[o_basis].syndrome)
            self[s_basis].flags.extend(other[o_basis].flags)

    def to_vector(self):
        """Cast the datatype to a vector usable for the RNN

        Returns:
            (n x 12) numpy.ndarray with n the number of time steps and
            12 = 3 x_stabs + 3 x_flags + 3 z_stabs + 3 z_flags
        """
        x_increments = self["X"].syndrome_increments
        x_flags = self["X"].flags
        z_increments = self["Z"].syndrome_increments
        z_flags = self["Z"].flags

        vector = numpy.empty((len(x_increments), 12), dtype=bool)

        vector[:, :3] = x_increments
        vector[:, 3:6] = x_flags
        vector[:, 6:9] = z_increments
        vector[:, 9:12] = z_flags
        return vector

    def x_syndromes(self, time_step):
        return self["X"].syndrome[time_step]

    def x_syndrome_increments(self, time_step):
        return self["X"].syndrome_increments[time_step]

    def x_flags(self, time_step):
        return self["X"].flags[time_step]

    def z_syndromes(self, time_step):
        return self["Z"].syndrome[time_step]

    def z_syndrome_increments(self, time_step):
        return self["Z"].syndrome_increments[time_step]

    def z_flags(self, time_step):
        return self["Z"].flags[time_step]

    def last_flagged(self):
        return any([sum(self[key].flags[-1]) > 0 for key in self.KEYS])

    def last_incremented(self):
        return any([sum(self[key].syndrome_increments[-1]) > 0
                    for key in self.KEYS])

    def pad_to(self, n_steps):
        for key in self.KEYS:
            length = len(self[key])
            diff = n_steps - length
            if diff > 0:
                for idx in range(diff):
                    self.append(key, [0, 0, 0], [0, 0, 0])
            elif diff == 0:
                pass
            else:
                raise RuntimeError("Number of steps greater than wanted pad"
                                   "size, cannot pad to this value!")


RNNData = collections.namedtuple(
    "RNNData",
    ("stabilizer_data", "final_syndrome_increment", "final_parity",
     "basis", "original_parity"))
