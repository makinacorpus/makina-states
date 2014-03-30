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


def settings():
    '''
    NGINX registry

    package
        TBD
    service
        TBD
    basedir
        TBD
    vhostdir
        TBD
    confdir
        TBD
    logdir
        TBD
    wwwdir
        TBD
    virtualhosts
        TDB
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        ry = __salt__['mc_nodetypes.registry']()
        locations = localsettings['locations']
        nbcpus = __grains__.get('num_cpus', '4')
        epoll = False
        if 'linux' in __grains__.get('kernel', '').lower:
            epoll = True

        ulimit = "200000"
        nginxData = __salt__['mc_utils.defaults'](
            'makina-states.services.http.nginx',
            __salt__['grains.filter_by']({
                'Debian': {
                },
            },
                merge=__salt__['grains.filter_by']({
                    'dev': {
                    },
                    'prod': {
                    },
                },
                    merge={
                        'ulimit': ulimit,
                        'open_file_cache': 'max=200000 inactive=5m',
                        'open_file_cache_valid': '6m',
                        'open_file_cache_min_uses': '2',
                        'open_file_cache_errors': 'on',
                        'epoll': epoll,
                        'default_domain': 'example.com',
                        'default_type': 'application/octet-stream',
                        'worker_processes': nbcpus,
                        'worker_connections': '1024',
                        'multi_accept': True,
                        'user': 'www-data',
                        'server_names_hash_bucket_size': '',
                        'logdir': '/var/log/nginx',
                        'access_log': '{logdir}/access.log',
                        'sendfile': True,
                        'tcp_nodelay': True,
                        'tcp_nopush': True,
                        'reset_timedout_connection': 'on',
                        'client_body_timeout': '10',
                        'send_timeout': '2',
                        'keepalive_request': '100000',
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
                        'docdir': '/sr/share/doc/nginx',
                        'docroot': '/sr/share/nginx/html',
                        'service': 'nginx',
                        'basedir': locations['conf_dir'] + '/nginx',
                        'confdir': locations['conf_dir'] + '/nginx/conf.d',
                        'logdir': locations['var_log_dir'] + '/nginx',
                        'wwwdir': locations['srv_dir'] + '/www'
                        'vhost_wrapper_template': (
                            'salt://makina-states/files/'
                            'etc/nginx/sites-available/vhost.conf'),
                        'vhost_body_template': '',
                        'allowed_host': ['localhost', '127.0.0.1', '::1'],
                    },
                    grain='default_env',
                    default='dev'
                ),
                grain='os_family',
                default='Debian',
            )
        )
        return nginxData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
