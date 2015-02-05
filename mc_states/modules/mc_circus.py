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
        log = '/var/log/circus/circus.log'
        locs = __salt__['mc_locations.settings']()
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.circus', {
                'location': locs['apps_dir'] + '/circus',
                'venv': '{location}/venv',
                'log': log,
                'conf': '/etc/circus/circusd.ini',
                'rotate': __salt__['mc_logrotate.settings'](),
                'pidf': locs['var_run_dir'] + '/circusd.pid',
                'logdir': '/var/log/circus',
                'requirements': [
                    'circus==0.11.1',
                    'circus-web==0.5',
                ],
                # parameters to set in circus configuration section
                'circusd': {
                    'warmup_delay': "0",
                    'umask': "002",
                    'httpd': False,
                    'stream_backend': 'thread',
                    'loglevel': 'info',
                    'debug': False,
                    'logoutput': log,
                    'statsd': False,
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



#
