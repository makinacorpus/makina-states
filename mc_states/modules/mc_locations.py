## -*- coding: utf-8 -*-
'''

.. _module_mc_locations:

mc_locations
============================================

'''
# Import python libs
import logging
import mc_states.utils

__name = 'locations'

log = logging.getLogger(__name__)


def settings():
    '''
    locations

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        # default paths
        # locationsVariables = {
        #     'prefix': '/srv'
        #      ...
        # }
        #
        # include the macro in your states and use:
        #   {{ salt['mc_locations.settings']().prefix }}
        #
        locationsData = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.locations', {
                'root_dir': '/',
                'home_dir': '{root_dir}home',
                'root_home_dir': '{root_dir}root',
                'sysadmins_home_dir': '{home_dir}',
                'users_home_dir': '{home_dir}/users',
                'usr_dir': '{root_dir}usr',
                'share_dir': '{usr_dir}/share',
                'bin_dir': '{usr_dir}/bin',
                'sbin_dir': '{usr_dir}/sbin',
                'venv': '{root_dir}salt-venv',
                'srv_dir': '{root_dir}srv',
                'prefix': '{srv_dir}',
                'rvm_prefix': '{usr_dir}/local',
                'rvm_path': '{rvm_prefix}/rvm',
                'rvm': '{rvm_path}/bin/rvm',
                'vms_docker_root': '{srv_dir}/docker',
                'docker_root': '',
                'lxc_root': '',
                'apps_dir': '{srv_dir}/apps',
                'projects_dir': '{srv_dir}/projects',
                'conf_dir': '{root_dir}etc',
                'initd_dir': '{conf_dir}/init.d',
                'upstart_dir': '{conf_dir}/init',
                'tmp_dir': '{root_dir}tmp',
                'var_dir': '{root_dir}var',
                'var_lib_dir': '{var_dir}/lib',
                'var_spool_dir': '{var_dir}/spool',
                'var_run_dir': '{var_dir}/run',
                'var_log_dir': '{var_dir}/log',
                'var_tmp_dir': '{var_dir}/tmp',
                'resetperms': (
                    '{prefix}/salt/makina-states/_scripts/reset-perms.py'
                ),
            })
        return locationsData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

# vim:set et sts=4 ts=4 tw=80:
