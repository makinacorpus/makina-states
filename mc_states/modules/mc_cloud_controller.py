# -*- coding: utf-8 -*-
'''
.. _module_mc_cloud_controller:

mc_cloud_controller / cloud related variables
==============================================

- This contains generate settings around salt_cloud
- This contains also all targets to be driven using the saltify driver
- LXC driver profile and containers settings are in :ref:`module_mc_cloud_lxc`.

'''
# Import salt libs
import mc_states.utils

__name = 'mc_cloud_controller'


def gen_id(name):
    return name.replace('.', '-')


def settings():
    """
    makina-states cloud controller common options

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
          ssh_gateway (all the gw params are opt.)
               ssh gateway info
          ssh_gateway_port
               ssh gateway info
          ssh_gateway_user
               ssh gateway info
          ssh_gateway_key
               ssh gateway info

    """
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        localsettings = __salt__['mc_localsettings.settings']()
        ct_registry = __salt__['mc_controllers.registry']()
        salt_settings = __salt__['mc_salt.settings']()
        pillar = __pillar__
        if (
            ct_registry['is']['mastersalt']
            or ct_registry['is']['mastersalt_master']
        ):
            root = salt_settings['msaltRoot']
            prefix = salt_settings['mconfPrefix']
        else:
            root = salt_settings['saltRoot']
            prefix = salt_settings['confPrefix']
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.cloud', {
                'root': root,
                'prefix': prefix,
                'mode': 'mastersalt',
                'bootsalt_args': '-C --from-salt-cloud -no-M',
                'bootsalt_mastersalt_args': (
                    '-C --from-salt-cloud --mastersalt-minion'),
                'bootsalt_branch': None ,
                'master_port': __salt__['config.get']('master_port'),
                'master': __grains__['fqdn'],
                'saltify_profile': 'salt',
                'pvdir': prefix + "/cloud.providers.d",
                'pfdir': prefix + "/cloud.profiles.d",
                'ssh_gateway': None,
                'ssh_gateway_user': 'root',
                'ssh_gateway_key': '/root/.ssh/id_dsa',
                'ssh_gateway_port': 22,
            }
        )
        if not data['bootsalt_branch']:
            data['bootsalt_branch'] = {
                'prod': 'stable',
                'preprod': 'stable',
            }.get(localsettings['default_env'], None)
        if not data['bootsalt_branch']:
            k = data['mode'] == 'mastersalt' and 'mastersaltCommonData' or 'saltCommonData'
            data['bootsalt_branch'] = salt_settings[k][
                'confRepos']['makina-states']['rev']
        if not data['bootsalt_branch']:
            data['bootsalt_branch'] = 'master'

        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
