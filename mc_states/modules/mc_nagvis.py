# -*- coding: utf-8 -*-
'''
.. _module_mc_nagvis:

mc_nagvis / nagvis functions
============================================

'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

import hmac
import hashlib

__name = 'nagvis'

log = logging.getLogger(__name__)


def settings():
    '''
    nagvis settings

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

        nagvis_reg = __salt__[
            'mc_macros.get_local_registry'](
                'nagvis', registry_format='pack')

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.nagvis', {
                'package': ['nagvis'],
                'configuration_directory': locs['conf_dir']+"/nagvis",
                'nginx': {
                    'domain': "nagvis.localhost",
                    'doc_root': "/usr/share/nagvis/www/",
                    'vh_content_source': "salt://makina-states/files/etc/nginx/sites-available/nagvis.content.conf",
                    'vh_top_source': "salt://makina-states/files/etc/nginx/sites-available/nagvis.top.conf",
                    'nagvis': {
                        'web_directory': "/nagvis",
                        'fastcgi_pass': "unix:/var/spool/www/nagvis_localhost.fpm.sock",
                    },
                },
                'phpfpm': {
                    'open_basedir': "/usr/share/php/php-gettext/:/etc/nagvis/:/var/lib/nagvis/:/var/cache/nagvis/",
                    'doc_root': '/usr/share/nagvis/',
                    #'session_save_path': '/var/lib/php5',
                    'session_auto_start': 0,
                },
        })

        __salt__['mc_macros.update_local_registry'](
            'nagvis', nagvis_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
