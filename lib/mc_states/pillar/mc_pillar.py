#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _pillar_mc_pillar:

mc_pillar
===============================================



'''
'''
code may seem not very pythonic, this is because at first, this is
a port for a jinja based dynamic pillar
'''

# Import salt libs
import logging
import salt.utils


log = logging.getLogger(__name__)


def ext_pillar(id_, pillar, *args, **kw):
    data = salt.utils.odict.OrderedDict()
    for i in [
        'mc_pillar.ext_pillar',
        #'mc_cloud_compute_node.ext_pillar'
    ]:
        data = __salt__['mc_utils.dictupdate'](
            data, __salt__[i](id_, pillar, *args, **kw))
    data['mc_pillar.loaded'] = True
    return data

# vim:set et sts=4 ts=4 tw=80:
