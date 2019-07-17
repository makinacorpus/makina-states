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
import six
from salt.utils.odict import OrderedDict
import mc_states.api
from salt.exceptions import CommandExecutionError

__name = 'haproxy'
PREFIX ='makina-states.services.proxy.{0}'.format(__name)
log = logging.getLogger(__name__)

re_flags = re.M | re.U | re.X
OBJECT_SANITIZER = re.compile('[\\\@+\$^&~"#\'()\[\]%*.:/]',
                              flags=re_flags)

registration_prefix = 'makina-states.haproxy_registrations'
DEFAULT_FRONTENDS = {80: {}, 443: {}}
SSHPROXY = [
  'option tcplog',
  'tcp-request inspect-delay 5s',
  'tcp-request content accept if HTTP',
  'acl client_attempts_ssh payload(0,7) -m bin 5353482d322e30',
  'use_backend {ssh_proxy} if !HTTP',
  'use_backend {ssh_proxy} if client_attempts_ssh',
  'use_backend {http_proxy} if HTTP']

CIPHERS = '''\
ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:\
ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:\
DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:\
ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:\
ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384\
:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:\
DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:\
DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:\
AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:\
AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:\
!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:\
!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA\
'''


def get_ssh_backend_proxy_name(ssh_proxy_host, ssh_proxy_port, k='ssh'):
    return get_backend_name('tcp', ssh_proxy_port, '{0}_{1}'.format(k, ssh_proxy_host))


def version(default_ver='1.5'):
    try:
        ret = __salt__['cmd.run']('haproxy -v')
        ret = ret.split()[2]
    except (CommandExecutionError,):
        ret = default_ver
    return ret


wk_re = re.compile('[{](\s+ssl_fc\s+)[}]', flags=re_flags)
def replace_wk_opts(o):
    return wk_re.sub('{bracket}\\1{ebracket}', o)


def settings():
    '''
    haproxy settings

    '''
    _g = __grains__
    _s = __salt__
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        locs = _s['mc_locations.settings']()
        # 'capture cookie vgnvisitor= len 32',
        # 'option    httpchk /index.html',
        # 'cookie SERVERID rewrite',
        # 'httpclose',
        # ('rspidel ^Set-cookie:\ IP=    '
        #  '# not let this cookie tell '
        #  'our internal IP address'),
        haproxy_password = _s['mc_utils.generate_stored_password'](
            'mc_haproxy.password')
        ssl = _s['mc_ssl.settings']()
        proxy_settings = _s['mc_proxy.settings']()
        reverse_proxy_addresses = proxy_settings['reverse_proxy_addresses']
        data = {
            'reverse_proxy_addresses': reverse_proxy_addresses,
            'location': locs['conf_dir'] + '/haproxy',
            'config_dir': '/etc/haproxy',
            'rotate': _s['mc_logrotate.settings']()['days'],
            'config': 'haproxy.cfg',
            'user': 'haproxy',
            'use_rsyslog': False,
            'group': 'haproxy',
            'stats_enabled': True,
            'defaults': {'extra_opts': '', 'enabled': '1'},
            'crt_dirs': [ssl['ssl_dir'] + '/haproxy/certs', '{crt_dir}'],
            'crt_dir': ssl['config_dir'] + '/certs',
            'ssl': {
                  'frontend_bind_options': "crt {main_cert}",
                  'bind_options': "no-sslv3 no-tls-tickets",
                  'server_bind_options': "no-sslv3 no-tls-tickets",
                  'bind_ciphers': CIPHERS,
                  'server_bind_ciphers': CIPHERS},
            'main_cert': None,
            'backend_opts': {
                'http_strict': [
                    'balance roundrobin',
                    'option forwardfor',
                    'option http-keep-alive',
                    'option httpchk',
                    'option log-health-checks'],
                'https_strict': [
                    'balance roundrobin',
                    'option forwardfor',
                    'option http-keep-alive',
                    "http-request set-header X-Forwarded-Proto http   if !{ ssl_fc }",  #noqa
                    "http-request set-header X-Forwarded-Proto https  if  { ssl_fc }",  #noqa
                    'http-request set-header X-FORWARDED-SSL %[ssl_fc]',
                    'http-request set-header X-SSL %[ssl_fc]',
                    'option httpchk',
                    'option log-health-checks'],
                'http': [
                    'balance roundrobin',
                    'option forwardfor',
                    'option http-keep-alive',
                    "http-request set-header X-Forwarded-Proto http   if !{ ssl_fc }",  #noqa
                    "http-request set-header X-Forwarded-Proto https  if  { ssl_fc }",  #noqa
                    'option httpchk',
                    'option log-health-checks',
                    'http-check expect rstatus (2|3|4|5)[0-9][0-9]'],
                'https': [
                    'balance roundrobin',
                    'option forwardfor',
                    'option http-keep-alive',
                    "http-request set-header X-Forwarded-Proto http   if !{ ssl_fc }",  #noqa
                    "http-request set-header X-Forwarded-Proto https  if  { ssl_fc }",  #noqa
                    'http-request set-header X-FORWARDED-SSL %[ssl_fc]',
                    'http-request set-header X-SSL %[ssl_fc]',
                    'option httpchk',
                    'option log-health-checks',
                    'http-check expect rstatus (2|3|4|5)[0-9][0-9]'],
                'tcp': ['balance roundrobin'],
                'rabbitmq': [
                    "balance roundrobin",
                    "option tcp-check",
                    "option clitcpka",
                    "timeout client 3h"],
                'redis': [
                    'option tcp-check',
                    'tcp-check connect',
                    'tcp-check send PING\r\n',
                    'tcp-check expect string +PONG',
                    'tcp-check send info\ replication\r\n',
                    'tcp-check expect string role:master',
                    'tcp-check send QUIT\r\n',
                    'tcp-check expect string +OK'],
                'redis_auth': [
                    'option tcp-check',
                    'tcp-check connect',
                    'tcp-check send auth\ {password}\r\n',
                    'tcp-check send PING\r\n',
                    'tcp-check expect string +PONG',
                    'tcp-check send info\ replication\r\n',
                    'tcp-check expect string role:master',
                    'tcp-check send QUIT\r\n',
                    'tcp-check expect string +OK'],
            },
            'frontend_opts': {'http': [], 'https': []},
            'proxy_modes': {
                9200: 'http',
                80: 'http',
                443: 'https',
                5672: 'rabbitmq',
                6379: 'redis',
                6378: 'redis'
            },
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
                    'loglevel': 'warning',
                    'loghost': '127.0.0.1',
                    'nbproc': '',
                    'node': _g['id'],
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
                }
            },
            'letsencrypt_registrations': [
                {'letsencrypt': True},
            ],
            'registrations': OrderedDict(),
            'listeners': OrderedDict(),
            'backends': OrderedDict(),
            'frontends': OrderedDict(),
            'dispatchers': OrderedDict(),
            'letsencrypt': True,
            'no_ipv6': False,
        }
        data['listeners']['stats'] = {
            # set bind to null to deactivate the stats listener
            'bind': ":1936",
            'user': 'admin',
            'password': haproxy_password,
            'raw_opts': [
                "stats enable",
                "stats hide-version",
                "stats uri /",
                "stats refresh 5s",
                "stats realm haproxy\ statistics",
                    "stats auth {user}:{password}"]}
        # if we find in the Pillar some configured certificates, we will use
        # the first found certificate configured for that machine as
        # the default one.
        # Nevertheless, certicates are matched via SNI, the first
        # is always used in THE LAST RESORT
        # for i, cdata in six.iteritems(ssl['certificates']):
        #     cert = _s['mc_ssl.get_cert_infos'](i, sinfos=cdata[3])
        #     data['main_cert'] = cert['crt']
        data['main_cert'] = data['crt_dirs'][0]
        # complete some options after all options collects
        data['ssl']['frontend_bind_options'] = (
            replace_wk_opts(data['ssl']['frontend_bind_options']).format(**data)
        )
        data = _s['mc_utils.defaults'](PREFIX, data)
        fsslfbo = data['ssl']['frontend_bind_options']
        for crtdir in data['crt_dirs']:
            fsslfbo = ' crt '.join([fsslfbo, crtdir])
            data['ssl']['frontend_bind_options'] = fsslfbo
        data = make_registrations(haproxy=data)
        if not data['stats_enabled']:
            data['listeners'].pop('stats', None)
        return data
    return _settings()


def sanitize(key):
    if isinstance(key, list):
        key = '_'.join(key)
    key = key.replace('*', 'wildcard')
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
            if 'wildcard' in opt:
                pref += 1
        elif ' host_' in opt:
            pref += 50
            if 'wildcard' in opt:
                pref += 1
        if 'letsencrypt' in opt and (
            'acl ' in opt or
            'use_backend ' in opt
        ):
            pref = 90
        return '{0:04d}_{1}'.format(pref, opt)

    opts.sort(key=sort)
    return opts


def register_frontend(port,
                      mode=None,
                      hosts=None,
                      wildcards=None,
                      regexes=None,
                      haproxy=None,
                      letsencrypt=False,
                      ssh_proxy=None,
                      ssh_proxy_host=None,
                      ssh_proxy_port=None):
    proxied_port = port
    if ssh_proxy:
        proxied_port = port + 1
    if haproxy is None:
        haproxy = settings()
    sbind = '*:{0}'.format(port)
    if not haproxy['no_ipv6']:
        sbind = '{0},ipv6@:{1}'.format(sbind, port)
    if ssh_proxy_host is None:
        ssh_proxy_host = '127.0.0.1'
    if ssh_proxy_port is None:
        ssh_proxy_port = 22
    # if this is a TLS backend, append also the certificates
    # configured on the machine
    frontends = haproxy.setdefault('frontends', {})
    has = {'backend': False,
           'ssl': False,
           'main_cert': haproxy['main_cert'] is not None}
    if mode.startswith('https') or mode in ['tcps', 'ssl', 'tls']:
        has.update({'ssl': True})
        sbind = '{0} ssl {1}'.format(
           sbind,
           haproxy['ssl']['frontend_bind_options'])
    fbind = sbind
    if ssh_proxy:
        fbind = '127.0.0.1:{0}'.format(proxied_port)
    fr = get_frontend_name(mode, proxied_port)
    frontend = frontends.setdefault(fr, {})
    frontend.setdefault('bind', fbind)
    if ssh_proxy:
        ssshbckname = get_ssh_backend_proxy_name(ssh_proxy_host, ssh_proxy_port,
                                               k='ssh')
        hsshbckname = get_ssh_backend_proxy_name('127.0.0.1', proxied_port,
                                               k='https')
        sshfr = get_frontend_name('tcp', port)
        sshproxyfrontend = frontends.setdefault(sshfr, {})
        sshproxyfrontend.setdefault('bind', sbind)
        sshproxyfrontend["mode"] = "tcp"
        sshproxyfrontend["raw_opts"] = [
            a.format(http_proxy=hsshbckname, ssh_proxy=ssshbckname,
                     bracket='{', ebracket='}')
            for a in SSHPROXY]
    # normalise https -> http  & default proxy mode to TCP
    hmode = frontend.setdefault(
        'mode',
        mode.startswith('http') and 'http' or 'tcp')
    opts = frontend.setdefault(
        'raw_opts',
        haproxy['frontend_opts'].get(mode, [])[:])
    # if we are on http/https, use the LEVEL7 haproxy mode
    # TUPLE FOR ORDER IS IMPORTANT !
    # one_backend does not have any importanance, its sole purpose is
    # to factorize further code
    if not hmode.startswith('http'):
        aclmodes = (('default', ['one_backend']),)
    else:
        aclmodes = (('regex', regexes),
                    ('wildcard', wildcards),
                    ('host', hosts))
    for aclmode, chosts in aclmodes:
        if chosts:
            for match in chosts:
                has['backend'] = True
                bck_name = get_backend_name(
                    mode, port, **{aclmode: match})
                sane_match = sanitize(match)
                if any([
                    aclmode == 'wildcard' and match == '*',
                    aclmode == 'regex' and match == '.*'
                ]):
                    aclmode = 'default'
                cfgentries = {
                    'default': (
                        [],
                        ['default_backend {bck_name}']),
                    'regex': (
                        ['acl rgx_{sane_match}'
                         ' hdr_reg(host) -i {match[0]} url_reg'
                         ' -i {match[1]}',
                         'acl rgx_{sane_match}'
                         ' hdr_reg(host) -i {match[0]} url_reg'
                         ' -i {match[1]}:{port}'],
                        ['use_backend {bck_name} if rgx_{sane_match}']),
                    'wildcard': (
                        ['acl wc_{sane_match} hdr_end(host) -i {match}',
                         'acl wc_{sane_match} hdr_end(host) -i {match}:{port}',],
                        ['use_backend {bck_name} if wc_{sane_match}']),
                    'host': (
                        ['acl host_{sane_match} hdr(host) -i {match}:{port}',
                         'acl host_{sane_match} hdr(host) -i {match}'],
                        ['use_backend {bck_name} if host_{sane_match}']),
                }
                aclsdefs = cfgentries.get(aclmode, cfgentries['default'])
                for acls in aclsdefs:
                    for cfgentry in acls:
                        cfgentry = replace_wk_opts(cfgentry).format(
                            port=port,
                            match=(aclmode == 'wildcard' and
                                   match[2:] or
                                   match),
                            sane_match=sane_match,
                            bck_name=bck_name, bracket='{', ebracket='}')
                        if cfgentry not in opts:
                            opts.append(cfgentry)
    if letsencrypt and not frontend.get('letsencrypt_activated'):
        opts.append('acl letsencrypt'
                    ' path_beg /.well-known/acme-challenge/')
        if has['ssl']:
            letsb = 'bck_letsencrypts'
        else:
            letsb = 'bck_letsencrypt'
        opts.append(
            'use_backend {0} if letsencrypt'.format(letsb))
        frontend['letsencrypt_activated'] = True
    if has['ssl'] and not has['main_cert'] or not has['backend']:
        frontends.pop(fr, None)
    return haproxy


def register_servers_to_backends(port,
                                 ip,
                                 to_port=None,
                                 mode='tcp',
                                 user=None,
                                 password=None,
                                 wildcards=None,
                                 regexes=None,
                                 hosts=None,
                                 haproxy=None,
                                 ssl_terminated=None,
                                 http_fallback=None,
                                 letsencrypt=None,
                                 letsencrypt_host=None,
                                 letsencrypt_http_port=None,
                                 letsencrypt_tls_port=None,
                                 ssh_proxy=None,
                                 ssh_proxy_host=None,
                                 ssh_proxy_port=None):
    '''
    Register a specific minion as a backend server
    where haproxy will forward requests to
    '''
    if ssh_proxy:
        proxied_port = port + 1
    if letsencrypt_host is None:
        letsencrypt_host = '127.0.0.1'
    if letsencrypt_http_port is None:
        letsencrypt_http_port = 54080
    if letsencrypt_tls_port is None:
        letsencrypt_tls_port = 54443
    if ssh_proxy is None:
        ssh_proxy = False
    if ssh_proxy_host is None:
        ssh_proxy_host = '127.0.0.1'
    if ssh_proxy_port is None:
        ssh_proxy_port = 22
    # if we proxy some https? traffic, we rely on host to choose a backend
    # and in other cases, we assume to proxy to a TCPs? backend
    if ssl_terminated is None:
        ssl_terminated = False
    if http_fallback is None:
        http_fallback = True
    if haproxy is None:
        haproxy = settings()
    backends = haproxy.setdefault('backends', {})
    sane_ip = sanitize(ip)
    if mode == 'redis' and password is not None:
        mode = 'redis_auth'
    opts = haproxy['backend_opts'].get(
        mode,
        haproxy['backend_opts']['tcp'])
    if not to_port:
        to_port = port
    if mode.startswith('http'):
        hmode = 'http'
        #  we try first a backend over https, and if not present on http #}
        if mode.startswith('https'):
            slug = ' ssl verify none'
            if ssl_terminated:
                slug = ''
            servers = [{'name': 'srv_{0}_ssl'.format(sane_ip),
                        'bind': '{0}:{1}'.format(ip, to_port),
                        'opts': 'check weight 100 inter 1s{0}'.format(slug)}]
            if http_fallback:
                servers.insert(0, {'name': 'srv_{0}_clear'.format(sane_ip),
                                   'bind': '{0}:{1}'.format(ip, 80),
                                   'opts': 'check weight 50 inter 1s backup'})
        else:
            servers = [{'name': 'srv_{0}'.format(sane_ip),
                        'bind': '{0}:{1}'.format(ip, to_port),
                        'opts': 'check inter 1s'}]

    elif mode in [
        'rabbitmq', 'tcp', 'tcps',
        'ssl', 'tls', 'redis', 'redis_auth'
    ]:
        hmode = 'tcp'
        servers = [
               {'name': 'srv_{0}'.format(sane_ip),
                'bind': '{0}:{1}'.format(ip, to_port),
                'opts': 'check inter 1s'}]
    if not hmode.startswith('http'):
        aclmodes = (('default', ['one_backend']),)
    else:
        aclmodes = (('host', hosts),
                    ('regex', regexes),
                    ('wildcard', wildcards))
    if hmode.startswith('http') and letsencrypt:
        backends.update({
            'bck_letsencrypt': {
                'name': 'bck_letsencrypt',
                'servers': [{
                    'bind': '{0}:{1}'.format(
                        letsencrypt_host, letsencrypt_http_port),
                }]
            },
            'bck_letsencrypts': {
                'name': 'bck_letsencrypts',
                'servers': [{
                    'bind': '{0}:{1}'.format(
                        letsencrypt_host, letsencrypt_tls_port),
                }]
            }
        })
    if ssh_proxy:
        sshbckname = get_ssh_backend_proxy_name(ssh_proxy_host, ssh_proxy_port,
                                                k='ssh')
        hsshbckname = get_ssh_backend_proxy_name('127.0.0.1', proxied_port,
                                                 k='https')
        backends.update({
            hsshbckname: {
                'mode': 'tcp',
                'servers': [{'bind': '{0}:{1}'.format('127.0.0.1', proxied_port)}],
            },
            sshbckname: {
                'mode': 'tcp',
                'raw_opts': ['option tcplog', 'timeout server 2h'],
                'servers': [{
                    'bind': '{0}:{1}'.format(ssh_proxy_host, ssh_proxy_port)
                }],
            },
        })
    for aclmode, hosts in aclmodes:
        if hosts:
            for match in hosts:
                bck_name = get_backend_name(mode, port, **{aclmode: match})
                backend = backends.setdefault(bck_name, {})
                backend.setdefault('mode', hmode)
                bopts = backend.setdefault('raw_opts', [])
                for o in opts:
                    o = replace_wk_opts(o).format(
                        user=user, password=password,
                        bracket='{', ebracket='}')
                    if o not in bopts:
                        bopts.append(o)
                bopts = backend['raw_opts']
                bservers = backend.setdefault('servers', [])
                for server in servers:
                    if server not in bservers:
                        bservers.append(server)
    return haproxy


def make_registrations_(data, haproxy):
    '''
    The idea is to have somehow haproxies-as-a-service where minions register
    themselves up to the haproxies.

    - they can then ve evicted from the proxies
      if they have a grain setted 'haproxy_disable'
    - We search in the pillar and in the mine for any registered frontend
      for each frontend, we try to setup the underling frontend
      and backend objects
      for the haproxy configuration
    '''
    for payload in data:
        for port, fdata in payload.get(
            'frontends', DEFAULT_FRONTENDS
        ).items():
            port = int(port)
            hosts = payload.get('hosts', [])
            wildcards = payload.get('wildcards', [])
            regexes = payload.get('regexes', [])
            to_port = int(fdata.get('to_port', port))
            user = fdata.get('user', None)
            password = fdata.get('password', None)
            ssl_terminated = fdata.get('ssl_terminated', None)
            http_fallback = fdata.get('http_fallback', None)
            letsencrypt = fdata.get('letsencrypt', haproxy['letsencrypt'])
            ssh_proxy = payload.get('ssh_proxy', None)
            ssh_proxy_host = payload.get('ssh_proxy_host', None)
            ssh_proxy_port = payload.get('ssh_proxy_port', None)
            letsencrypt_host = fdata.get(
                'letsencrypt_host', None)
            letsencrypt_http_port = fdata.get(
                'letsencrypt_http_port', None)
            letsencrypt_tls_port = fdata.get(
                'letsencrypt_tls_port', None)
            mode = fdata.get('mode',
                             haproxy['proxy_modes'].get(port, 'tcp'))
            register_frontend(port, mode, hosts=hosts,
                              wildcards=wildcards,
                              regexes=regexes,
                              haproxy=haproxy,
                              letsencrypt=letsencrypt,
                              ssh_proxy=ssh_proxy,
                              ssh_proxy_host=ssh_proxy_host,
                              ssh_proxy_port=ssh_proxy_port)
            if ssh_proxy:
                payload.setdefault(
                    'ip', [ssh_proxy_host or '127.0.0.1'])
            if not isinstance(payload['ip'], list):
                payload['ip'] = payload['ip']
            register_servers_to_backends(
                port=port, ip=payload['ip'],
                to_port=to_port, mode=mode,
                user=user, password=password,
                hosts=hosts, wildcards=wildcards,
                regexes=regexes,
                ssl_terminated=ssl_terminated,
                http_fallback=http_fallback,
                haproxy=haproxy,
                letsencrypt=letsencrypt,
                letsencrypt_host=letsencrypt_host,
                letsencrypt_http_port=letsencrypt_http_port,
                letsencrypt_tls_port=letsencrypt_tls_port,
                ssh_proxy=ssh_proxy,
                ssh_proxy_host=ssh_proxy_host,
                ssh_proxy_port=ssh_proxy_port
            )
    return haproxy


def make_registrations(data=None, haproxy=None):
    if data is None:
        data = __pillar__
    if haproxy is None:
        haproxy = settings()
    for k in [
        a for a in data
        if a.startswith(registration_prefix)
    ]:
        haproxy = make_registrations_(data[k], haproxy)
    haproxy = make_registrations_(haproxy["registrations"].values(), haproxy)
    return haproxy
# vim:set et sts=4 ts=4 tw=0:
