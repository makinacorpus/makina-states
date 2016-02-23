#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import sys
try:
    import docker
    import mc_states
    import salttesting
    import salt
    import requests
except ImportError:
    sys.exit(0)
sys.exit(1)
# vim:set et sts=4 ts=4 tw=80:
