# -*- coding: utf-8 -*-
'''
.. _module_mc_haproxy:

mc_haproxy / haproxy functions
==================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import mc_states.utils

__name = 'haproxy'

log = logging.getLogger(__name__)


def settings():
    '''
    haproxy settings

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        locs = localsettings['locations']
        #'capture cookie vgnvisitor= len 32',
        #'option    httpchk /index.html',
        #'cookie SERVERID rewrite',
        #'httpclose',
        #('rspidel ^Set-cookie:\ IP=    '
        # '# do not let this cookie tell '
        # 'our internal IP address'),
        df_listeners = {
            #'default-listener': {
            #    'bind': '0.0.0.0:10001',
            #    'raw_opts': [

            #        'balance roundrobin',
            #    ],
            #    'servers': [
            #        {
            #            'name': 'appl1',
            #            'bind': '192.168.34.23:8080',
            #            'opts': (
            #                'cookie '
            #                'app1inst1 check '
            #                'inter 2000 '
            #                'rise 2 '
            #                'fall 5'
            #            )
            #        }
            #    ]
            #},
        }
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.proxy.haproxy', {
                'location': locs['conf_dir'] + '/haproxy',
                'config_dir': '/etc/haproxy',
                'rotate': localsettings['rotate']['days'],
                'config': 'haproxy.cfg',
                'user': 'haproxy',
                'group': 'haproxy',
                'defaults': {'extra_opts': '',
                             'enabled': '1'},
                'config': {
                    'global': {
                        'logfacility': 'local0',
                        'loglevel': 'notice',
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
                            'auth': 'admin:admin',
                        },
                    }
                },
                'listeners': df_listeners,
                'backends': {},
                'frontends': {},
                'dispatchers': {
                   # 'appl2': {
                   #     'uri': '0.0.0.0:8082',
                   #     'uris': ['192.168.135.17:80']}
                },
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
