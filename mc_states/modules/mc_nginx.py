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
import mc_states.utils

__name = 'nginx'

log = logging.getLogger(__name__)


def is_reverse_proxied():
    return __salt__['mc_cloud.is_vm']()


def settings():
    '''
    NGINX registry

    is_reverse_proxied
        is nginx itself is reverse proxified (true in cloudcontroller mode)
    reverse_proxy_addresses
        authorized reverse proxied addresses
    use_real_ip
        do we use real ip module
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
    user
        nginx user
    server_names_hash_bucket_size
        raw setting for nginx (see nginx documentation)
    loglevel
        nginx error loglevel (crit)
    logdir
        nginx logdir (/var/log/nginx)
    access_log
        '{logdir}/access.log
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
        do we redirect server aliases to /
    port
        http port (80)
    sshl_port
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
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        locations = localsettings['locations']
        nbcpus = __grains__.get('num_cpus', '4')
        epoll = False
        if 'linux' in __grains__.get('kernel', '').lower():
            epoll = True
        ulimit = "65536"
        is_rp = is_reverse_proxied()
        reverse_proxy_addresses = []
        if is_rp:
            gw = grains.get('makina.default_route', {}).get('gateway').strip()
            if gw and gw not in reverse_proxy_addresses:
                reverse_proxy_addresses.append(gw)

        logformat = '$remote_addr - $remote_user [$time_local]  '
        logformat += '"$request" $status $bytes_sent "$http_referer" '
        logformat += '"$http_user_agent" "$gzip_ratio"'
        logformats = {
            'custom_combined': logformat
        }

        nginxData = __salt__['mc_utils.defaults'](
            'makina-states.services.http.nginx', {
                'is_reverse_proxied': is_rp,
                'reverse_proxy_addresses': reverse_proxy_addresses,
                'use_real_ip': True,
                'real_ip_header': 'X-Forwarded-For',
                'logformat': 'custom_combined',
                'logformats': logformats,
                'allowed_hosts': [],
                'ulimit': ulimit,
                'open_file_cache': 'max=200000 inactive=5m',
                'open_file_cache_valid': '6m',
                'open_file_cache_min_uses': '2',
                'open_file_cache_errors': 'on',
                'epoll': epoll,
                'default_type': 'application/octet-stream',
                'worker_processes': nbcpus,
                'worker_connections': '1024',
                'multi_accept': True,
                'user': 'www-data',
                'server_names_hash_bucket_size': '64',
                'loglevel': 'crit',
                'logdir': '/var/log/nginx',
                'access_log': '{logdir}/access.log',
                'sendfile': True,
                'tcp_nodelay': True,
                'tcp_nopush': True,
                'reset_timedout_connection': 'on',
                'client_body_timeout': '10',
                'send_timeout': '2',
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
                'sshl_port': '443',
                'default_activation': True,
                'package': 'nginx',
                'docdir': '/usr/share/doc/nginx',
                'doc_root': '/usr/share/nginx/www',
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
        return nginxData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
