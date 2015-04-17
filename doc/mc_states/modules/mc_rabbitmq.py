# -*- coding: utf-8 -*-
'''
.. _module_mc_rabbitmq:

mc_rabbitmq / rabbitmq functions
============================================



'''

# Import python libs
import logging
import mc_states.api

__name = 'rabbitmq'

log = logging.getLogger(__name__)


def settings():
    '''
    rabbitmq settings

    location
        installation directory

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        rabbitmq_reg = __salt__[
            'mc_macros.get_local_registry'](
                'rabbitmq', registry_format='pack')
        pw = rabbitmq_reg.setdefault(
            'password', __salt__['mc_utils.generate_password']())
        locs = __salt__['mc_locations.settings']()
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.db.rabbitmq', {
                'admin': 'admin',
                'password': pw,
                'defaults': {
                    'ulimit': 1024,
                    'RABBITMQ_NODENAME': 'rabbit@' + __grains__['host'],
                    'RABBITMQ_BASE': '/var/lib/rabbitmq/mnesia/',
                    'RABBITMQ_CONFIG_FILE': '/etc/rabbitmq/rabbitmq',
                    'RABBITMQ_NODE_IP_ADDRESS': "'0.0.0.0'",
                    'RABBITMQ_NODE_PORT': 5672,
                    'RABBITMQ_LOG_BASE': '/var/log/rabbitmq',
                },
                'dbs': {
                },
                'users': {
                },
                'rabbitmq': {
                    'plugins': [
                        'rabbitmq_management',
                        'rabbitmq_web_stomp',
                        'rabbitmq_stomp',
                    ],
                    'admin': 'admin',
                    'password': __salt__['mc_utils.generate_stored_password'](
                        'rabbitmq_server'),
                }
            })
        __salt__['mc_macros.update_local_registry'](
            'rabbitmq', rabbitmq_reg,
            registry_format='pack')
        return data
    return _settings()



#
