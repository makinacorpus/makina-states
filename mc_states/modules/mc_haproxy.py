# -*- coding: utf-8 -*-
'''
.. _module_mc_haproxy:

mc_haproxy / haproxy functions
==================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import mc_states.utils

__name = 'haproxy'

log = logging.getLogger(__name__)


def settings():
    '''
    haproxy settings

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        shorewall = __salt__['mc_shorewall.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        services_registry = __salt__['mc_services.registry']()
        locs = localsettings['locations']
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.firewall.haproxy', {
                'location': locs['conf_dir'] + '/haproxy',
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
