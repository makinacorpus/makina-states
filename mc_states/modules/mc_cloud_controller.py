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
import mc_states.utils
from mc_states.utils import memoize_cache
from salt.modules import tls as tlsm
import M2Crypto

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


def ensure_ca_present():
    '''Retrocompat'''
    return __salt__['mc_ssl.ensure_ca_present']()


def get_cert_for(domain, gen=False, domain_csr_data=None):
    '''Retrocompat'''
    return __salt__['mc_ssl.get_cert_for'](
        domain, gen, domain_csr_data)


def is_certificate_matching_domain(cert_path, domain):
    '''Retrocompat'''
    return __salt__['mc_ssl.is_certificate_matching_domain'](domain)


def domain_match(domain, cert_domain):
    '''Retrocompat'''
    return __salt__['mc_ssl.domain'](domain, cert_domain)


def load_certs(path):
    '''Retrocompat'''
    return __salt__['mc_ssl.domain_match'](path)


def get_certs_dir():
    '''Retrocompat'''
    return __salt__['mc_ssl.get_certs_dir']()


def search_matching_certificate(domain):
    '''Retrocompat'''
    return __salt__['mc_ssl.search_matching_certificate'](domain)


def ssl_certs(domains):
    '''Retrocompat'''
    return __salt__['mc_ssl.ssl_certs'](domains)


def default_settings():
    data = {'controller': _s['mc_pillar.mastersalt_minion_id'](),
            'vts': {'generic': True,
                      'saltify': True,
                      'lxc': False,
                      'kvm': False},
            'compute_nodes': OrderedDict(),
            'vms': OrderedDict()}
    return data


def extpillar_settings(id_=None, ttl=30):
    def _do(id_=None):
        _s = __salt__
        gconf = _s['mc_pillar.get_configuration'](
            _s['mc_pillar.mastersalt_minion_id']())
        gdata = {'vts': {'lxc': gconf.get('cloud_control_lxc', False),
                           'kvm': gconf.get('cloud_control_kvm', False)}}
        extdata = _s['mc_pillar.get_global_clouf_conf']('cloud')
        data = _s['mc_utils.dictupdate'](default_settings(),
                                         _s['mc_utils.dictupdate'](gdata, extdata))
        return data
    cache_key = 'mc_cloud_controller.extpillar_settings{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def ext_pillar(id_=None, ttl=30):
    def _do(id_=None):
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
            dtargets = _s['mc_utils.dictupdate'](
                dtargets, {tid: tdata})
            dvms = _s['mc_utils.dictupdate'](
                dvms, {id_: conf_vms[id_]})
        data['compute_nodes'] = dtargets
        data['vms'] = dvms
        return {PREFIX: data}
    cache_key = 'mc_cloud_controller.extpillar{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def settings(ttl=60):
    '''
    compute node related settings
    '''
    def _do():
        _s = __salt__
        data = _s['mc_utils.defaults'](PREFIX, default_settings())
        return data
    cache_key = '{0}.{1}'.format(__name, 'settings')
    return memoize_cache(_do, [], {}, cache_key, ttl)


#
