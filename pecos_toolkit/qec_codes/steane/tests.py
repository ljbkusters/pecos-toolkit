#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.py
@author Luc Kusters
@date 02-06-2022
"""

from circuits import Measurements
from data_types import Plaquette
from circuit_runners import Runners
import pecos.simulators

xstab = Plaquette.XStabilizer(0, 1, 2, 3)
MeasCirc = Measurements.StabMeasCircuit(xstab)
print(MeasCirc)
F1FTECMeasCirc = Measurements.F1FTECStabMeasCircuit(xstab)
print(F1FTECMeasCirc)
#print(F1FTECMeasCirc)
#help(MeasCirc)
##state = pecos.simulators.SparseSim(11)
#runner = Runners.ImprovedRunner()
#state, meas, faults = runner.run(state=state, circ=MeasCirc)
#print(meas, faults)
#print([x.syndrome for x in meas.values()])
