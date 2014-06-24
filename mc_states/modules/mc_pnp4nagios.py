# -*- coding: utf-8 -*-
'''
.. _module_mc_pnp4nagios:

mc_pnp4nagios / pnp4nagios functions
============================================

'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import copy
import mc_states.utils

import hmac
import hashlib

__name = 'pnp4nagios'

log = logging.getLogger(__name__)


def settings():
    '''
    pnp4nagios settings

    location
        installation directory

    package
        list of packages to install icinga-web
    configuration_directory
        directory where configuration files are located
                
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locs = __salt__['mc_locations.settings']()

        pnp4nagios_reg = __salt__[
            'mc_macros.get_local_registry'](
                'pnp4nagios', registry_format='pack')

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.pnp4nagios', {
                'package': ['pnp4nagios-bin', 'pnp4nagios-web'],
                'configuration_directory': locs['conf_dir']+"/pnp4nagios",
                'nginx': {
                    'domain': "pnp4nagios.localhost",
                    'doc_root': "/usr/share/pnp4nagios/html/",
                    'vh_content_source': "salt://makina-states/files/etc/nginx/sites-available/pnp4nagios.content.conf",
                    'vh_top_source': "salt://makina-states/files/etc/nginx/sites-available/pnp4nagios.top.conf",
                    'pnp4nagios': {
                        'web_directory': "/pnp4nagios",
                        'fastcgi_pass': "unix:/var/spool/www/pnp4nagios_localhost.fpm.sock",
                        'realm': "Authentication",
                        'htpasswd_file': "/etc/icinga/htpasswd.users",
                        'htdocs_dir': "/usr/share/icinga/htdocs/",
                    },
                    'icinga_cgi': {
                        'enabled': True, # icinga cgi will not be configured. It is done in services.monitoring.icinga
                        'web_directory': "/icinga",
                        'realm': "Authentication",
                        'htpasswd_file': "/etc/icinga/htpasswd.users",
                        'htdocs_dir': "/usr/share/icinga/htdocs/",
                        'images_dir': "/usr/share/icinga/htdocs/images/$1",
                        'styles_dir': "/usr/share/icinga/htdocs/stylesheets/$1",
                        'cgi_dir': "/usr/lib/cgi-bin/",
                        'uwsgi_pass': "127.0.0.1:3030",
                    },
                },
                'phpfpm': {
                    'open_basedir': "/usr/bin/rrdtool:/etc/pnp4nagios/:/usr/share/php/kohana2/system/:/usr/share/php/kohana2/system/config/:/var/lib/pnp4nagios/perfdata/",
                    'doc_root': '/usr/share/pnp4nagios/',
                    #'session_save_path': '/var/lib/php5',
                    'session_auto_start': 0,
                    'extensions_packages': ['php-gettext', 'php-net-socket', 'php-pear', 'php5-sqlite'],
                },
                'npcd_cfg': {
                    'user': "nagios",
                    'group': "nagios",
                    'log_type': "syslog",
                    'log_file': "/var/log/pnp4nagios/npcd.log",
                    'max_logfile_size': 10485760,
                    'log_level': 2,
                    'perfdata_spool_dir': "/var/lib/icinga/spool/",
                    'perfdata_file_run_cmd': "/usr/lib/pnp4nagios/libexec/process_perfdata.pl",
                    'perfdata_file_run_cmd_args': "-b",
                    'identify_npcd': 1,
                    'npcd_max_threads': 5,
                    'sleep_time': 15,
                    'load_threshold': 0.0,
                    'pid_file': "/var/run/npcd.pid",
                    'perfdata_file': "/var/lib/icinga/perfdata.dump",
                    'perfdata_spool_filename': "perfdata",
                    'perfdata_file_processing_interval': 15,
                },
        })

        __salt__['mc_macros.update_local_registry'](
            'pnp4nagios', pnp4nagios_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
