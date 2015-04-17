# -*- coding: utf-8 -*-
'''
.. _module_mc_psad:

mc_psad / psad functions
==================================



'''

# Import python libs
import logging
import os
import mc_states.api

__name = 'psad'

log = logging.getLogger(__name__)


def settings():
    '''
    psad settings

        alertdest
            (root@fqdn)
        hostname
            (fqdn)

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.firewall.psad', {
                'alertdest': 'root@{0}'.format(__grains__['fqdn']),
                'hostname': __grains__['fqdn'],
            }
        )
        return data
    return _settings()



#
