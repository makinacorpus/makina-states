# -*- coding: utf-8 -*-
'''

.. _module_mc_proxy:

mc_proxy / proxy registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_proxy

'''
# Import python libs
import logging
import copy
import mc_states.api
from salt.utils.pycrypto import secure_password

__name = 'proxy'

log = logging.getLogger(__name__)


def is_reverse_proxied():
    _s, _g = __salt__, __grains__
    return __salt__['mc_cloud.is_vm']() or _s['mc_utils.get']('makina-states.is.reverse-proxied', False)


def settings():
    '''
    proxy registry

    is_reverse_proxied
        is proxy itself is reverse proxified (true in cloudcontroller mode)
    reverse_proxy_addresses
        authorized reverse proxied addresses
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s, _g = __salt__, __grains__
        reverse_proxy_addresses = []
        is_rp = is_reverse_proxied()
        if is_rp:
            gw = _g.get('makina.default_route', {}).get('gateway', '').strip()
            if gw and gw not in reverse_proxy_addresses:
                reverse_proxy_addresses.append(gw)
        proxyData = __salt__['mc_utils.defaults'](
            'makina-states.services.proxy.proxy', {
                'reverse_proxy_addresses': reverse_proxy_addresses,
            }
        )
        return proxyData
    return _settings()
