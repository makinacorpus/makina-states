# -*- coding: utf-8 -*-
'''
.. _module_mc_saltcloud:

mc_saltcloud / saltcloud related variables
============================================
NOT IMPLEMENTED YET
'''
# Import salt libs
import mc_states.utils

__name = 'saltcloud'


def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        localsettings = __salt__['mc_localsettings.settings']()
        salt_regitry = __salt__['mc_controllers.registry']()
        salt_settings = __salt__['mc_salt.settings']()
        resolver = __salt__['mc_utils.format_resolve']
        pillar = __pillar__
        locs = localsettings['locations']
        data = __salt__['mc_utils.defaults'](
            'makina-states.controllers.salt_cloud', {
                'master': False,
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
