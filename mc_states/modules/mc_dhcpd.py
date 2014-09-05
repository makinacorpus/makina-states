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
import mc_states.utils
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
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        local_conf = __salt__['mc_macros.get_local_registry'](
            'dhcpd', registry_format='pack')
        cn_pass = local_conf.setdefault('cn_pass', secure_password(32))
        dhcpdData = __salt__['mc_utils.defaults'](
            'makina-states.services.dns.dhcpd', {
                'dhcpd_directory': "/etc/dhcpd",
                'extra_dirs': [
                ],
                'defaults': {
                    'INTERFACES': '',
                    'OPTIONS': '',
                },
                'pkgs': ['dhcp3-server'],
                'service_name': 'isc-dhcp-server',
            })
        return dhcpdData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
