#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_circuit_runner.py
@author Luc Kusters
@date 19-08-2022
"""

import unittest

import pecos

import testsuite
from pecos_toolkit import circuit_runner


class TestMeasurementContainer(testsuite.LoggedTestCase):

    def setUp(self):
        self.container = circuit_runner.MeasurementContainer()

        # measurement 1
        self.tick_1 = 1
        self.measurement_1 = circuit_runner.Measurement(3)
        self.measurement_1[1] = 0
        self.measurement_1[2] = 1
        self.container[self.tick_1] = self.measurement_1

        # measurement 2
        self.tick_2 = 5
        self.measurement_2 = circuit_runner.Measurement(5)
        self.measurement_2[1] = 0
        self.measurement_2[4] = 1
        self.container[self.tick_2] = self.measurement_2

        # measurement 2
        self.tick_3 = 6
        self.measurement_3 = circuit_runner.Measurement(5)
        self.measurement_3[1] = 0
        self.measurement_3[2] = 0
        self.measurement_3[4] = 1
        self.container[self.tick_3] = self.measurement_3

    def tearDown(self):
        pass

    def test_ticks(self):
        self.assertEqual(self.container.ticks,
                         [self.tick_1, self.tick_2, self.tick_3])
        self.assertEqual(self.container.to_list(), self.container.simplified())
        self.assertEqual(self.container.first, self.measurement_1)
        self.assertEqual(self.container.last, self.measurement_3)
        self.assertEqual(self.container.to_list()[1], self.measurement_2)


class TestMeasurement(testsuite.LoggedTestCase):

    def setUp(self):
        self.measurement = circuit_runner.Measurement(3)
        self.measurement[1] = 0
        self.measurement[2] = 1

    def tearDown(self):
        pass

    def test_syndrome(self):
        self.assertEqual(self.measurement.syndrome, [None, 0, 1])

    def test_repr(self):
        self.assertEqual(self.measurement.__repr__(),
                         "Measurement({1: 0, 2: 1})")

    def test_num_qubits(self):
        self.assertEqual(self.measurement.num_qubits, 3)


class TestImprovedRunner(testsuite.LoggedTestCase):

    def setUp(self):
        self.runner = circuit_runner.ImprovedRunner()

        # circuit 1
        self.state1 = pecos.simulators.SparseSim(3)
        self.circ1 = pecos.circuits.QuantumCircuit()
        # tick 0
        self.circ1.append('init |0>', {0})  # left to idle, has effect on meas
        self.circ1.update('init |1>', {1})
        self.circ1.update('init |0>', {2})
        # tick 1
        self.circ1.append('CNOT', {(1, 2)})
        # tick 2
        self.circ1.append('measure Z', {1, 2})
        # tick 3
        self.circ1.append('CNOT', {(1, 2)})
        # tick 4
        self.circ1.append('X', {(1)})
        # tick 5
        self.circ1.append('measure Z', {1, 2})

        # circuit 2
        self.state2 = pecos.simulators.SparseSim(2)
        self.circ2 = pecos.circuits.QuantumCircuit()
        self.circ2.append('init |1>', {0})
        self.circ2.update('init |0>', {1})
        self.circ2.append('CNOT', {(0, 1)})

    def tearDown(self):
        pass

    def test_run_deterministic(self):
        res = self.runner.run(self.state1, self.circ1)
        # assert types
        self.assertIsInstance(res, circuit_runner.RunnerResult)
        self.assertTrue(isinstance(res.state,
                                   pecos.simulators._parent_sim_classes
                                   .BaseSim
                                   ))
        self.assertIsInstance(res.measurements,
                              circuit_runner.MeasurementContainer
                              )
        self.assertEqual(res.faults, None)

        # check if measurement is as expected
        first_meas_expected = circuit_runner.Measurement(num_qubits=2)
        first_meas_expected[1] = 1
        first_meas_expected[2] = 1

        second_meas_expected = circuit_runner.Measurement(num_qubits=3)
        second_meas_expected[1] = 0
        second_meas_expected[2] = 0
        self.assertEqual(res.measurements.ticks, [2, 5])
        self.assertEqual(res.measurements.first, first_meas_expected)
        self.assertEqual(res.measurements.last, second_meas_expected)
        self.assertEqual(res.measurements.to_list()[0], first_meas_expected)
        self.assertEqual(res.measurements.to_list()[1], second_meas_expected)
        self.assertEqual(res.measurements.first.syndrome, [None, 1, 1])
        self.assertEqual(res.measurements.last.syndrome, [None, 0, 0])

        res = self.runner.run(self.state2, self.circ2)
        self.assertEqual(res.measurements, None)
        self.assertEqual(res.faults, None)

    def test_run_with_faults(self):
        gen = pecos.error_gens.DepolarGen()
        ep = {"p": 1}

        res = self.runner.run(self.state1, self.circ1,
                              error_gen=gen, error_params=ep)
        self.assertTrue(res.faults is not None)
        self.assertIsInstance(res.faults,
                              pecos.error_gens.class_errors_circuit
                              .ErrorCircuits)


if __name__ == "__main__":
    unittest.main()
