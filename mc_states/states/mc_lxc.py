#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
mc_lxc / Spin up LXC containers and attach them to (master)salt
================================================================
'''
__docformat__ = 'restructuredtext en'
from salt.states import postgres_extension as postgres
import difflib
import datetime
import traceback

# vim:set et sts=4 ts=4 tw=80:
