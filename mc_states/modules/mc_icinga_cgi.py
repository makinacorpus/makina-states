# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga_cgi:

mc_icinga_cgi / icinga_cgi functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

import hmac
import hashlib

__name = 'icinga_cgi'

log = logging.getLogger(__name__)


def settings():
    '''
    icinga_cgi settings

    location
        installation directory

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        icinga_cgi_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga_cgi', registry_format='pack')
        locs = __salt__['mc_locations.settings']()

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga_cgi', {
                'package': ['icinga-cgi'],
                'configuration_directory': locs['conf_dir']+"/icinga-web",
                'nginx': {
                    'virtualhost': "icinga-cgi.localhost",
                    'doc_root': "/usr/share/icinga-web/pub/",
                    'vh_content_source': "salt://makina-states/files/etc/icinga-cgi/nginx.conf",
                    'vh_top_source': "salt://makina-states/files/etc/icinga-cgi/nginx.top.conf",
                },
                'uwsgi': {
                    'name': "icinga",
                    'config_file': "salt://makina-states/files/etc/icinga-cgi/uwsgi.conf",
                    'enabled': True,
                    'config_data': {
                        'plugins': "cgi",
                        'async': 20,
                        'socket': "127.0.0.1:3030",
                        'cgi': "/usr/lib/cgi-bin/icinga",
                        'cgi_allowed_ext': ".cgi",
                    },
                },
        })

        __salt__['mc_macros.update_local_registry'](
            'icinga_cgi', icinga_cgi_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
