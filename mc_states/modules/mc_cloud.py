# -*- coding: utf-8 -*-

'''
.. _module_mc_cloud:

mc_cloud / cloud registries & functions
==============================================

'''

# Import salt libs
import os
import copy
import mc_states.utils
import socket
import yaml
import logging

__name = 'cloud'
log = logging.getLogger(__name__)


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


def default_settings():
    '''
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

    '''
    root = '/srv/mastersalt'
    prefix = '/etc/mastersalt'
    data = {
        'root': root,
        'all_pillar_dir': (
            '/srv/mastersalt-pillar/cloud-controller'
        ),
        'ssl': {
            'cert_days': 365*1000,
            'ca': {
                'ca_name': __grains__['id'],
                'bits': 2048,
                'days': 365*1000,
                'CN': 'makina-states-cloud-controller',
                'C': 'FR',
                'ST': 'PdL',
                'L': 'Nantes',
                'O': 'Makina Corpus',
                'OU': None,
                'emailAddress': 'contact@makina-corpus.com',
            }
        },
        'all_sls_dir': 'cloud-controller',
        'compute_node_sls_dir': (
            '{all_sls_dir}/controller'
        ),
        'compute_node_sls_dir': (
            '{all_sls_dir}/compute_node'
        ),
        'compute_node_pillar_dir': (
            '{all_pillar_dir}/compute_node'
        ),
        'ssl_dir': '{all_sls_dir}/ssl',
        'ssl_pillar_dir': '{all_pillar_dir}/ssl',
        'prefix': prefix,
        'mode': 'mastersalt',
        'script': (
            '/srv/mastersalt/makina-states/'
            '_scripts/boot-salt.sh'),
        'bootsalt_shell': 'bash',
        'bootsalt_args': '-C --from-salt-cloud -no-M',
        'bootsalt_mastersalt_args': (
            '-C --from-salt-cloud --mastersalt-minion'),
        'bootsalt_branch': None,
        'master_port': __opts__.get('master_port'),
        'master': __grains__['id'],
        'saltify_profile': 'salt',
        'pvdir': prefix + "/cloud.providers.d",
        'pfdir': prefix + "/cloud.profiles.d",
        'ssh_gateway_password': None,
        'ssh_gateway': None,
        'ssh_gateway_user': 'root',
        'ssh_gateway_key': '/root/.ssh/id_dsa',
        'ssh_gateway_port': 22,
        # states registry settings
        'generic': True,
        'saltify': True,
        'lxc': False,
        'kvm': False,
        'lxc.defaults.backing': 'dir'
    }
    return data


def extpillar_settings(id_=None, *args, **kw):
    '''
    return the cloud global configuation
    opts['id'] should resolve to mastersalt
    '''
    _s = __salt__
    _o = __opts__
    if id_ is None:
        id_ = __opts__['id']
    conf = _s['mc_pillar.get_configuration'](_o['id'])
    extdata = _s['mc_pillar.get_global_clouf_conf']('cloud')
    default_env = _s['mc_env.ext_pillar'](id_).get('env', '')
    data = _s['mc_utils.dictupdate'](
        _s['mc_utils.dictupdate'](
            default_settings(), {'ssl': {'ca': {'ca_name': id_}},
                                 'master_port': _o.get('master_port'),
                                 'master': id_,
                                 # states registry settings
                                 'generic': True,
                                 'saltify': True,
                                 'lxc': conf.get('cloud_control_lxc', False),
                                 'kvm': conf.get('cloud_control_kvm', False)}
        ), extdata)
    if not data['bootsalt_branch']:
        data['bootsalt_branch'] = {'dev': 'master',
                                   'prod': 'stable',
                                   'preprod': 'stable'}.get(
                                       default_env, 'stable')
    data = _s['mc_utils.format_resolve'](data)
    return data


def ext_pillar(id_, *args, **kw):
    '''
    makina-states cloud extpillar
    '''
    _s = __salt__
    _o = __opts__
    settings = extpillar_settings(id_)
    return {_p: data}


'''
On node side, after ext pillar is loaded
'''


def metadata():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['services'])
    return _metadata()


def settings():
    '''
    Global cloud configuration
    '''
    _s = __salt__
    _g = __grains__
    _o = __opts__
    ct_registry = _s['mc_controllers.registry']()
    salt_settings = _s['mc_salt.settings']()
    if (
        ct_registry['is']['mastersalt']
        or ct_registry['is']['cloud_master']
    ):
        root = salt_settings['msaltRoot']
        prefix = salt_settings['mconfPrefix']
    else:
        root = salt_settings['saltRoot']
        prefix = salt_settings['confPrefix']
    #    fic.write(pformat(__opts__))
    data = _s['mc_utils.defaults'](
        'makina-states.cloud',
        _s['mc_utils.dictupdate'](
            default_settings(), {
                'root': root,
                'all_pillar_dir': (
                    os.path.join(
                        _o['pillar_roots']['base'][0],
                        'cloud-controller')),
                'ssl': {'ca': {'ca_name': _o['id']}},
                'prefix': prefix,
                'master_port': _s['config.get']('master_port'),
                'master': _o['id'],
                'pvdir': prefix + "/cloud.providers.d",
                'pfdir': prefix + "/cloud.profiles.d",
            }))
    if not data['bootsalt_branch']:
        data['bootsalt_branch'] = {
            'prod': 'stable',
            'preprod': 'stable',
        }.get(_s['mc_env.settings']()['default_env'], None)
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


def registry():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'generic': {'active': False},
            'lxc': {'active': False},
            'kvm': {'active': False},
            'saltify': {'active': False},
        })
    return _registry()
#
