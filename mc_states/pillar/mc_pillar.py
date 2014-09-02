#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import salt libs
import mc_states.utils
import random
import os
import logging


log = logging.getLogger(__name__)

__name = 'salt'


def ext_pillar(id_, pillar, *args, **kw):
    data = {'thisisa': 'test'}
    return data

# vim:set et sts=4 ts=4 tw=80:
