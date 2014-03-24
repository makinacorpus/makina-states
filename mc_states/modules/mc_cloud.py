# -*- coding: utf-8 -*-

'''
.. _module_mc_services:

mc_cloud / cloud registries & functions
==============================================

'''

# Import salt libs
import mc_states.utils

__name = 'cloud'


def metadata():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings'])
    return _metadata()


def settings():
    '''
    Global services registry
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        """
        makina-states cloud global configuration options

        compute_nodes
          information about current nodes

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
        ssh_gateway_password
             ssh gateway info
        """
        pillar = __pillar__
        grains = __grains__
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
            'makina-states.cloud', {
                'root': root,
                'vms_sls_dir': (
                    'cloud-controller/vms'
                ),
                'compute_node_sls_dir': (
                    'cloud-controller/compute_node'
                ),
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
                'ssh_gateway_password': None,
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
            if data['mode'] == 'mastersalt':
                k = 'mastersaltCommonData'
            else:
                k = 'saltCommonData'
            data['bootsalt_branch'] = salt_settings[k][
                'confRepos']['makina-states']['rev']
        if not data['bootsalt_branch']:
            data['bootsalt_branch'] = 'master'

        return data
    return _settings()


def registry():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'cloud.generic': {'active': False},
            'cloud.lxc': {'active': False},
            'cloud.saltify': {'active': False},
        })
    return _registry()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
