# -*- coding: utf-8 -*-
'''
.. _module_mc_rsyslog:

mc_rsyslog / rsyslog functions
==================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import mc_states.utils

__name = 'rsyslog'

log = logging.getLogger(__name__)


def settings():
    '''
    rsyslog settings

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        locs = localsettings['locations']
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.log.rsyslog', {
                'spool': '/var/spool/rsyslog',
                'user': 'syslog',
                'group': 'syslog',
                'admin_group': 'adm',
                'listen_addr': '0.0.0.0',
                'udp_port': '514',
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
