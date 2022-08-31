#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backwards compatible import loader

Loads the qec_codes module instead of the qecc_codes module. This
is to help with backwards compatiblility in projects using the
qecc_codes import directly.

@author Luc Kusters
@date 31-08-2022
"""

import sys
import warnings
from importlib.abc import MetaPathFinder, Loader
import importlib

from pecos_toolkit.qec_codes import *


warnings.warn("This import method is deprecated, please use "
              "pecos_toolkit.qec_codes")


class MyLoader(Loader):
    def module_repr(self, module):
        return repr(module)

    def load_module(self, fullname):
        old_name = fullname
        names = fullname.split(".")
        names[1] = "qec_codes"
        fullname = ".".join(names)
        module = importlib.import_module(fullname)
        sys.modules[old_name] = module
        return module


class MyImport(MetaPathFinder):
    def find_module(self, fullname, path=None):
        names = fullname.split(".")
        if (len(names) >= 2 and names[0] == "pecos_toolkit"
                and names[1] == "qecc_codes"):
            return MyLoader()


sys.meta_path.append(MyImport())
