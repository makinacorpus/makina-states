# -*- coding: utf-8 -*-
'''
.. _module_mc_haproxy:

mc_haproxy / haproxy functions
==================================



'''

# Import python libs
import logging
import os
from salt.utils.odict import OrderedDict
import mc_states.api

__name = 'haproxy'
PREFIX ='makina-states.services.proxy.{0}'.format(__name)
log = logging.getLogger(__name__)


def settings():
    '''
    haproxy settings

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        locs = __salt__['mc_locations.settings']()
        # 'capture cookie vgnvisitor= len 32',
        # 'option    httpchk /index.html',
        # 'cookie SERVERID rewrite',
        # 'httpclose',
        # ('rspidel ^Set-cookie:\ IP=    '
        #  '# do not let this cookie tell '
        #  'our internal IP address'),
        haproxy_password = __salt__['mc_utils.generate_stored_password'](
            'mc_haproxy.password')
        ssl = _s['mc_ssl.settings']()
        proxy_settings = _s['mc_proxy.settings']()
        reverse_proxy_addresses = proxy_settings['reverse_proxy_addresses']
        data = {
            'reverse_proxy_addresses': reverse_proxy_addresses,
            'location': locs['conf_dir'] + '/haproxy',
            'config_dir': '/etc/haproxy',
            'rotate': __salt__['mc_logrotate.settings']()['days'],
            'config': 'haproxy.cfg',
            'user': 'haproxy',
            'group': 'haproxy',
            'defaults': {'extra_opts': '', 'enabled': '1'},
            'configs': {'/etc/haproxy/haproxy.cfg': {},
                        '/etc/haproxy/extra/backends.cfg': {},
                        '/etc/systemd/system/haproxy.service': {},
                        '/etc/haproxy/extra/dispatchers.cfg': {},
                        '/etc/haproxy/extra/frontends.cfg': {},
                        '/etc/haproxy/extra/listeners.cfg': {},
                        '/etc/logrotate.d/haproxy': {},
                        '/etc/default/haproxy': {'mode': 755},
                        '/etc/init.d/haproxy': {'mode': 755},
                        '/usr/bin/mc_haproxy.sh': {'mode': 755},

                        '/etc/haproxy/errors/403.http': {},
                        '/etc/haproxy/errors/408.http': {},
                        '/etc/haproxy/errors/500.http': {},
                        '/etc/haproxy/errors/502.http': {},
                        '/etc/haproxy/errors/503.http': {},
                        '/etc/haproxy/errors/504.http': {}},
            'config': {
                'global': {
                    'logfacility': 'local0',
                    # upgrade to info to debug # activation of keepalive
                    # in cloud confs
                    'loglevel': 'info',
                    'loghost': '127.0.0.1',
                    'nbproc': '',
                    'node': __grains__['id'],
                    'ulimit': '65536',
                    'maxconn': '4096',
                    'stats_sock': '/var/run/haproxy.sock',
                    'stats_sock_lvl': 'admin',
                    'daemon': True,
                    'debug': False,
                    'quiet': False,
                    'chroot': '',
                },
                'default': {
                    'log': 'global',
                    'mode': 'http',
                    'options': ['httplog',
                                'abortonclose',
                                'redispatch',
                                'dontlognull'],
                    'retries': '3',
                    'maxconn': '2000',
                    'timeout': {
                        'connect': '7s',
                        'queue': '15s',
                        'client': '300s',
                        'server': '300s',
                    },
                    'stats': {
                        'enabled': True,
                        'uri': '/_balancer_status_',
                        'refresh': '5s',
                        'realm': 'haproxy\ statistics',
                        'auth': 'admin:{0}'.format(haproxy_password),
                    },
                }
            },
            'listeners': OrderedDict(),
            'backends': OrderedDict(),
            'frontends': OrderedDict(),
            'dispatchers': OrderedDict(),
        }
        data = __salt__['mc_utils.defaults'](PREFIX, data)
        return data
    return _settings()
