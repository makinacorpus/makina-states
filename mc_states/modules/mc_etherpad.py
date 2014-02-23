# -*- coding: utf-8 -*-
'''
.. _module_mc_etherpad:

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
        Change which version of etherpad is installed.
    location
        Change the directory in which circus is installed.
    apikey
        The secret used to encrypt transmissions.
    title
        The title of the server.
    ip
        Ip on which the server will bind.
    port
        Port the server will listen for.
    dbType
        Type of the database.
    dbSettings
        Settings of the database.
    requireSession
        Require session setting.
    editOnly
        Edit only setting.
    admin
        Create an admin or not.
    adminPassword
        Admin's password.
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
