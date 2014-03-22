# -*- coding: utf-8 -*-
'''
.. _module_mc_cloud_controller:

mc_cloud_controller / cloud related variables
==============================================

- This contains generate settings around salt_cloud
- This contains also all targets to be driven using the saltify driver
- LXC driver profile and containers settings are in :ref:`module_mc_lxc`.

'''
# Import salt libs
import mc_states.utils

__name = 'cloud_controller'


def gen_id(name):
    return name.replace('.', '-')


def settings():
    """
          master
            The default master to link to into salt cloud profile
          master_port
            The default master port to link to into salt cloud profile
          mode
            (salt or mastersal (default)t)
          pvdir
            salt cloud providers directory
          pfdir
            salt cloud profile directory
          bootsalt_branch
            bootsalt branch to use (default: master or prod if prod)
          bootsalt_args
            makina-states bootsalt args in salt mode
          bootsalt_mastersalt_args
            makina-states bootsalt args in mastersalt mode
          keep_tmp
            keep tmp files

            ::

                'salty_targets': {
                    #'id': {
                    #    'name': 'germaine.tld',
                    #    'ssh_host': 'ip_or_dns',
                    #    'profile': 'salt-minion',
                    #    'ssh_username': 'foo',
                    #    'password': 'password',
                    #    'sudo_password': 'sudo_password',
                    #    'sudo': True,
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
            'makina-states.services.cloud', {
                'prefix': prefix,
                'mode': 'mastersalt',
                'bootsalt_args': '-C --from-salt-cloud -no-M',
                'bootsalt_mastersalt_args': (
                    '-C --from-salt-cloud --mastersalt-minion'),
                'bootsalt_branch': {
                    'prod': 'stable',
                    'preprod': 'stable',
                    'dev': 'master',
                }.get(localsettings['default_env'], 'dev'),
                'master_port': __salt__['config.get']('master_port'),
                'master': __grains__['fqdn'],
                'saltify_profile': 'salt',
                'pvdir': prefix + "/cloud.providers.d",
                'pfdir': prefix + "/cloud.profiles.d",
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
