#!/usr/bin/env python
'''

.. _module_mc_provider:

mc_provider / provider functions
============================================



Useful functions to locate a particular host
or setting
'''

__docformat__ = 'restructuredtext en'
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.api
from salt.utils.odict import OrderedDict

__name = 'provider'

log = logging.getLogger(__name__)


def settings():
    '''
    provider settings

        is
            booleans

            online
                are we on an online host
            ovh
                are we on an ovh host
            sys
                are we on an soyoustart host

        have_rpn
            online specific: do we have rpn

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        is_ovh = 'ovh' in __grains__['id']
        is_sys = __grains__['id'].startswith('sys-')
        is_online = 'online-dc' in __grains__['id']
        have_rpn = None
        ifaces = grains['ip_interfaces'].items()
        data = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.provider', {
                'is': {
                    'online': is_online,
                    'ovh': is_ovh,
                    'sys': is_sys,
                },
                'have_rpn': have_rpn,
            })
        if data['is']['online'] and data['have_rpn'] is None:
            for ifc in ['eth1', 'em1']:
                if True in [ifc == a[0] for a in ifaces]:
                    data['have_rpn'] = True  # must stay none if not found
        return data
    return _settings()



#
# vim:set et sts=4 ts=4 tw=80:
