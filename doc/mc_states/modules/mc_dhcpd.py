# -*- coding: utf-8 -*-
'''

.. _module_mc_dhcpd:

mc_dhcpd / dhcpd registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_dhcpd

'''
# Import python libs
import logging
import mc_states.api
from salt.utils.pycrypto import secure_password
import base64
import getpass
import hashlib
from base64 import urlsafe_b64encode as encode
import os
__name = 'dhcpd'


log = logging.getLogger(__name__)


def settings():
    '''
    dhcpd registry

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _g = __grains__
        _p = __pillar__
        locations = __salt__['mc_locations.settings']()
        local_conf = __salt__['mc_macros.get_local_registry'](
            'dhcpd', registry_format='pack')
        cn_pass = local_conf.setdefault('cn_pass', secure_password(32))
        pkgs = ['dhcp3-server']
        if _g.get('os') in ['Ubuntu']:
            if _g['osrelease'] >= 15.10:
                pkgs = ['isc-dhcp-server']
        dhcpdData = __salt__['mc_utils.defaults'](
            'makina-states.services.dns.dhcpd', {
                'dhcpd_directory': "/etc/dhcpd",
                'templates': {
                  '/etc/default/isc-dhcp-server': {},
                  '/etc/dhcp/dhcpd.conf': {},
                },
                'extra_dirs': [
                ],
                'defaults': {
                    'INTERFACES': '',
                    'OPTIONS': '',
                },
                'subnets': {},
                'hosts': {},
                'conf': {
                    'ddns_update_style': 'none',
                    'domain_name': 'example.org',
                    'default_lease_time': '864000',
                    'max_lease_time': '864000',
                    'log_facility': 'local7',
                    'domain_name_servers': (
                        'ns1.example.org, ns2.example.org'),
                },
                'pkgs': pkgs,
                'service_name': 'isc-dhcp-server',
            })
        return dhcpdData
    return _settings()
