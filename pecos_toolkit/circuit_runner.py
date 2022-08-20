#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runners.py
@author Luc Kusters
@date 02-06-2022
"""

import collections
import copy
import numpy.random

import pecos.circuit_runners


RunnerResult = collections.namedtuple("RunnerResult", ("state", "measurements",
                                                       "faults"))


class MeasurementContainer(dict):
    """Data structure for containing measurements used in the ImprovedRunner

    MeasurementContainer is a basic dict with some extra functionality
    """

    @property
    def ticks(self):
        """get a list of keys"""
        return list(self.keys())

    def to_list(self):
        """returns a list of measurements (without the keys)"""
        return list(self.values())

    def simplified(self):
        """Compatibility alias, the method to_list is prefered"""
        return self.to_list()

    @property
    def first(self):
        """Get the first measurement"""
        return self.to_list()[0]

    @property
    def last(self):
        """Get the last measurement"""
        return self.to_list()[-1]


class Measurement(dict):
    """Measurement object to store measurements made on a single tick"""

    def __init__(self, num_qubits, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_qubits = num_qubits

    @property
    def syndrome(self):
        """Measurement syndrome from the state it was measured on

        Returns:
            list of zeros and ones
        """
        return [self[i] if i in self.keys() else 0
                for i in range(self.num_qubits)]

    def __repr__(self):
        return f"Measurement({super().__repr__()})"


class ImprovedRunner(pecos.circuit_runners.Standard):
    """Wrapper around standard runner, improves measurement output

    If no measurements took place the measurement output is set to None
    (similar for faults)

    Measurement output is always given as a dict of ticks containing
    dicts of locations with measurement output as a 0 or 1 (instead
    of only showing measurment output IF the output is a 1)
    """
    MEASUREMENTS = ("measure X", "measure Y", "measure Z")

    def __init__(self, random_seed=True, *args, **kwargs):
        seed = numpy.random.randint(1e9) if random_seed else None
        super().__init__(seed=seed, *args, **kwargs)

    def run(self, state, circ, copy_state=False, *args, **kwargs):
        if copy_state:
            state = copy.deepcopy(state)
        std_meas, std_faults = super().run(state, circ, *args, **kwargs)
        meas = MeasurementContainer()
        for tick, tick_idx, params in circ.iter_ticks():
            locations = [qudit for gate_symbol, qudit_set, params
                         in tick.items() for qudit in qudit_set
                         if gate_symbol in self.MEASUREMENTS]
            if len(locations) > 0:
                meas[tick_idx] = Measurement(num_qubits=state.num_qubits)
                locations_meas_ones = \
                    std_meas[tick_idx] if len(std_meas) > 0 else []
                for loc in locations:
                    meas[tick_idx][loc] = \
                            1 if loc in locations_meas_ones else 0
        if len(meas) == 0:
            meas = None
        faults = std_faults
        if len(std_faults) == 0:
            faults = None
        return RunnerResult(state, meas, faults)
