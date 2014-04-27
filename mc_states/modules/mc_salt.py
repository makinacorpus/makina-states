# -*- coding: utf-8 -*-
'''
.. _module_mc_salt:

mc_salt / salt related helpers
================================

'''
# Import salt libs
import mc_states.utils
import os

__name = 'salt'

loglevelfmt = (
    "'%(asctime)s,%(msecs)03.0f "
    "[%(name)-17s][%(levelname)-8s] %(message)s'")


def settings():
    '''Registry of settings decriving salt installation

    Please read the code to be sure to understand it before changing parameters
    as it can brick your installation.
    That's why most of this stuff will be underdocumented at first sight.
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        nodetypes_reg = saltmods['mc_nodetypes.registry']()
        resolver = saltmods['mc_utils.format_resolve']
        pillar = __pillar__
        locs = saltmods['mc_locations.settings']()
        usergroup = saltmods['mc_usergroup.get_default_groups']()
        group = usergroup['group']
        groupId = usergroup['groupId']
        # You can overrides this dict via the salt pillar
        # entry 'confRepos', see bellow
        # external base repositories to checkout
        # Add also here the formumlas to checkout
        # and if neccesary the symlink to wire on the salt root tree
        salt_ssh_data = saltmods['mc_utils.defaults'](
            'makina-states.controllers.salt.ssh', {
                'priv': '/root/.ssh/id_rsa',
                'roster': {}})
        for id_ in [a for a in salt_ssh_data['roster']]:
            data = salt_ssh_data['roster'][id_]
            data.setdefault('priv', salt_ssh_data['priv'])
        confRepos = {
            'salt-git': {
                'name': 'http://github.com/makinacorpus/salt.git',
                'rev': 'develop',
                'target': '{salt_root}/makina-states/src/salt'},
            'SaltTesting-git': {
                'name': 'http://github.com/saltstack/salt-testing.git',
                'rev': 'develop',
                'target': '{salt_root}/makina-states/src/SaltTesting'},
            'm2crypto': {
                'name': 'https://github.com/makinacorpus/M2Crypto.git',
                'target': '{salt_root}/makina-states/src/m2crypto'},
            #'salt-formulae': {
            #    'name': 'http://github.com/saltstack-formulas/salt-formula.git',
            #    'link': {'target': '{salt_root}/formulas/salt/salt',
            #             'name': '{salt_root}/salt'},
            #    'target': '{salt_root}/formulas/salt'},
            #'openssh-formulae': {
            #    'name': 'http://github.com/saltstack-formulas/openssh-formula.git',
            #    'link': {'target': '{salt_root}/formulas/openssh/openssh',
            #             'name': '{salt_root}/openssh'},
            #    'target': '{salt_root}/formulas/openssh'},
            #'openstack-formulae': {
            #    'name': 'https://github.com/kiorky/openstack-salt-states.git',
            #    'target': '{salt_root}/openstack'},
            'makina-states': {
                'name': 'https://github.com/makinacorpus/makina-states.git',
                'target': '{salt_root}/makina-states'},
        }
        for i, data in confRepos.items():
            for k in ['rev', 'target', 'name']:
                data.update({
                    'rev': saltmods['mc_utils.get']
                    ('makina-states.salt.' + i + '.rev',
                     data.get('rev', False))})
        data = {}
        has_filelimit = True
        init_debug = False
        if 'TRAVIS' in os.environ:
            init_debug = True
        if saltmods['mc_lxc.is_lxc']():
            has_filelimit = False
        crons = True
        env = saltmods['mc_env.settings']()['env']
        if (
            nodetypes_reg['is']['devhost']
            or env in ['dev']
        ):
            crons = False

        saltCommonData = {
            'module_dirs': ['{salt_root}/_modules',
                            '{salt_root}/makina-states/mc_states/modules'],
            'returner_dirs': ['{salt_root}/_returners',
                              '{salt_root}/makina-states/mc_states/returners'],
            'grain_dirs': ['{salt_root}/_grains',
                           '{salt_root}/makina-states/mc_states/grains'],
            'states_dirs': ['{salt_root}/_states',
                            '{salt_root}/makina-states/mc_states/states'],
            'render_dirs': ['{salt_root}/_renderers',
                            '{salt_root}/makina-states/mc_states/renderers'],
            'cron_auto_clean': crons,
            'cron_auto_sync': crons,
            'cron_auto_restart': crons,
            'cron_check_alive': crons,
            'cron_auto_upgrade': crons,
            'cron_clean_minute': 'random',
            'cron_clean_hour': '0,6,12,18',
            'cron_minion_checkalive': '*/10',
            'cron_sync_minute': '*/10',
            'cron_sync_hour': '*',
            'cron_upgrade_minute': 3,
            'cron_upgrade_hour': 0,
            'cron_master_restart_minute': 0,
            'cron_master_restart_hour': 0,
            'cron_minion_restart_minute': 3,
            'cron_minion_restart_hour': 0,
            'init_debug': init_debug,
            'has_filelimit': has_filelimit,
            'confRepos': confRepos,
            'rotate': saltmods['mc_logrotate.settings']()['days'],
            'yaml_utf8': True,
            'root_dir': locs['root_dir'],
            'conf_dir': locs['conf_dir'],
            'bin_dir': locs['bin_dir'],
            'bin_dir': locs['bin_dir'],
            'upstart_dir': locs['upstart_dir'],
            'var_prefix': locs['var_dir'],
            'initd_dir': locs['initd_dir'],
            'pref_name': '',
            'name': '{pref_name}salt',
            'group': group,
            'groupId': groupId,
            'projects_root': '{prefix}/projects',
            'vagrant_root': '{prefix}/vagrant',
            'vms_docker_root': locs['vms_docker_root'],
            'docker_root': locs['docker_root'],
            'resetperms': '{msr}/_scripts/reset-perms.py',
            'init_d': '{initd_dir}',
            'prefix': locs['prefix'],
            'venv': locs['venv'],
            'salt_root': '{prefix}/{name}',
            'msr': '{salt_root}/makina-states',
            'pillar_root': '{prefix}/pillar',
            'conf_prefix': '{conf_dir}/{name}',
            'cache_prefix': '{var_prefix}/cache/{name}',
            'run_prefix': '{var_prefix}/run',
            'daemon_name': '{name}-{service_name}',
            'default_include': '{service_name}.d/*.conf',
            'cachedir': '{cache_prefix}/{daemon_name}',
            'pki_dir': '{conf_prefix}/pki/{service_name}',
            'pidfile': '{run_prefix}/{daemon_name}.pid',
            'sock_dir': '{run_prefix}/{name}/{service_name}',
            'log_prefix': '{var_prefix}/log/{name}',
            'log_file': '{log_prefix}/{daemon_name}',
            'key_logfile': '{log_prefix}/{daemon_name}-key',
            'log_level': 'warning',
            'log_level_logfile': 'info',
            'log_datefmt': "'%H:%M:%S'",
            'log_datefmt_logfile': "'%Y-%m-%d %H:%M:%S'",
            'log_fmt_console': "'[%(levelname)-8s] %(message)s'",
            'log_fmt_logfile': loglevelfmt,
            'verify_env': True,
            'loop_interval': '60',
            'user': 'root',
            'file_roots': {'base': ['{salt_root}']},
            'pillar_roots': {'base': ['{pillar_root}']},
            'include': [],
            'ipv6': False,
            'color': True,
            'open_mode': False,
            'permissive_pki_access': False,
            'state_output': 'full',
            'state_verbose': True,
            'state_top': 'top.sls',
            'cython_enable': False,
            'failhard': False,
            'log_granular_levels': {},
            'salt_modules': [
                '_grains',
                '_modules',
                '_renderers',
                '_runners',
                '_returners',
                '_states',
            ]
        }
        #  default daemon overrides
        saltMinionData = saltmods['mc_utils.dictupdate'](saltCommonData.copy(), {
            'service_name': 'minion',
            'master': '127.0.0.1',
            'master_port': '4506',
            'retry_dns': '30',
            'id': saltmods['config.option']('makina-states.minion_id',
                                            saltmods['config.option']('id', None)),
            'append_domain': False,
            'grains': {},
            'output': None,
            'cache_jobs': False,
            'disable_modules': [],
            'disable_returners': [],
            'minion': None,
            'backup_mode': '',
            'acceptance_wait_time': '10',
            'top_file': '""',
            'acceptance_wait_time_max': '0',
            'random_reauth_delay': '60',
            'recon_default': '100',
            'recon_max': '5000',
            'recon_randomize': False,
            'dns_check': True,
            'ipc_mode': 'ipc',
            'tcp_pub_port': '4510',
            'tcp_pull_port': '4511',
            'module_dirs': ['{salt_root}/_modules',
                            '{salt_root}/makina-states/mc_states/modules'],
            'returner_dirs': ['{salt_root}/_returners',
                              '{salt_root}/makina-states/mc_states/returners'],
            'grain_dirs': ['{salt_root}/_grains',
                           '{salt_root}/makina-states/mc_states/grains'],
            'states_dirs': ['{salt_root}/_states',
                            '{salt_root}/makina-states/mc_states/states'],
            'render_dirs': ['{salt_root}/_renderers',
                            '{salt_root}/makina-states/mc_states/renderers'],
            'providers': {},
            'autoload_dynamic_modules': True,
            'clean_dynamic_modules': True,
            'environment': None,
            'startup_states': "''",
            'sls_list': '[]',
            '': "''",
            'file_client': 'remote',
            'master_finger': "''",
            'multiprocessing': True,
            'update_url': False,
            'update_restart_services': '[]',
            'tcp_keepalive': True,
            'tcp_keepalive_idle': '300',
            'tcp_keepalive_cnt': '-1',
            'tcp_keepalive_intvl': '-1',
            'win_repo_cachefile': 'salt://win/repo/winrepo.p',
        })
        #  default master settings
        saltMasterData = saltmods['mc_utils.dictupdate'](
            saltCommonData.copy(), {
                'service_name': 'master',
                'ssh': salt_ssh_data,
                'interface': '127.0.0.1',
                'publish_port': '4505',
                'ret_port': '4506',
                'max_open_files': '100000',
                'worker_threads': '5',
                'dev_worker_threads': '2',
                'keep_jobs': '24',
                'timeout': '120',
                'output': None,
                'job_cache': True,
                'minion_data_cache': True,
                'auto_accept': False,
                'autosign_file': '{conf_prefix}/autosign.conf',
                'client_acl_blacklist': {},
                'external_auth': {},
                'token_expire': '43200',
                'file_recv': False,
                'master_tops': {},
                'external_nodes': None,
                'renderer': 'yaml_jinja',
                'hash_type': 'md5',
                'file_buffer_size': '1048576',
                'file_ignore_regex': [],
                'runner_dirs': ['{salt_root}/_runners',
                                '{salt_root}/makina-states/mc_states/runners'],
                'file_ignore_glob': [],
                'fileserver_backend':  ['roots', 'git'],
                'gitfs_remotes': '[]',
                'ext_pillar': {},
                'pillar_opts': True,
                'order_masters': True,
                'syndic_master': None,
                'syndic_master_port': '4506',
                'syndic_pidfile':  '{run_prefix}/{name}-syndic.pid',
                'syndic_log_file': '{log_prefix}/{name}-syndic',
                'peer': {},
                'peer_run': {},
                'nodegroups': {},
                'range_server': None,
                'win_repo': '{salt_root}/win/repo',
                'win_repo_mastercachefile': '{salt_root}/win/repo/winrepo.p',
                'win_gitrepos': [],
            }
        )


        #  mastersalt daemon overrides
        mastersaltCommonData = saltmods['mc_utils.dictupdate'](
            saltCommonData.copy(), {'pref_name': 'master',
                                    'pillar_root': locs['prefix'] + '/{name}-pillar'})
        mastersaltMasterData = saltmods['mc_utils.dictupdate'](
            saltMasterData.copy(), mastersaltCommonData.copy())
        mastersaltMinionData = saltmods['mc_utils.dictupdate'](
            saltMinionData.copy(), mastersaltCommonData.copy())
        mastersaltMasterData = saltmods['mc_utils.dictupdate'](
            mastersaltMasterData, {
                'publish_port': '4605',
                'ret_port': '4606'})
        mastersaltMinionData = saltmods['mc_utils.dictupdate'](
            mastersaltMinionData, {
                'master': '127.0.0.1',
                'master_port': '4606',
                'tcp_pub_port': '4610',
                'tcp_pull_port': '4611'})
        #  common pillar overrides
        salt_pillar = pillar.get('salt', {})
        saltCommonPillar = salt_pillar.get('common', {})
        saltMasterPillar = salt_pillar.get('master', {})
        saltMinionPillar = salt_pillar.get('minion', {})
        mastersalt_pillar = pillar.get('mastersalt', {})
        mastersaltCommonPillar = mastersalt_pillar.get('common', {})
        mastersaltMasterPillar = mastersalt_pillar.get('master', {})
        mastersaltMinionPillar = mastersalt_pillar.get('minion', {})
        #  per daemon commpon section overrides
        saltMasterData = saltmods['mc_utils.dictupdate'](
            saltMasterData,  saltCommonPillar.copy())
        saltMinionData = saltmods['mc_utils.dictupdate'](
            saltMinionData, saltCommonPillar.copy())
        mastersaltMasterData = saltmods['mc_utils.dictupdate'](
            mastersaltMasterData, mastersaltCommonPillar.copy())
        mastersaltMinionData = saltmods['mc_utils.dictupdate'](
            mastersaltMinionData, mastersaltCommonPillar.copy())
        #  per daemon pillar overrides
        saltMasterData = saltmods['mc_utils.dictupdate'](
            saltMasterData,  saltMasterPillar.copy())
        saltMinionData = saltmods['mc_utils.dictupdate'](
            saltMinionData, saltMinionPillar.copy())
        #  per mastersalt daemon pillar overrides
        mastersaltMasterData = saltmods['mc_utils.dictupdate'](
            mastersaltMasterData, mastersaltMasterPillar.copy())
        mastersaltMinionData = saltmods['mc_utils.dictupdate'](
            mastersaltMinionData, mastersaltMinionPillar.copy())
        #
        ########################################
        # default exposed global variables
        ########################################
        # SALT VARIABLES
        data['saltCommonData'] = saltCommonData = resolver(saltCommonData)
        data['saltMasterData'] = saltMasterData = resolver(saltMasterData)
        data['saltMinionData'] = saltMinionData = resolver(saltMinionData)
        data['saltname'] = saltCommonData['name']
        saltprefix = data['saltprefix'] = saltCommonData['prefix']
        data['prefix'] = saltprefix
        data['projectsRoot'] = saltCommonData['projects_root']
        data['vagrantRoot'] = saltCommonData['vagrant_root']
        data['dockerRoot'] = saltCommonData['docker_root']
        saltroot = data['saltroot'] = saltCommonData['salt_root']
        data['saltRoot'] = saltroot
        data['confPrefix'] = saltCommonData['conf_prefix']
        data['cachePrefix'] = saltCommonData['cache_prefix']
        data['runPrefix'] = saltCommonData['run_prefix']
        data['logPrefix'] = saltCommonData['log_prefix']
        data['pillarRoot'] = saltCommonData['pillar_root']
        msr = data['msr'] = saltroot + '/makina-states'
        data['resetperms'] = msr + '/_scripts/reset-perms.py'
        data['saltbinpath'] = msr + '/bin'

        #  MASTERSALT VARIABLES
        mastersaltCommonData = resolver(mastersaltCommonData)
        data['mastersaltCommonData'] = mastersaltCommonData
        mastersaltMasterData = resolver(mastersaltMasterData)
        data['mastersaltMasterData'] = mastersaltMasterData
        mastersaltMinionData = resolver(mastersaltMinionData)
        data['mastersaltMinionData'] = mastersaltMinionData

        data['msaltname'] = mastersaltCommonData['name']
        msaltprefix = data['msaltprefix'] = mastersaltCommonData['prefix']
        data['mprefix'] = msaltprefix
        data['mprojects_root'] = mastersaltCommonData['projects_root']
        data['mvagrant_root'] = mastersaltCommonData['vagrant_root']
        msaltroot = data['msaltroot'] = mastersaltCommonData['salt_root']
        data['msaltRoot'] = msaltroot
        data['mconfPrefix'] = mastersaltCommonData['conf_prefix']
        data['mcachePrefix'] = mastersaltCommonData['cache_prefix']
        data['mrunPrefix'] = mastersaltCommonData['run_prefix']
        data['mlogPrefix'] = mastersaltCommonData['log_prefix']
        data['mpillarRoot'] = mastersaltCommonData['pillar_root']
        mmsr = data['mmsr'] = msaltroot + '/makina-states'
        data['mresetperms'] = mmsr + '/_scripts/reset-perms.py'
        data['msaltbinpath'] = mmsr + '/bin'

        keys = ['saltname', 'prefix', 'projects_root', 'vagrant_root',
                'saltRoot', 'confPrefix', 'cachePrefix', 'runPrefix',
                'logPrefix', 'pillarRoot', 'msr', 'saltbinpath']
        if __salt__['mc_utils.get']('config_dir') == data['mconfPrefix']:
            pref = 'm'
            csaltMasterData = mastersaltMasterData
            csaltMinionData = mastersaltMinionData
        else:
            pref = ''
            csaltMasterData = saltMasterData
            csaltMinionData = saltMinionData

        #  mappings
        data['c'] = {'master': csaltMasterData,
                     'o': {},
                     'minion': csaltMinionData}
        for key in keys:
            data['c']['o'][key] = data['{0}{1}'.format(pref, key)]
        data['data_mappings'] = {
            'master': {
                'salt': saltMasterData,
                'mastersalt': mastersaltMasterData,
            },
            'minion': {
                'salt': saltMinionData,
                'mastersalt': mastersaltMinionData,
            }
        }
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
