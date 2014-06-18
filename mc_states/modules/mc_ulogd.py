# -*- coding: utf-8 -*-
'''
.. _module_mc_ulogd:

mc_ulogd / ulogd functions
==================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import mc_states.utils

__name = 'ulogd'

log = logging.getLogger(__name__)


def settings():
    '''
    ulogd settings


    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        nt_reg = __salt__['mc_nodetypes.registry']()
        locs = __salt__['mc_locations.settings']()
        service = 'ulogd'
        if (
            grains['os'] in ['Ubuntu'] 
            and (grains.get('oscodename', '') not in ['precise'])
        ):
            service = 'ulogd2'
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.log.ulogd', {
                'ulog_emu': True,
                'nflog_emu': True,
                'service_name': service,
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
