# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
'''
.. _module_mc_haproxy:

mc_haproxy / haproxy functions
==================================



'''

# Import python libs
import copy
import json
import logging
import re
import os
from salt.utils.odict import OrderedDict
import mc_states.api

__name = 'haproxy'
PREFIX ='makina-states.services.proxy.{0}'.format(__name)
log = logging.getLogger(__name__)

OBJECT_SANITIZER = re.compile('[\\\@+\$^&~"#\'()\[\]%*.:/]',
                              flags=re.M | re.U | re.X)


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
        data = __salt__['mc_utils.defaults'](
            PREFIX, {
                'location': locs['conf_dir'] + '/haproxy',
                'config_dir': '/etc/haproxy',
                'rotate': __salt__['mc_logrotate.settings']()['days'],
                'config': 'haproxy.cfg',
                'user': 'haproxy',
                'group': 'haproxy',
                'defaults': {'extra_opts': '', 'enabled': '1'},
                'configs': {'/etc/haproxy/haproxy.cfg': {},
                            '/etc/systemd/system/haproxy.service': {},
                            '/etc/haproxy/cfg.d/backends.cfg': {},
                            '/etc/haproxy/cfg.d/dispatchers.cfg': {},
                            '/etc/haproxy/cfg.d/frontends.cfg': {},
                            '/etc/haproxy/cfg.d/listeners.cfg': {},
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
        )
        return data
    return _settings()


def sanitize(key):
    if isinstance(key, list):
        key = '_'.join(key)
    return OBJECT_SANITIZER.sub('_', key)


def get_object_name(mode, port,
                    prefix='o',
                    host=None,
                    regex=None,
                    wildcard=None,
                    **kwargs):
    name = '{0}{1}_{2}'.format(prefix, mode, port)
    if host:
        key = 'host'
        id_ = host
    elif regex:
        key = 'regex'
        id_ = regex
    elif wildcard:
        key = 'wildcard'
        id_ = wildcard
    else:
        key = None
        id_ = None
    if key:
        name += '_{0}_{1}'.format(key, sanitize(id_))
    return name


def get_backend_name(mode, port,
                     host=None,
                     regex=None,
                     wildcard=None,
                     **kwargs):
    return get_object_name(prefix='b',
                           mode=mode,
                           port=port,
                           host=host,
                           regex=regex,
                           wildcard=wildcard,
                           **kwargs)


def get_frontend_name(mode, port,
                      host=None,
                      regex=None,
                      wildcard=None,
                      **kwargs):
    return get_object_name(prefix='f',
                           mode=mode,
                           port=port,
                           host=host,
                           regex=regex,
                           wildcard=wildcard,
                           **kwargs)


def ordered_backend_opts(opts=None):
    if not opts:
        opts = []
    opts = copy.deepcopy(opts)

    def sort(opt, count={'count': 0}):
        count['count'] += 1
        pref = count['count']
        opt = opt.strip()
        if opt.startswith('balance '):
            pref += 100
        elif opt.startswith('option '):
            pref += 500
        elif opt.startswith('tcp-check '):
            pref += 600
        elif opt.startswith('http-check '):
            pref += 600
        elif opt.startswith('http-request '):
            pref += 700
        elif opt.startswith('timeout '):
            pref += 800

        return '{0:04d}_{1}'.format(pref, opt)

    opts.sort(key=sort)
    return opts


def ordered_frontend_opts(opts=None):
    if not opts:
        opts = []
    opts = copy.deepcopy(opts)

    def sort(opt, count={'count': 0}):
        count['count'] += 1
        pref = count['count']
        opt = opt.strip()
        if opt.startswith('acl '):
            pref += 100
        elif 'use_backend' in opt:
            pref += 500
        elif 'default_backend' in opt:
            pref += 900
        if ' rgx_' in opt:
            pref += 20
        elif ' wc_' in opt:
            pref += 70
        elif ' host_' in opt:
            pref += 50
        return '{0:04d}_{1}'.format(pref, opt)

    opts.sort(key=sort)
    return opts


def registrations(*args, **kwargs):
    '''
    Sanytize a haproxy payload before storing in the mine'''
    payload = copy.deepcopy(kwargs.get('payload', {}))
    for k in [a for a in payload if a != __opts__['id']]:
        payload.pop(k, None)
    for k in [a for a in payload]:
        sub = payload[k]
        for a in [b for b in sub]:
            if a not in [
                'regexes', 'hosts', 'frontends', 'wildcard'
            ]:
                raise Exception(
                    'Invalid payload entry {0}\n {1}'.format(
                        a, json.dumps(payload)))
    return payload
# vim:set et sts=4 ts=4 tw=80:
