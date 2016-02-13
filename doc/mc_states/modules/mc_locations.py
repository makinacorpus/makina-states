# -*- coding: utf-8 -*-
'''

.. _module_mc_locations:

mc_locations
============================================

'''
# Import python libs
import copy
import logging
import mc_states.api

__name = 'locations'

log = logging.getLogger(__name__)
default_locs = {
    'srv_dir': '{root_dir}srv',
    'ms': '{srv_dir}/makina-states',
    'apps_dir': '{srv_dir}/apps',
    'bin_dir': '{usr_dir}/bin',
    'conf_dir': '{root_dir}etc',
    'docker_root': '',
    'home_dir': '{root_dir}home',
    'initd_dir': '{conf_dir}/init.d',
    'lxc_root': '',
    'projects_dir': '{srv_dir}/projects',
    'remote_projects_dir': '{srv_dir}/remote_projects',
    'root_dir': '/',
    'root_home_dir': '{root_dir}root',
    'rvm_path': '{rvm_prefix}/rvm',
    'rvm_prefix': '{usr_dir}/local',
    'rvm': '{rvm_path}/bin/rvm',
    'sbin_dir': '{usr_dir}/sbin',
    'share_dir': '{usr_dir}/share',
    'sysadmins_home_dir': '{home_dir}',
    'tmp_dir': '{root_dir}tmp',
    'upstart_dir': '{conf_dir}/init',
    'users_home_dir': '{home_dir}/users',
    'usr_dir': '{root_dir}usr',
    'var_dir': '{root_dir}var',
    'var_lib_dir': '{var_dir}/lib',
    'var_log_dir': '{var_dir}/log',
    'var_run_dir': '{var_dir}/run',
    'var_spool_dir': '{var_dir}/spool',
    'var_tmp_dir': '{var_dir}/tmp',
    'venv':  (
        '{ms}/venv'
    ),
    'vms_docker_root': '{srv_dir}/docker',
    'resetperms': (
        '{ms}/_scripts/reset-perms.py'
    )}


def settings(cached=True):
    '''
    locations
    '''
    def _settings():
        locationsData = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.locations',
            copy.deepcopy(default_locs))
        return locationsData
    if cached:
        _settings = mc_states.api.lazy_subregistry_get(
            __salt__, __name)(_settings)
    return _settings()
# vim:set et sts=4 ts=4 tw=80:
