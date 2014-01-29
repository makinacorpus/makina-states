#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import os
import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest

J = os.path.join
D = os.path.dirname

STATES_DIR = J(D(D(D(__file__))), '_modules')


class ModuleCase(unittest.TestCase):
    '''Base test class'''



# vim:set et sts=4 ts=4 tw=80:
