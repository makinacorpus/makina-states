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


def settings():
    '''
    controller node settings

        controllers
            list of controllers
                for now, just one, the current minion
                which is certainly the mastersalt master
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        #compute_data = OrderedDict()
        #compute_data = _register_default_settings_for(compute_data)
        data = __salt__['mc_utils.defaults'](
            'makina-states.cloud.controller', {
                'controllers': {
                    __grains__['id']: {
                    }
                },
                'computes_nodes': [],
                'vts': ['lxc'],
            })
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
