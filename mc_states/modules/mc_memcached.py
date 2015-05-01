# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# pylint: disable=W0105
'''

.. _module_mc_memcached:

mc_memcached / memcached registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_memcached

'''
# Import python libs
import logging
import mc_states.api
__name = 'memcached'


log = logging.getLogger(__name__)


def settings():
    '''
    memcached registry

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        memcachedData = __salt__['mc_utils.defaults'](
            'makina-states.services.dns.memcached', {
                'memcached_directory': "/etc/memcached",
                'templates': {
                    '/etc/default/memcached': (
                        'salt://makina-states/'
                        'files/etc/default/memcached'
                    ),
                    '/etc/memcached.conf': (
                        'salt://makina-states/'
                        'files/etc/memcached.conf'
                    ),
                },
                'extra_dirs': [
                ],
                'defaults': {
                    'ENABLED': 'yes',
                },
                'conf': {
                    'verbose': False,
                    'logfile': '/var/log/memcached.log',
                    'cap': '128',
                    'port': '11211',
                    'listen': '127.0.0.1',
                    'unitcachesize': '10M'
                },
                'pkgs': ['memcached', 'libmemcached-dev'],
                'service_name': 'memcached',
            })
        return memcachedData
    return _settings()
