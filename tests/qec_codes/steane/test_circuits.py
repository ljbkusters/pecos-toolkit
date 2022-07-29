#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
circuit_test.py
@author Luc Kusters
@date 20-06-2022
"""

import pecos.circuits
from toolkits.qecc_codes.steane.data_types import Plaquette
from toolkits.qecc_codes.steane.circuits import Measurement

circ = pecos.circuits.QuantumCircuit()
circ.append("X", {0})
circ.append("Y", {0, 2})
circ.append("measure X", {0, 1})
circ.insert(1, ({"measure X": {2, 3}}, {}))

for obj in circ.items():
    print(obj)
print()
for obj in circ.iter_ticks():
    print(obj)
    for bj in obj[0].items():
        print(bj)

stab = Plaquette.XStabilizer(0, 1, 2, 3)
circ = Measurement.F1FTECStabMeasCircuit(stab)
