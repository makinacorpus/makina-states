#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
'''
code may seem not very pythonic, this is because at first, this is
a port for a jinja based dynamic pillar
'''

# Import salt libs
import logging


log = logging.getLogger(__name__)


def ext_pillar(id_, pillar, *args, **kw):
    return __salt__['mc_pillar.ext_pillar'](
        id_, pillar, *args, **kw)

# vim:set et sts=4 ts=4 tw=80:
