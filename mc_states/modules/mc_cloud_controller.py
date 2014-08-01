# -*- coding: utf-8 -*-
'''
.. _module_mc_cloud_controller:

mc_cloud_controller / cloud related variables
==============================================



- This contains generate settings around salt_cloud
- This contains also all targets to be driven using the saltify driver
- LXC driver profile and containers settings are in :ref:`module_mc_cloud_lxc`.

'''

# Import python libs
import logging
# Import salt libs
from copy import deepcopy
import os
from salt.utils.odict import OrderedDict
import copy
import mc_states.api
from salt.modules import tls as tlsm

from mc_states.modules.mc_pillar import PILLAR_TTL
from mc_states.modules.mc_ssl import (
    CertificateNotFoundError,
    CertificateCreationError,
    MissingKeyError,
    MissingCertError)
try:
    import OpenSSL
    HAS_SSL = True
except:
    HAS_SSL = False

log = logging.getLogger(__name__)
__name = 'mc_cloud_controller'
PREFIX = 'makina-states.cloud.cloud_controller'


def gen_id(name):
    return name.replace('.', '-')


def default_settings():
    _s = __salt__
    data = {'controller': _s['mc_pillar.minion_id'](),
            'vts': {'generic': True,
                      'saltify': True,
                      'lxc': False,
                      'kvm': False},
            'compute_nodes': OrderedDict(),
            'vms': OrderedDict()}
    return data


def extpillar_settings(id_=None, limited=False, ttl=PILLAR_TTL):
    def _do(id_=None, limited=False):
        _s = __salt__
        gconf = _s['mc_pillar.get_configuration'](
            _s['mc_pillar.minion_id']())
        gdata = {'vts': {'lxc': gconf.get('cloud_control_lxc', True),
                         'kvm': gconf.get('cloud_control_kvm', True)}}
        extdata = _s['mc_pillar.get_global_clouf_conf']('cloud')
        data = _s['mc_utils.dictupdate'](default_settings(),
                                         _s['mc_utils.dictupdate'](gdata, extdata))
        return data
    cache_key = 'mc_cloud_controller.extpillar_settings{0}{1}'.format(
        id_, limited)
    return __salt__['mc_utils.memoize_cache'](_do, [id_, limited], {}, cache_key, ttl)


def ext_pillar(id_=None, prefixed=True, limited=False, ttl=PILLAR_TTL):
    def _do(id_=None, prefixed=True, limited=False):
        if not id_:
            id_ = __grains__['id']
        _s = __salt__
        expose = any([_s['mc_cloud.is_a_controller'](id_),
                      _s['mc_cloud.is_a_vm'](id_),
                      _s['mc_cloud.is_a_compute_node'](id_)])
        if not expose:
            return {}
        data = extpillar_settings(id_)
        conf_targets = _s['mc_cloud_compute_node.get_targets']()
        conf_vms = _s['mc_cloud_compute_node.get_vms']()
        compute_node_data = conf_targets.get(id_, None)
        dtargets = data['compute_nodes']
        dvms = data['vms']
        if _s['mc_cloud.is_a_controller'](id_):
            expose = True
            dtargets = _s['mc_utils.dictupdate'](dtargets, conf_targets)
            dvms = _s['mc_utils.dictupdate'](dvms, conf_vms)
        else:
            data.pop('vts', None)
        if _s['mc_cloud.is_a_compute_node'](id_):
            expose = True
            dtargets = _s['mc_utils.dictupdate'](
                dtargets, {id_: compute_node_data})
            dvms = _s['mc_utils.dictupdate'](
                dvms, dict([(vm, conf_vms[vm])
                            for vm in conf_targets[id_]['vms']]))
        if _s['mc_cloud.is_a_vm'](id_):
            expose = True
            tid = conf_vms[id_]['target']
            tdata = conf_targets[tid]
            tdata['vms'] = dict([(vm, tdata['vms'][vm])
                                 for vm in tdata['vms']
                                 if vm == id_])
            dtargets = _s['mc_utils.dictupdate'](dtargets, {tid: tdata})
            dvms = _s['mc_utils.dictupdate'](dvms, {id_: conf_vms[id_]})
        data['compute_nodes'] = dtargets
        data['vms'] = dvms
        if prefixed:
            data = {PREFIX: data}
        return data
    cache_key = 'mc_cloud_controller.extpillar{0}{1}{2}'.format(
        id_, prefixed, limited)
    return __salt__['mc_utils.memoize_cache'](_do, [id_, prefixed, limited], {}, cache_key, ttl)


def settings(ttl=60):
    '''
    compute node related settings
    '''
    def _do():
        _s = __salt__
        data = _s['mc_utils.defaults'](PREFIX, default_settings())
        return data
    cache_key = '{0}.{1}'.format(__name, 'settings')
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)
