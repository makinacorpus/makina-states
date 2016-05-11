# -*- coding: utf-8 -*-
'''

.. _module_mc_nginx:

mc_nginx / nginx registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_nginx

'''
# Import python libs
import logging
import copy
import mc_states.api
from salt.utils.pycrypto import secure_password

__name = 'nginx'

log = logging.getLogger(__name__)


def is_reverse_proxied():
    is_vm = False
    try:
        with open('/etc/mastersalt/makina-states/cloud.yaml') as fic:
            is_vm = 'is.vm' in fic.read()
    except Exception:
        pass
    return __salt__['mc_cloud.is_vm']() or is_vm


def settings():
    '''
    nginx registry

    is_reverse_proxied
        is nginx itself is reverse proxified (true in cloudcontroller mode)
    reverse_proxy_addresses
        authorized reverse proxied addresses
    use_real_ip
        do we use real ip module
    use_naxsi
        configure & use naxsi
    use_naxsi_secrules
        use sec rules in naxsi
    naxsi_ui_pass
        pass for naxsi leaning mode ui
    naxsi_ui_host
        host for naxsi leaning mode ui
    naxsi_ui_intercept_port
        intercept_port for naxsi leaning mode ui
    naxsi_ui_extract_port
        extract port for naxsi leaning mode ui
    use_naxsi_learning
        put naxsi in learning mode
    naxsi_denied_url
        uri for naxsi refused cnx
    real_ip_header
        which http header to search for real ip
    reverse_proxy_addresses
        control real ip addresses (list of values).
        Default to network gateway (in cloud controllermode, haproxy is there)
    logformat
        default log format
    logformats
        custom log formats mapping
    allowed_hosts
        default allowed hosts
    ulimit
        default ulimit for the workers
    open_file_cache
        raw setting for nginx (see nginx documentation)
    open_file_cache_valid
        raw setting for nginx (see nginx documentation)
    open_file_cache_min_uses
        raw setting for nginx (see nginx documentation)
    open_file_cache_errors
        raw setting for nginx (see nginx documentation)
    epoll
        do we use epoll (true on linux)
    default_type
        raw setting for nginx (see nginx documentation)
    worker_processes
        nb workers, default to nb of cpus
    worker_connections
        raw setting for nginx (see nginx documentation)
    multi_accept
        raw setting for nginx (see nginx documentation)
    ssl_cacert
        ssl_cacert content if any
    ssl_redirect
        unconditionnal www -> ssl redirect
    ssl_protocols
        SSLv3 TLSv1 TLSv1.1 TLSv1.2
    ssl_cacert_first
            False
    ssl_session_cache
        shared:SSL:10m
    ssl_session_timeout
        10m
    ssl_cipher
        IGH:!aNULL:!MD5
    user
        nginx user
    group
        nginx group
    server_names_hash_bucket_size
        raw setting for nginx (see nginx documentation)
    loglevel
        nginx error loglevel (crit)
    logdir
        nginx logdir (/var/log/nginx)
    access_log
        '{logdir}/access.log
    ldap_cache:
        use ldap auth plugin cache (True)
    sendfile
        raw setting for nginx (see nginx documentation)
    tcp_nodelay
        raw setting for nginx (see nginx documentation)
    tcp_nopush
        raw setting for nginx (see nginx documentation)
    reset_timedout_connection
        raw setting for nginx (see nginx documentation)
    client_body_timeout
        raw setting for nginx (see nginx documentation)
    send_timeout
        raw setting for nginx (see nginx documentation)
    keepalive_requests
        raw setting for nginx (see nginx documentation)
    keepalive_timeout
        raw setting for nginx (see nginx documentation)
    types_hash_max_size
        raw setting for nginx (see nginx documentation)
    server_tokens
        raw setting for nginx (see nginx documentation)
    server_name_in_redirect
        raw setting for nginx (see nginx documentation)
    error_log
        '{logdir}/error.log'
    gzip
        enabling gzip
    redirect_aliases
        do we redirect server aliases to main domain
    port
        http port (80)
    ssh_port
        https port (443)
    default_domains
        default domains to server ['localhost']
    docdir
        /usr/share/doc/nginx
    doc_root
        /usr/share/nginx/www
    vhost_default_template
       salt://makina-states/files/etc/nginx/sites-available/vhost.conf
    vhost_wrapper_template
        Default template for vhosts
        salt://makina-states/files/etc/nginx/sites-available/vhost.conf
    vhost_default_content
        Default content template for the DEFAULT DOMAIN vhost
        salt://makina-states/files/etc/nginx/sites-available/default.conf'
    vhost_top_template
       default template to include in vhost top
       salt://makina-states/files/etc/nginx/sites-available/vhost.top.conf,
    vhost_content_template
       default template for vhost content
       salt://makina-states/files/etc/nginx/sites-available/vhost.content.conf
    virtualhosts
        Mapping containing all defined virtualhosts
    rotate
        days to rotate log
    default_vhost
        set to false to disable default vhost
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _g = __grains__
        local_conf = __salt__['mc_macros.get_local_registry'](
            'nginx', registry_format='pack')
        naxsi_ui_pass = local_conf.setdefault('naxsi_ui_pass',
                                              secure_password(32))
        locations = __salt__['mc_locations.settings']()
        nbcpus = _g.get('num_cpus', '4')
        epoll = False
        if 'linux' in _g.get('kernel', '').lower():
            epoll = True
        ulimit = "65536"
        is_rp = is_reverse_proxied()
        reverse_proxy_addresses = []
        if is_rp:
            gw = _g.get('makina.default_route', {}).get('gateway', '').strip()
            if gw and gw not in reverse_proxy_addresses:
                reverse_proxy_addresses.append(gw)

        logformat = '$remote_addr - $remote_user [$time_local]  '
        logformat += '"$request" $status $bytes_sent "$http_referer" '
        logformat += '"$http_user_agent" "$gzip_ratio"'
        logformats = {
            'custom_combined': logformat
        }
        no_daemon = False
        if __salt__['mc_nodetypes.is_docker']():
            no_daemon = True
        www_reg = __salt__['mc_www.settings']()

        # fix virtualbox bad support of sendfile
        sendfile = True
        if __grains__.get('virtual', None) == 'VirtualBox':
            sendfile = False

        nginxData = __salt__['mc_utils.defaults'](
            'makina-states.services.http.nginx', {
                'rotate': '365',
                'real_ip_recursive': 'on',
                'no_daemon': no_daemon,
                'is_reverse_proxied': is_rp,
                'reverse_proxy_addresses': reverse_proxy_addresses,
                'default_vhost': True,
                'use_real_ip': True,
                'use_naxsi': False,
                'use_naxsi_secrules': True,
                'naxsi_ui_user': 'naxsi_web',
                'proxy_headers_hash_max_size': '1024',
                'proxy_headers_hash_bucket_size': '128',
                'naxsi_ui_pass': naxsi_ui_pass,
                'naxsi_ui_host': '127.0.01',
                'naxsi_ui_intercept_port': '18080',
                'naxsi_ui_extract_port': '18081',
                'use_naxsi_learning': True,
                'naxsi_denied_url': "/RequestDenied",
                'real_ip_header': 'X-Forwarded-For',
                'logformat': 'custom_combined',
                'logformats': logformats,
                'v6': False,
                'allowed_hosts': [],
                'ulimit': ulimit,
                'client_max_body_size': www_reg[
                    'upload_max_filesize'],
                'open_file_cache': 'max=200000 inactive=5m',
                'open_file_cache_valid': '6m',
                'configs': {
                    '/etc/nginx/drupal_cron_allowed_hosts.conf': {},
                    '/etc/nginx/fastcgi_fpm_symfony.conf': {},
                    '/etc/nginx/fastcgi_fpm_drupal.conf': {},
                    '/etc/nginx/fastcgi_fpm_drupal_params.conf': {},
                    '/etc/nginx/fastcgi_fpm_drupal_private_files.conf': {},
                    '/etc/nginx/fastcgi_microcache_zone.conf': {},
                    '/etc/nginx/fastcgi_params': {},
                    '/etc/nginx/fastcgi_params_common': {},
                    '/etc/nginx/koi-utf': {},
                    '/etc/nginx/koi-win': {},
                    '/etc/nginx/map_cache.conf': {},
                    '/etc/nginx/microcache_fcgi.conf': {},
                    '/etc/nginx/mime.types': {},
                    '/etc/nginx/naxsi_core.rules': {},
                    '/etc/nginx/nginx.conf': {},
                    '/etc/nginx/php_fpm_status_vhost.conf': {},
                    '/etc/nginx/php_fpm_status_allowed_hosts.conf': {},
                    '/etc/nginx/proxy_params': {},
                    '/etc/nginx/scgi_params': {},
                    '/etc/nginx/status_allowed_hosts.conf': {},
                    '/etc/nginx/status_vhost.conf': {},
                    '/etc/nginx/uwsgi_params': {},
                    '/etc/nginx/win-utf': {},
                    "/etc/logrotate.d/nginx": {},
                    '/etc/default/nginx': {},
                    '/etc/init.d/nginx': {"mode": "755"},
                    '/etc/systemd/system/overrides.d/nginx.conf': {"mode": "644"},
                },
                'open_file_cache_min_uses': '2',
                'open_file_cache_errors': 'off',
                'epoll': epoll,
                'default_type': 'application/octet-stream',
                'worker_processes': nbcpus,
                'worker_connections': '1024',
                'multi_accept': True,
                'user': 'www-data',
                'group': 'www-data',
                'server_names_hash_bucket_size': '64',
                'loglevel': 'crit',
                'ldap_cache': True,
                'logdir': '/var/log/nginx',
                'access_log': '{logdir}/access.log',
                'sendfile': sendfile,
                'tcp_nodelay': True,
                'tcp_nopush': True,
                'reset_timedout_connection': 'on',
                'client_body_timeout': 4 * 60 * 60,
                'send_timeout': '60s',
                'keepalive_requests': '100000',
                'keepalive_timeout': '30',
                'types_hash_max_size': '2048',
                'server_tokens': False,
                'server_name_in_redirect': False,
                'error_log':  '{logdir}/error.log',
                'virtualhosts': {},
                'gzip': True,
                'redirect_aliases': True,
                'port': '80',
                'default_domains': ['localhost'],
                'ssl_port': '443',
                'ssl_protocols': 'TLSv1 TLSv1.1 TLSv1.2',
                'ssl_redirect': False,
                'ssl_cacert_first': False,
                'ssl_session_cache': 'shared:SSL:10m',
                'ssl_session_timeout': '10m',
                'ssl_ciphers': 'EECDH+AESGCM:EDH+AESGCM:ECDHE-RSA-AES128-GCM-SHA256:AES256+EECDH:DHE-RSA-AES128-GCM-SHA256:AES256+EDH:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256:AES256-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4',
                'default_activation': True,
                'package': 'nginx',
                'docdir': '/usr/share/doc/nginx',
                'doc_root': www_reg['doc_root'],
                'service': 'nginx',
                'basedir': locations['conf_dir'] + '/nginx',
                'confdir': locations['conf_dir'] + '/nginx/conf.d',
                'logdir': locations['var_log_dir'] + '/nginx',
                'wwwdir': locations['srv_dir'] + '/www',
                'vhost_default_template': (
                    'salt://makina-states/files/'
                    'etc/nginx/sites-available/vhost.conf'),
                'vhost_wrapper_template': (
                    'salt://makina-states/files/'
                    'etc/nginx/sites-available/vhost.conf'),
                'vhost_default_content': (
                    'salt://makina-states/files/'
                    'etc/nginx/sites-available/default.conf'),
                'vhost_top_template': (
                    'salt://makina-states/files/'
                    'etc/nginx/sites-available/vhost.top.conf'),
                'vhost_content_template': (
                    'salt://makina-states/files/'
                    'etc/nginx/sites-available/vhost.content.conf'),
            }
        )
        __salt__['mc_macros.update_local_registry'](
            'nginx', local_conf, registry_format='pack')
        return nginxData
    return _settings()


def vhost_settings(domain, doc_root, **kwargs):
    '''
    Settings for the nginx macro

    ssl_cert
        ssl_cert content if any
    ssl_key
        ssl_key content if any

    '''
    nginxSettings = copy.deepcopy(__salt__['mc_nginx.settings']())
    # retro compat
    extra = kwargs.pop('extra', {})
    kwargs.update(extra)
    kwargs.setdefault('small_name',
                      domain.replace('.', '_').replace('-', '_').replace('*', 'star'))
    vhost_basename = kwargs.setdefault('vhost_basename', domain)
    kwargs.setdefault(
        'vhost_available_file',
        nginxSettings['basedir'] + "/sites-available/" + vhost_basename + ".conf")
    kwargs.setdefault(
        'vhost_content_file',
        (nginxSettings['basedir'] + "/sites-available/" +
         vhost_basename + ".content.conf"))
    kwargs.setdefault(
        'vhost_top_file',
        nginxSettings['basedir'] + "/sites-available/" + vhost_basename + ".top.conf")
    kwargs.setdefault('with_include_sls_statement', False)
    kwargs.setdefault('redirect_aliases', True)
    kwargs.setdefault('force_reload', True)
    kwargs.setdefault('force_restart', False)
    kwargs.setdefault('domain', domain)
    kwargs.setdefault('active', nginxSettings['default_activation'])
    kwargs.setdefault('server_name', kwargs['domain'])
    kwargs.setdefault('default_server', False)
    kwargs.setdefault('ssl_ciphers', nginxSettings['ssl_ciphers'])
    kwargs.setdefault('ssl_port', nginxSettings['ssl_port'])
    kwargs.setdefault('ssl_protocols', nginxSettings['ssl_protocols'])
    kwargs.setdefault('ssl_redirect', nginxSettings['ssl_redirect'])
    kwargs.setdefault('ssl_cacert_first', nginxSettings['ssl_cacert_first'])
    kwargs.setdefault('ssl_session_cache', nginxSettings['ssl_session_cache'])
    kwargs.setdefault('ssl_session_timeout',
                      nginxSettings['ssl_session_timeout'])
    kwargs.setdefault('server_aliases', None)
    kwargs.setdefault('doc_root', doc_root)
    kwargs.setdefault('vh_top_source', nginxSettings['vhost_top_template'])
    kwargs.setdefault('vh_template_source',
                      nginxSettings['vhost_wrapper_template'])
    kwargs.setdefault('vh_content_source',
                      nginxSettings['vhost_content_template'])
    nginxSettings = __salt__['mc_utils.dictupdate'](nginxSettings, kwargs)
    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
    nginxSettings['data'] = copy.deepcopy(nginxSettings)
    nginxSettings['data']['extra'] = copy.deepcopy(nginxSettings)
    nginxSettings['extra'] = copy.deepcopy(nginxSettings)

    # to disable ssl, ssl_cert must be a empty string
    if nginxSettings.get('ssl_cert', None) != '':
        ssldomain = domain
        if ssldomain in ['default']:
            ssldomain = _g['fqdn']
        lcert, lkey, lchain = __salt__[
            'mc_ssl.get_configured_cert'](ssldomain, gen=True)
        if not nginxSettings.get('ssl_cert'):
            nginxSettings['ssl_cert'] = lcert + lchain
        if not nginxSettings.get('ssl_key'):
            nginxSettings['ssl_key'] = lcert + lchain + lkey
        if not nginxSettings.get('ssl_bundle'):
            nginxSettings['ssl_bundle'] = ''
        certs = ['ssl_cert']
        if nginxSettings.get('ssl_cacert', ''):
            if nginxSettings['ssl_cacert_first']:
                certs.insert(0, 'ssl_cacert')
            else:
                certs.append('ssl_cacert')
        for cert in certs:
            nginxSettings['ssl_bundle'] += nginxSettings[cert]
            if not nginxSettings['ssl_bundle'].endswith('\n'):
                nginxSettings['ssl_bundle'] += '\n'
        for k in ['ssl_bundle', 'ssl_key', 'ssl_cert', 'ssl_cacert']:
            kpath = k + '_path'
            if not nginxSettings.get(kpath):
                nginxSettings.setdefault(
                    kpath,
                    "/etc/ssl/nginx/{0}_{1}.pem".format(ssldomain, k))
    return nginxSettings
