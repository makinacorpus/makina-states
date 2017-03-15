#!/usr/bin/env python
'''

.. _pillar_mc_pillar_jsons:

mc_pillar_jsons
===============================================



'''
import logging
import salt.utils

log = logging.getLogger(__name__)


def ext_pillar(id_, pillar, *args, **kw):
    data = salt.utils.odict.OrderedDict()
    for i in ['mc_pillar.json_pillars']:
        data = __salt__['mc_utils.dictupdate'](
            data, __salt__[i](id_, pillar, *args, **kw))
    data['mc_pillar_jsons.loaded'] = True
    return data

# vim:set et sts=4 ts=4 tw=80:
