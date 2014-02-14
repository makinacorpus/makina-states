# -*- coding: utf-8 -*-
'''
mc_etherpad / etherpad functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'etherpad'

log = logging.getLogger(__name__)


def settings():
    '''
    Etherpad settings

    version
        TBD
    location
        TBD
    apikey
        TBD
    title
        TBD
    ip
        TBD
    port
        TBD
    dbType
        TBD
    dbSettings
        TBD
    requireSession
        TBD
    editOnly
        TBD
    admin
        TBD
    adminPassword
        TBD
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locs = localsettings['locations']
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.collab.etherpad', {
                'version': '1.3.0',
                'location': locs['apps_dir'] + '/etherpad',
                'apikey': 'SECRET-API-KEY-PLS-CHANGE-ME',
                'title': 'Etherpad',
                'ip': '0.0.0.0',
                'port': '9001',
                'dbType': 'dirty',
                'dbSettings': '{"filename": "var/dirty.db"}',
                'requireSession': 'true',
                'editOnly': 'false',
                'admin': False,
                'adminPassword': 'admin',
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
