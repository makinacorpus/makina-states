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
    data = __salt__['mc_utils.defaults'](
        'makina-states.cloud.controller', {
            'controller': __opts__['id'],
            'compute_nodes': OrderedDict(),
            'vms': OrderedDict()})
    return data


def extpillar_settings(id_=None):
    _s = __salt__
    extdata = {}
    data = _s['mc_utils.dictupdate'](default_settings(), extdata)
    return data


def ext_pillar(id_=None):
    _s = __salt__
    expose = any([_s['mc_cloud.is_a_controller'](id_),
                  _s['mc_cloud.is_a_vm'](id_),
                  _s['mc_cloud.is_a_compute_node'](id_)])
    if not expose:
        return {}
    data = extpillar_settings(id_)
    conf_targets = _s['mc_cloud_compute_node.get_vms']()
    conf_vms = _s['mc_cloud_compute_node.get_all_vms']()
    compute_node_data = copy.deepcopy(conf_targets.get(id_, None))
    dtargets = data['compute_nodes']
    dvms = data['vms']
    if _s['mc_cloud.is_a_controller'](id_):
        expose = True
        dtargets = _s['mc_utils.dictupdate'](dtargets, conf_targets)
        dvms = _s['mc_utils.dictupdate'](dvms, conf_vms)
    if _s['mc_cloud.is_a_compute_node'](id_):
        expose = True
        dtargets = _s['mc_utils.dictupdate'](
            dtargets, {id_: compute_node_data})
        dvms = _s['mc_utils.dictupdate'](
            dvms, dict([(vm, copy.deepcopy(conf_vms[vm]))
                        for vm in conf_targets[id_]['vms']]))
    if _s['mc_cloud.is_a_vm'](id_):
        expose = True
        tid = conf_vms[id_]['target']
        tdata = copy.deepcopy(conf_targets[tid])
        tdata['vms'] = dict([(vm, tdata['vms'][vm])
                             for vm in tdata['vms']
                             if vm == id_])
        dtargets = _s['mc_utils.dictupdate'](
            dtargets, {tid: tdata})
        dvms = _s['mc_utils.dictupdate'](
            dvms, {id_: copy.deepcopy(conf_vms[id_])})
    data['compute_nodes'] = dtargets
    data['vms'] = dvms
    return {PREFIX: data}

def settings():
    '''
    compute node related settings
    '''
    _s = __salt__
    data = _s['mc_utils.defaults'](PREFIX, default_settings())
    return data
#
