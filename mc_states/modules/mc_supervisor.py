# -*- coding: utf-8 -*-
'''
.. _module_mc_supervisor:

mc_supervisor / supervisor functions
============================================




'''

# Import python libs
import logging
import mc_states.api

__name = 'supervisor'

log = logging.getLogger(__name__)


def settings():
    '''
    supervisor settings

    location
        installation directory

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        supervisor_reg = __salt__[
            'mc_macros.get_local_registry'](
                'supervisor', registry_format='pack')
        locs = __salt__['mc_locations.settings']()
        user = 'user'
        pw = supervisor_reg.setdefault(
            'password',
            __salt__['mc_utils.generate_password']())
        sock = '/tmp/supervisor.sock'
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.supervisor', {
                'location': locs['apps_dir'] + '/supervisor',
                'venv': '{location}/venv',
                'conf': '/etc/supervisord.conf',
                'rotate': __salt__['mc_logrotate.settings'](),
                'pidf': locs['var_run_dir'] + '/supervisord.pid',
                'includes': ' '.join([
                    '/etc/supervisor.d/*.conf',
                    '/etc/supervisor.d/*.ini',
                ]),
                'configs': {
                    '/etc/supervisord.conf': {"mode": "644"},
                    '/etc/logrotate.d/supervisor.conf': {"mode": "644"},
                    '/usr/bin/ms_supervisorctl': {"mode": "755"},
                    '/etc/init.d/ms_supervisor': {"mode": "755"},
                    '/etc/init/ms_supervisor.conf': {"mode": "755"},
                    '/etc/systemd/system/ms_supervisor.service': {
                        "mode": "644"}
                },
                'requirements': ['supervisor==3.2.0'],
                # parameters to set in supervisor configuration section
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
                'supervisord': {
                    'logdir': '/var/log/supervisor',
                    'logfile': '/var/log/supervisord.log',
                    'logfile_maxbytes': '50MB',
                    'logfile_backups': '10',
                    'loglevel': 'info',
                    'pidfile': '/var/run/supervisord.pid',
                    'nodaemon': 'false',
                    'minfds': '1024',
                    'minprocs': '200',
                    'umask': '022',
                    'user': 'root',
                    'identifier': 'supervisor',
                    'directory': '/tmp',
                    'tmpdir': '/tmp',
                    'nocleanup': 'true',
                    'childlogdir': '/tmp',
                    'strip_ansi': 'false',
                    'environment': '',
                },
                'supervisorctl': {
                    'serverurl': 'unix://{0}'.format(sock),
                    'username': user,
                    'password': pw,
                    'history_file': '/etc/supervisor.history',
                    'prompt': "supervisorctl",
                },
            })
        __salt__['mc_macros.update_local_registry'](
            'supervisor', supervisor_reg,
            registry_format='pack')
        return data
    return _settings()
