#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fault_tolerance_checker.py
@author Luc Kusters
@date 28-06-2022
"""

import collections
import copy
import itertools

from pecos_toolkit import circuit_runner
from pecos_toolkit.error_generator_toolkit import ErrorGenerator

RUNNER = circuit_runner.ImprovedRunner()


ErrorCircCollection = collections.namedtuple("ErrorCircCollection",
                                             ("circuit", "error_locations"))
GateCoordinate = collections.namedtuple("GateCoordinate", ("gate_symbol",
                                                           "tick_idx",
                                                           "qudits"))
ErrorCoordinate = collections.namedtuple("ErrorCoordinate",
                                        ("gate_symbol", "tick_idx", "qudits",       
                                         "error_gate", "after"))


def possible_error_coordinates(circuit, epgc_list):
    error_coordinates = []
    gate_coords = GateCoordinateList(circuit)
    errors_per_gate_type = ErrorModelLookupTable(epgc_list)
    for gate_symbol, tick_idx, qudits in gate_coords:
        if gate_symbol in errors_per_gate_type.keys():
            errors = errors_per_gate_type[gate_symbol]
        else:
            continue  # no error for this gate in error model
        for sub_tick_timestep, after_bool in zip(("before", "after"),
                                                 (False, True)):
            for error in errors[sub_tick_timestep]:
                error_coordinates.append(
                        ErrorCoordinate(
                            gate_symbol=gate_symbol,
                            tick_idx=tick_idx,
                            qudits=qudits,
                            error_gate=error,
                            after=after_bool)
                        )
    return error_coordinates


class ErrorPlacer(object):
    """Class that can generate all possible (single) errors given a circuit
    and an error model defined by a list of ErrorProneGateCollections
    """

    def __init__(self, circuit, epgc_list):
        self.circuit = circuit
        self.epgc_list = epgc_list
        self.possible_errors = possible_error_coordinates(circuit, epgc_list)

    def generate_error_circuits(self, order=1):
        error_circs = []
        error_combinations = itertools.combinations(self.possible_errors,
                                                    r=order)
        for combination in error_combinations:
            for error in combination:
                error_circ = copy.deepcopy(self.circuit)
                _, tick_idx, qudits, error_gate, after = error
                if isinstance(error_gate, tuple):
                    for single_gate, qudit in zip(error_gate, qudits):
                        error_circ.insert(tick_idx + int(after),
                                          ({single_gate: {qudit}}, {}))
                elif isinstance(error_gate, str):
                    error_circ.insert(tick_idx + int(after),
                                      ({error_gate: {qudits}}, {}))
            error_circs.append(ErrorCircCollection(
                error_circ, combination))
        return error_circs


class ErrorModelLookupTable(dict):
    """Order all errors in an epgc_list by the gate on which they may occur
    
    An epgc_list is a list of ErrorProneGateCollection objects (including the
    IdleErrorCollection)
    """
    
    def __init__(self, epgc_list):
        self.epgc_list = epgc_list
        self.generate_empty_lookup_table()
        self.generate_epgc_lookup_table()

    def generate_epgc_lookup_table(self):
        """Generate a lookup table for each gate type"""
        for epgc in self.epgc_list:
            if isinstance(epgc, ErrorGenerator.ErrorProneGateCollection):
                for ep_gate in epgc.ep_gates:
                    if epgc.before:
                        self[ep_gate]["before"].update(
                                epgc.error_gates)
                    if epgc.after:
                        self[ep_gate]["after"].update(epgc.error_gates)
            elif isinstance(epgc, ErrorGenerator.IdleErrorCollection):
                if epgc.before:
                    self["idle"]["before"].update(epgc.error_gates)
                if epgc.after:
                    self["idle"]["after"].update(epgc.error_gates)
            else:
                raise TypeError(f"epgc of type '{type(epgc)}' not supported")

    def generate_empty_lookup_table(self):
        keys = set()
        for epgc in self.epgc_list:
            if isinstance(epgc, ErrorGenerator.ErrorProneGateCollection):
                keys.update(epgc.ep_gates)
            elif isinstance(epgc, ErrorGenerator.IdleErrorCollection):
                keys.update({"idle"})
            else:
                raise TypeError(f"epgc of type '{type(epgc)}' not supported")
        for key in keys:
            self[key] = {"before": set(), "after": set()}


class GateCoordinateList(list):
    """Reshapes a pecos quantum circuit into a dictionary of locations and 
    ticks on a per gate sorting

    This allows for relatively easy error placement with permutations.
    
    example: 
    >>> q = QuantumCircuit(("X":{0, 1}), ("X":{0}, "CNOT":{(1, 2)}))
    >>> gl = GateCoordinateList(q, with_idle=True)
    >>> print(gl)
        [GateCoordinate(gate_symbol="X", tick_idx=0, qudits={0}),
         GateCoordinate(gate_symbol="X", tick_idx=0, qudits={1}),
         GateCoordinate(gate_symbol="idle", tick_idx=0, qudits={2}),
         GateCoordinate(gate_symbol="X", tick_idx=1, qudits={0}),
         GateCoordinate(gate_symbol="CNOT", tick_idx=1, qudits={1, 2}),
        ]
    """

    IDLE_SYMBOL = "idle"

    def __init__(self, circuit, *args, with_idle=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.circuit = circuit
        self.with_idle = with_idle
        self.locate_gates()

    def locate_gates(self):
        """Add all coordinates"""
        for tick, tick_idx, params in self.circuit.iter_ticks():
            for gate_symbol, locations, gate_params in tick.items():
                for location in locations:
                    self.append(
                            GateCoordinate(gate_symbol=gate_symbol,
                                           tick_idx=tick_idx,
                                           qudits=location)
                            )
            if self.with_idle:
                idle_qudits = (self.circuit.qudits
                               - self.circuit.active_qudits[tick_idx])
                for qudit in idle_qudits:
                    self.append(
                            GateCoordinate(gate_symbol=self.IDLE_SYMBOL,
                                           tick_idx=tick_idx,
                                           qudits=qudit)
                            )


if __name__ == '__main__':
    from pecos_toolkit.qecc_codes.steane.circuits import Logical

    circ = Logical.LogicalZeroInitialization()
    epgc_list = [
            ErrorGenerator.FlipZInit,
            ErrorGenerator.FlipXInit,
            ErrorGenerator.FlipZMeasurement,
            ErrorGenerator.FlipXMeasurement,
            ErrorGenerator.ErrorProneGateCollection(
                symbol="two_qubit_gate_errors",
                ep_gates=ErrorGenerator._TWO_QUBIT_GATES,
                param="two_qubit",
                error_gates=ErrorGenerator._PAULI_ERROR_TWO,
                before=False,
                after=True,
                ),
            ErrorGenerator.IdleErrorCollection(
                symbol="idle_errors",
                param="idle",
                error_gates=ErrorGenerator._PAULI_ERRORS,
                before=False,
                after=True,
                ),
            ]
    ep = ErrorPlacer(circ, epgc_list)
    single_error_circs = ep.generate_error_circuits(order=1)
    two_error_circs = ep.generate_error_circuits(order=2)
