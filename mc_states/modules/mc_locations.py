# -*- coding: utf-8 -*-
'''

.. _module_mc_locations:

mc_locations
============================================

'''
# Import python libs
import os
import copy
import logging
import mc_states.api

J = os.path.join
D = os.path.dirname
E = os.path.exists
__name = 'locations'

log = logging.getLogger(__name__)
default_locs = {
    'root_dir': '/',
    'bin_dir': '{usr_dir}/bin',
    'conf_dir': '{root_dir}etc',
    'docker_root': '',
    'home_dir': '{root_dir}home',
    'initd_dir': '{conf_dir}/init.d',
    'root_home_dir': '{root_dir}root',
    'rvm_path': '{rvm_prefix}/rvm',
    'rvm_prefix': '{usr_dir}/local',
    'rvm': '{rvm_path}/bin/rvm',
    'sbin_dir': '{usr_dir}/sbin',
    'share_dir': '{usr_dir}/share',
    'srv_dir': '{root_dir}srv',
    'cops': '{srv_dir}/corpusops/corpusops.bootstrap',
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
    'lxc_root': '',
    'prefix': None,
    'msr': None,
    'pillar_root': '{msr}/pillar',
    'vms_docker_root': '{prefix}/docker',
    'apps_dir': '{prefix}/apps',
    'projects_dir': '{prefix}/projects',
    'remote_projects_dir': '{prefix}/remote_projects',
    'salt_root': '{msr}/salt',
    'makina_states':  '{salt_root}/makina-states',
    'resetperms': '{msr}/_scripts/reset-perms.py',
    'venv': '{msr}/venv',
    'venv_path': '{venv}'}


def first_loc(key, default=None, default_section='base'):
    pr = __opts__[key]
    fpj = default
    for i in [default_section] + [a for a in pr]:
        for j in pr.get(i, []):
            pj = os.path.abspath(j)
            if os.path.exists(pj):
                return pj
    return fpj


def first_pillar_root():
    return first_loc('pillar_roots', '/srv/pillar')


def first_salt_root():
    return first_loc('salt_roots', '/srv/salt')


def msr():
    return os.path.dirname(
        os.path.dirname(
            os.path.abspath(__opts__['config_dir'])))


def prefix():
    return os.path.dirname(msr())


def get_default_locs():
    locationsData = copy.deepcopy(default_locs)
    lmsr = locationsData['msr'] = msr()
    lprefix = locationsData['prefix'] = prefix()
    salt_root = J(lmsr, 'salt')
    # compat with v1
    if not E(salt_root):
        salt_root = J(lmsr, 'fileroot')
    locationsData['salt_root'] = salt_root
    return locationsData


def settings(cached=True):
    '''
    locations
    '''
    def _settings():
        data = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.locations',
            get_default_locs())
        return data
    if cached:
        _settings = mc_states.api.lazy_subregistry_get(
            __salt__, __name)(_settings)
    return _settings()
# vim:set et sts=4 ts=4 tw=80:
