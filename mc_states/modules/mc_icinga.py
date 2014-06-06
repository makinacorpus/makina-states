# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga:

mc_icinga / icinga functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'icinga'

log = logging.getLogger(__name__)


def settings():
    '''
    icinga settings

    location
        installation directory

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        icinga_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga', registry_format='pack')
        locs = __salt__['mc_locations.settings']()
        user = 'user'
        pw = icinga_reg.setdefault(
            'password',
            __salt__['mc_pillar.generate_password']())
        sock = '/tmp/icinga.sock'
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga', {
                'location': locs['apps_dir'] + '/icinga',
                'venv': '{location}/venv',
                'conf': '/etc/icingad.conf',
                'rotate': __salt__['mc_logrotate.settings'](),
                'pidf': locs['var_run_dir'] + '/icingad.pid',
                'includes': ' '.join([
                    '/etc/icinga.d/*.conf',
                    '/etc/icinga.d/*.ini',
                ]),
                'conf_template': (
                    'salt://makina-states/files/etc/icingad.conf'
                ),
                'requirements': ['icinga==1.10.3', ''],
                # parameters to set in icinga configuration section
                'program': {
                    'autostart': 'true',
                    'autorestart': 'true',
                    'stopwaitsecs': '10',
                    'startsecs': '10',
                    'umask': '022',
                },
                'inet_http_server': {
                    'port': 9001,
                    'username': user,
                    'password': pw,
                },
                'unix_http_server': {
                    'file': sock,
                    'chmod': '0777',
                    'chown': 'nobody:nogroup',
                    'username': user,
                    'password': pw,
                },
                'icingad': {
                    'logdir': '/var/log/icinga',
                    'logfile': '/var/log/icingad.log',
                    'logfile_maxbytes': '50MB',
                    'logfile_backups': '10',
                    'loglevel': 'info',
                    'pidfile': '/var/run/icingad.pid',
                    'nodaemon': 'false',
                    'minfds': '1024',
                    'minprocs': '200',
                    'umask': '022',
                    'user': 'root',
                    'identifier': 'icinga',
                    'directory': '/tmp',
                    'tmpdir': '/tmp',
                    'nocleanup': 'true',
                    'childlogdir': '/tmp',
                    'strip_ansi': 'false',
                    'environment': '',
                },
                'icingactl': {
                    'serverurl': 'unix://{0}'.format(sock),
                    'username': user,
                    'password': pw,
                    'history_file': '/etc/icinga.history',
                    'prompt': "icingactl",
                },
            })
        __salt__['mc_macros.update_local_registry'](
            'icinga', icinga_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
