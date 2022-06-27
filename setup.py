#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup.py
@author Luc Kusters
@date 24-06-2022
"""

import pip
from setuptools import setup
from setuptools import find_packages

# installed = pip.freeze()
# if "quantum-pecos==2.0.dev0" not in installed:
#     print("This install relies on the RWTH Quantum-PECOS 2.0.dev0"
#           " distribution. as it is currently not publicly available, please"
#           " install this package by hand!")

setup(name='pecos_toolkit',
      version='0.0.1',
      description='Toolkit with useful implemented code based on pecos module',
      url='https://git.rwth-aachen.de/masters-thesis/code/pecos-toolkit',
      author='Luc Kusters',
      author_email='luc.kusters@rwth-aachen.de',
      license='GNU GPLv3',
      packages=find_packages(),
      zip_safe=False,
      install_requires=[
            "numpy",
            # "pecos==0.2.dev0",
          ],
      )
