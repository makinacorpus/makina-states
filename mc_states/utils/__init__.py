#!/usr/bin/env python
'''
Utilities functions (deprecated location)
=========================================
'''
import logging
#import traceback
logging.getLogger(__name__).error(
    'Importing this module: {0} is deprecated,'
    ' import mc_states.api instead'.format(__name__))
#logging.getLogger(__name__).error(traceback.format_exc())
#traceback.print_stack()
from mc_states.api import *
# vim:set et sts=4 ts=4 tw=80:
