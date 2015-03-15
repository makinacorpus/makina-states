#!/usr/bin/env python
'''
Utilities functions (deprecated location)
=========================================
'''
import logging
logging.getLogger(__name__).error(
    'Importing this module: {0} is deprecated,'
    ' import mc_states.api instead'.format(__name__))
from mc_states.api import *
# vim:set et sts=4 ts=4 tw=80:
