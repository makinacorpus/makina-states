# -*- coding: utf-8 -*-
'''
.. _module_mc_uwsgi:

mc_uwsgi / uwsgi functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

import hmac
import hashlib

__name = 'uwsgi'

log = logging.getLogger(__name__)


def settings():
    '''
    uwsgi settings

    location
        installation directory

    run_at_startup
        "yes" or "no"
    verbose
        "yes" or "no"
    print_confnames_in_initd_script_output
        "yes" or "no"
    inherited_config
        inherited config to fill missing uwsgi parameters
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        uwsgi_reg = __salt__[
            'mc_macros.get_local_registry'](
                'uwsgi', registry_format='pack')
        locs = __salt__['mc_locations.settings']()

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.cgi.uwsgi', {
                'package': ['uwsgi', 'uwsgi-core'],
                'configuration_directory': locs['conf_dir']+"/uwsgi",
                'default_uwsgi': {
                    'run_at_startup': "yes",
                    'verbose': "yes",
                    'print_confnames_in_initd_script_output': "no",
                    'inherited_config': "/usr/share/uwsgi/conf/default.ini",
                },
        })

        __salt__['mc_macros.update_local_registry'](
            'uwsgi', uwsgi_reg,
            registry_format='pack')
        return data
    return _settings()

def dump():
    return mc_states.utils.dump(__salt__,__name)

#
