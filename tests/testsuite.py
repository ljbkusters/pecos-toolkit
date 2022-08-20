#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
testsuite.py
@author Luc Kusters
@date 20-08-2022
"""

import unittest
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s: %(levelname)s: %(message)s")


class LoggedTestCase(unittest.TestCase):

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        """docstring for setUpClass"""
        print("")
        cls.logger.info(f"Running class: {cls.__name__}")
