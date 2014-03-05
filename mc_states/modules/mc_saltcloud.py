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


def gen_id(name):
    return name.replace('.', '-')


def settings():
    """
          master
            TDB
          master_port
            TDB
          pvdir
            TDB
          pfdir
            TDB
          targets
            TDB

            ::

                'targets': {
                    #'id': {
                    #    'name': 'dns',
                    #    'ssh_username': 'foo',
                    #    'password': 'password',
                    #    'sudo_password': 'sudo_password',
                    #    'sudo': 'foo',
                    #}
    """
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        localsettings = __salt__['mc_localsettings.settings']()
        salt_registry = __salt__['mc_controllers.registry']()
        salt_settings = __salt__['mc_salt.settings']()
        resolver = __salt__['mc_utils.format_resolve']
        pillar = __pillar__
        locs = localsettings['locations']
        if salt_registry['is']['mastersalt_master']:
            prefix = salt_settings['mconfPrefix']
        else:
            prefix = salt_settings['confPrefix']
        data = __salt__['mc_utils.defaults'](
            'makina-states.controllers.salt_cloud', {
                'prefix': prefix,
                'master': __grains__['fqdn'],
                'master_port': '4506',
                'pvdir': prefix + "/cloud.providers.d",
                'pfdir': prefix + "/cloud.profiles.d",
                'targets': {
                    #'id': {
                    #    'name': 'dns',
                    #    'ssh_username': 'foo',
                    #    'password': 'password',
                    #    'sudo_password': 'sudo_password',
                    #    'sudo': 'foo',
                    #}
                }
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
