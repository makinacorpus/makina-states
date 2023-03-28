# -*- coding: utf-8 -*-
'''
.. _module_mc_ulogd:

mc_ulogd / ulogd functions
==================================
'''

# Import python libs
import logging
import mc_states.api

__name = 'ulogd'

log = logging.getLogger(__name__)


def settings():
    '''
    ulogd settings
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        utemplate = (
            'salt://makina-states/files/etc/ulogd.conf')
        service = 'ulogd2'
        if (
            grains['os'] in ['Ubuntu'] and
            (grains.get('oscodename', '') in ['precise'])
        ):
            utemplate = (
                'salt://makina-states/files/etc/ulogd1.conf')
            service = 'ulogd'
        enabled = not __salt__['mc_nodetypes.is_container']()
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.log.ulogd', {
                'enabled': enabled,
                'ulog_emu': True,
                'nflog_emu': True,
                'service_name': service,
                'confs': {'/etc/logrotate.d/ulogd2': {"mode": "644"},
                          "/etc/ulogd.conf": {
                              "source": utemplate,
                              "mode": "644"}}})
        return data
    return _settings()
