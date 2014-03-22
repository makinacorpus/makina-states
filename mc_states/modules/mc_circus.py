# -*- coding: utf-8 -*-
'''
.. _module_mc_circus:

mc_circus / circus functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'circus'

log = logging.getLogger(__name__)


def settings():
    '''
    circus settings

    location
        installation directory

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        locs = localsettings['locations']
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.circus', {
                'location': locs['apps_dir'] + '/circus',
                'rotate': localsettings['rotate'],
                'requirements': [
                    'circus==0.10.0',
                    'circus-web==0.4.1',
                ],
                # parameters to set in circus configuration section
                'circusd': {
                    'warmup_delay': "0",
                    'umask': "002",
                    'httpd': True,
                    'stream_backend': 'thread',
                    'loglevel': 'info',
                    'debug': False,
                    'statsd': True,
                    'statsd_close_outputs': False,
                    'httpd_close_outputs': False,
                    'check_delay': "5",
                    'httpd_host': "localhost",
                    'httpd_port': "5554",
                    'endpoint': "tcp://127.0.0.1:5555",
                    'pubsub_endpoint': "tcp://127.0.0.1:5556",
                    'stats_endpoint': 'tcp://127.0.0.1:5557',
                }
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
