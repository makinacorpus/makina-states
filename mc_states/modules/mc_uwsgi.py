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
        })

        __salt__['mc_macros.update_local_registry'](
            'uwsgi', uwsgi_reg,
            registry_format='pack')
        return data
    return _settings()

#def config_settings(name, **kwargs):
#    '''Settings for the nginx macro'''
#    uwsgiSettings = copy.deepcopy(__salt__['mc_uwsgi.settings']())
#    # retro compat
#    extra = kwargs.pop('extra', {})
#    kwargs.update(extra)
#    kwargs.setdefault('name', name)
#    kwargs.setdefault('config_file', config_file)
#    uwsgiSettings = __salt__['mc_utils.dictupdate'](nginxSettings, kwargs)
#    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
#    uwsgiSettings['data'] = copy.deepcopy(uwsgiSettings)
#    uwsgiSettings['data']['extra'] = copy.deepcopy(uwsgiSettings)
#    uwsgiSettings['extra'] = copy.deepcopy(uwsgiSettings)
#    return uwsgiSettings




def dump():
    return mc_states.utils.dump(__salt__,__name)

#
