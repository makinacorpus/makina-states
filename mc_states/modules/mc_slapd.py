# -*- coding: utf-8 -*-
'''

.. _module_mc_slapd:

mc_slapd / slapd registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_slapd

'''
# Import python libs
import logging
import mc_states.utils

__name = 'slapd'

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
    slapd registry

    is_reverse_proxied
        is slapd itself is reverse proxified (true in cloudcontroller mode)
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
        raw setting for slapd (see slapd documentation)
    open_file_cache_valid
        raw setting for slapd (see slapd documentation)
    open_file_cache_min_uses
        raw setting for slapd (see slapd documentation)
    open_file_cache_errors
        raw setting for slapd (see slapd documentation)
    epoll
        do we use epoll (true on linux)
    default_type
        raw setting for slapd (see slapd documentation)
    worker_processes
        nb workers, default to nb of cpus
    worker_connections
        raw setting for slapd (see slapd documentation)
    multi_accept
        raw setting for slapd (see slapd documentation)
    user
        slapd user
    server_names_hash_bucket_size
        raw setting for slapd (see slapd documentation)
    loglevel
        slapd error loglevel (crit)
    logdir
        slapd logdir (/var/log/slapd)
    access_log
        '{logdir}/access.log
    sendfile
        raw setting for slapd (see slapd documentation)
    tcp_nodelay
        raw setting for slapd (see slapd documentation)
    tcp_nopush
        raw setting for slapd (see slapd documentation)
    reset_timedout_connection
        raw setting for slapd (see slapd documentation)
    client_body_timeout
        raw setting for slapd (see slapd documentation)
    send_timeout
        raw setting for slapd (see slapd documentation)
    keepalive_requests
        raw setting for slapd (see slapd documentation)
    keepalive_timeout
        raw setting for slapd (see slapd documentation)
    types_hash_max_size
        raw setting for slapd (see slapd documentation)
    server_tokens
        raw setting for slapd (see slapd documentation)
    server_name_in_redirect
        raw setting for slapd (see slapd documentation)
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
        /usr/share/doc/slapd
    doc_root
        /usr/share/slapd/www
    vhost_default_template
       salt://makina-states/files/etc/slapd/sites-available/vhost.conf
    vhost_wrapper_template
        Default template for vhosts
        salt://makina-states/files/etc/slapd/sites-available/vhost.conf
    vhost_default_content
        Default content template for the DEFAULT DOMAIN vhost
        salt://makina-states/files/etc/slapd/sites-available/default.conf'
    vhost_top_template
       default template to include in vhost top
       salt://makina-states/files/etc/slapd/sites-available/vhost.top.conf,
    vhost_content_template
       default template for vhost content
       salt://makina-states/files/etc/slapd/sites-available/vhost.content.conf
    virtualhosts
        Mapping containing all defined virtualhosts
    rotate
        days to rotate log
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        slapdData = __salt__['mc_utils.defaults'](
            'makina-states.services.dns.slapd', {
                'slapd_directory': "/etc/ldap/slapd.d",
                'extra_dirs': [
                    '/etc/ldap',
                    '/var/lib/ldap',
                ],
                'pkgs': ['ldap-utils', 'slapd'],
                'user': 'openldap',
                'group': 'openldap',
                'SLAPD_CONF': '/etc/slapd.d',
                'SLAPD_PIDFILE': '',
                'SLAPD_SERVICES': 'ldaps:/// ldap:/// ldapi:///',
                'SLAPD_NO_START': "",
                'SLAPD_SENTINEL_FILE': '/etc/ldap/noslapd',
                'SLAPD_OPTIONS': '',
                'config_root_dn': 'cn=admin,cn=config',
                'config_root_pw': 's3cr3t',
                'dn': 'dc=sample,dc=com',
                'init_ldif': 'salt://makina-states/files/etc/ldap/init.ldif',
                'mode': 'bare',
                'root_dn': None,
                'root_pw': None,
                'loglevel': 'sync',
                'syncprov': True,
                'syncrepl': None,
                'tls_cacert': None,
                'tls_cert': None,
                'tls_key': None,
            }
        )
        return slapdData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
