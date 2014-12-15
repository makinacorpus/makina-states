# -*- coding: utf-8 -*-
'''
.. _module_mc_redis:

mc_redis / redis functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'redis'

log = logging.getLogger(__name__)


def settings():
    '''
    redis settings

    location
        installation directory

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        redis_reg = __salt__[
            'mc_macros.get_local_registry'](
                'redis', registry_format='pack')
        pw = redis_reg.setdefault(
            'password', __salt__['mc_utils.generate_password']())
        locs = __salt__['mc_locations.settings']()
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.db.redis', {
                'admin': 'admin',
                'password': pw,
                'redisd': {
                    'dbpath': '/var/lib/redis',
                    'logpath': '/var/log/redis/redisd.log',
                    'logappend': 'true',
                    'bind_ip': '127.0.0.1',
                    'port': 27017,
                    'auth': 'true',
                    'nohttpinterface': 'true',
                    'rest': 'false'
                }
            })
        __salt__['mc_macros.update_local_registry'](
            'redis', redis_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
