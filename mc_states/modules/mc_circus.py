# -*- coding: utf-8 -*-
'''
mc_circus / circus functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'circus'

log = logging.getLogger(__name__)


def settings():
    '''
    circus settings

    location
        installation directory

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locs = localsettings['locations']
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.circus', {
                'location': locs['apps_dir'] + '/circus',
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
