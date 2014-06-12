# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga_web:

mc_icinga_web / icinga_web functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'icinga_web'

log = logging.getLogger(__name__)


def settings():
    '''
    icinga_web settings

    location
        installation directory

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        icinga_web_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga_web', registry_format='pack')
        locs = __salt__['mc_locations.settings']()

        # generate default password
        icinga_web_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga_web', registry_format='pack')

        password_web = icinga_web_reg.setdefault('web.password', __salt__['mc_utils.generate_password']())

        # get default ido password
        password_ido=""
        # TODO

        ido2db_database = {
            'type': "pgsql",
            'host': "localhost",
            'port': 5432,
#            'socket': "",
            'user': "icinga",
            'password': password_ido,
            'name': "icinga_ido",
            'prefix': "icinga_",
        }

        web_database = {
            'type': "pgsql",
            'host': "localhost",
            'port': 5432,
#            'socket': "",
            'user': "icinga",
            'password': password_web,
            'name': "icinga_web",
            'prefix': "nsm_",
        }

        has_sgbd = ((('host' in web_database)
                     and (web_database['host']
                          in  [
                              'localhost', '127.0.0.1', grains['host']
                          ]))
                    or ('socket' in web_database))

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga_web', {
                'package': ['icinga-web'],
                'configuration_directory': locs['conf_dir']+"/icinga-web",
                'has_pgsql': ('pgsql' == web_database['type']
                              and has_sgbd),
                'has_mysql': ('mysql' == web_database['type']
                              and has_sgbd),
                'databases': {
                    'ido2db': ido2db_database,
                    'web': web_database,
                }
        })

        __salt__['mc_macros.update_local_registry'](
            'icinga_web', icinga_web_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
