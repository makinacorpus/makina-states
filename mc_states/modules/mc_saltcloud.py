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

loglevelfmt = (
    "'%(asctime)s,%(msecs)03.0f "
    "[%(name)-17s][%(levelname)-8s] %(message)s'")


def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        localsettings = __salt__['mc_localsettings.settings']()
        salt_regitry = __salt__['mc_salt.regisry']()
        salt_settings = __salt__['mc_salt.settings']()
        resolver = __salt__['mc_utils.format_resolve']
        pillar = __pillar__
        locs = localsettings['locations']
        data = __salt__['mc_utils.defaults'](
            'makina-states.cloud', {
                'cloud_master': False,
                'profiles': {
                    # 'profileid': {
                    #   'box_name': {
                    #       'ip': xxx.xxx.xxx.xxx.xx
                    #             & other provider data to
                    #             feed the state}
                    #}
                }
            }
        )
        if (
            not __salt__['registry']['is']['salt_master']
            and not __salt__['registry']['is']['mastersalt_master']
        ):
            data['cloud_master'] = False
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
