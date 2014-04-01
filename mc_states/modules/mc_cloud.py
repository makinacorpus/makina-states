# -*- coding: utf-8 -*-

'''
.. _module_mc_cloud:

mc_cloud / cloud registries & functions
==============================================

'''

# Import salt libs
import mc_states.utils
import yaml

__name = 'cloud'


def is_vm():
    is_proxied = False
    gr = 'makina-states.cloud.is.vm'
    try:
        with open('/etc/mastersalt/grains') as fic:
            is_proxied = bool(yaml.load(fic).get(gr))
    except Exception:
        pass
    if not is_proxied:
        is_proxied = __salt__['mc_utils.get'](gr)
    return is_proxied


def metadata():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['services'])
    return _metadata()


def settings():
    '''
    Global services registry
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        """
        makina-states cloud global configuration options

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

        is
            mapping with various informations

            controller
                is this minion a cloud controller

            compute_node
                is this minion a cloud compute node

            vm
                is this minion a cloud operating vm

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
                'all_sls_dir': (
                    'cloud-controller'
                ),
                'compute_node_sls_dir': (
                    '{all_sls_dir}/controller'
                ),
                'compute_node_sls_dir': (
                    '{all_sls_dir}/compute_node'
                ),
                'prefix': prefix,
                'mode': 'mastersalt',
                'bootsalt_args': '-C --from-salt-cloud -no-M',
                'bootsalt_mastersalt_args': (
                    '-C --from-salt-cloud --mastersalt-minion'),
                'bootsalt_branch': None,
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
            'generic': {'active': False},
            'lxc': {'active': False},
            'saltify': {'active': False},
        })
    return _registry()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
