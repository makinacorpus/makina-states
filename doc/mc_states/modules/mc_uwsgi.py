# -*- coding: utf-8 -*-
'''
.. _module_mc_uwsgi:

mc_uwsgi / uwsgi functions
============================================
'''

# Import python libs
import logging
import copy
import mc_states.api

import hmac
import hashlib

__name = 'uwsgi'

log = logging.getLogger(__name__)


def settings():
    '''
    uwsgi settings

    location
        installation directory

    package
        list of packages to install uwsgi
    configuration directory
        directory where configuration files are located
    run_at_startup
        "yes" or "no"
    verbose
        "yes" or "no"
    print_confnames_in_initd_script_output
        "yes" or "no"
    inherited_config
        inherited config to fill missing uwsgi parameters
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        uwsgi_reg = __salt__[
            'mc_macros.get_local_registry'](
                'uwsgi', registry_format='pack')
        locs = __salt__['mc_locations.settings']()

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.proxy.uwsgi', {
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

def config_settings(config_name, config_file, enabled, **kwargs):
    '''Settings for the uwsgi macro'''
    uwsgiSettings = copy.deepcopy(__salt__['mc_uwsgi.settings']())
    extra = kwargs.pop('extra', {})
    kwargs.update(extra)
    kwargs.setdefault('config_name', config_name)
    kwargs.setdefault('config_file', config_file)
    kwargs.setdefault('enabled', enabled)
    uwsgiSettings = __salt__['mc_utils.dictupdate'](uwsgiSettings, kwargs)
    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
    uwsgiSettings['data'] = copy.deepcopy(uwsgiSettings)
    uwsgiSettings['data']['extra'] = copy.deepcopy(uwsgiSettings)
    uwsgiSettings['extra'] = copy.deepcopy(uwsgiSettings)
    return uwsgiSettings


#
