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
from mc_states.utils import memoize_cache
import socket
import yaml
import logging

__name = 'cloud'
log = logging.getLogger(__name__)
PREFIX = 'makina-states.cloud'


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
        'script': ('/srv/mastersalt/makina-states/'
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
        'is': {'compute_node': False,
               'vm': False,
               'controller': False},
        'lxc.defaults.backing': 'dir'
    }
    return data


def extpillar_settings(id_=None, ttl=30, *args, **kw):
    '''
    return the cloud global configuation
    opts['id'] should resolve to mastersalt
    '''
    def _do(id_=None):
        _s = __salt__
        _o = __opts__
        if id_ is None:
            id_ = _s['mc_pillar.mastersalt_minion_id']()
        conf = _s['mc_pillar.get_configuration'](
            _s['mc_pillar.mastersalt_minion_id']())
        extdata = _s['mc_pillar.get_global_clouf_conf']('cloud')
        default_env = _s['mc_env.ext_pillar'](id_).get('env', '')
        data = _s['mc_utils.dictupdate'](
            _s['mc_utils.dictupdate'](
                default_settings(), {
                    'ssl': {'ca': {'ca_name': id_}},
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
    cache_key = 'mc_cloud.extpillar_settings{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def is_a_vm(id_=None, ttl=30):
    def _do(id_=None):
        if id_ is None:
            id_ = __grains__['id']
        _s = __salt__
        vms = _s['mc_cloud_compute_node.get_vms']()
        if id_ in vms:
            return True
        return False
    cache_key = 'mc_cloud.is_a_vm{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)

def is_a_compute_node(id_=None, ttl=30):
    def _do(id_=None):
        if id_ is None:
            id_ = __grains__['id']
        _s = __salt__
        targets = _s['mc_cloud_compute_node.get_targets']()
        if id_ in targets:
            return True
        return False
    cache_key = 'mc_cloud.is_a_compute_node{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def is_a_controller(id_=None, ttl=30):
    def _do(id_):
        if id_ is None:
            id_ = __grains__['id']
        _s = __salt__
        conf = _s['mc_pillar.get_configuration'](id_)
        if (
            (_s['mc_pillar.mastersalt_minion_id']() == id_)
            or conf.get('cloud_master', False)
        ):
            return True
        return False
    cache_key = 'mc_cloud.is_a_controller{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def is_a_cloud_member(id_=None):
    if id_ is None:
        id_ = __grains__['id']
    return any([is_a_vm(id_),
                is_a_compute_node(id_),
                is_a_controller(id_)])


def ext_pillar(id_, *args, **kw):
    '''
    makina-states cloud extpillar
    '''
    data = {}
    _s = __salt__
    extdata = extpillar_settings(id_)
    vms = _s['mc_cloud_compute_node.get_vms']()
    targets = _s['mc_cloud_compute_node.get_targets']()
    if is_a_vm(id_):
        extdata['is']['vm'] = True
        vmvt = vms[id_]['vt']
        extdata['is']['{0}_vm'.format(vmvt)] = True
        nodetype_vt = {'lxc': 'lxccontainer',
                       'docker': 'dockercontainer',
                       'kvm': 'kvm'}.get(vmvt, None)
        if nodetype_vt:
            for pref in [
                'makina-states.nodetypes.is',
                'makina-states.nodetypes.has'
            ]:
                spref = '{0}.{1}'.format(pref, nodetype_vt)
                data[spref] = True
    if is_a_compute_node(id_):
        extdata['is']['compute_node'] = True
        for i in targets[id_]['vts']:
            extdata['is']['{0}_compute_node'.format(i)] = True
    if any([
        extdata['is']['vm'],
        extdata['is']['compute_node']
    ]):
        data.update(_s['mc_cloud_vm.ext_pillar'](id_))
    if any([
        extdata['is']['controller'],
        extdata['is']['compute_node']
    ]):
        data.update(_s['mc_cloud_compute_node.ext_pillar'](id_))
    if is_a_controller(id_):
        extdata['is']['controller'] = True
    # if any of vm/computenode/controller
    # expose global cloud conf
    if any(extdata['is'].values()):
        data.update(_s['mc_cloud_images.ext_pillar'](id_))
        data[PREFIX] = extdata
    return data


'''
On node side, after ext pillar is loaded
'''


def is_(typ):
    is_proxied = False
    gr = 'makina-states.cloud.is.{0}'.format(typ)
    try:
        with open('/etc/mastersalt/grains') as fic:
            is_proxied = bool(yaml.load(fic).get(gr))
    except Exception:
        pass
    if not is_proxied:
        is_proxied = __salt__['mc_utils.get'](gr)
    return is_proxied


def is_vm():
    return is_('vm')


def is_compute_node():
    return is_('compute_node')


def is_controller():
    return is_('controller')


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
                'ssl': {'ca': {'ca_name': _s[
                    'mc_pillar.mastersalt_minion_id']()}},
                'prefix': prefix,
                'master_port': _s['config.get']('master_port'),
                'master': _s['mc_pillar.mastersalt_minion_id'](),
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
            'saltify': {'active': False}})
    return _registry()
#
