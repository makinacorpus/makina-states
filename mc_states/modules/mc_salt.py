# -*- coding: utf-8 -*-
'''
Salt related variables
============================================

'''
# Import salt libs
import mc_states.utils

__name = 'salt'

loglevelfmt = (
    "'%(asctime)s,%(msecs)03.0f "
    "[%(name)-17s][%(levelname)-8s] %(message)s'")


def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        localsettings = __salt__['mc_localsettings.settings']()
        resolver = __salt__['mc_utils.format_resolve']
        pillar = __pillar__
        locs = localsettings['locations']
        group = localsettings['group']
        groupId = localsettings['groupId']
        # You can overrides this dict via the salt pillar
        # entry 'confRepos', see bellow
        # external base repositories to checkout
        # Add also here the formumlas to checkout
        # and if neccesary the symlink to wire on the salt root tree
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
            'salt-formulae': {
                'name': 'http://github.com/saltstack-formulas/salt-formula.git',
                'link': {'target': '{salt_root}/formulas/salt/salt',
                         'name': '{salt_root}/salt'},
                'target': '{salt_root}/formulas/salt'},
            'openssh-formulae': {
                'name': 'http://github.com/saltstack-formulas/openssh-formula.git',
                'link': {'target': '{salt_root}/formulas/openssh/openssh',
                         'name': '{salt_root}/openssh'},
                'target': '{salt_root}/formulas/openssh'},
            'openstack-formulae': {
                'name': 'https://github.com/kiorky/openstack-salt-states.git',
                'target': '{salt_root}/openstack'},
            'makina-states': {
                'name': 'https://github.com/makinacorpus/makina-states.git',
                'target': '{salt_root}/makina-states'},
        }
        for i, data in confRepos.items():
            for k in ['rev', 'target', 'name']:
                data.update({
                    'rev': __salt__['mc_utils.get']
                    ('makina-states.salt.' + i + '.rev',
                     data.get('rev', False))})
        saltCommonData = {
            'confRepos': confRepos,
            'rotate': localsettings['rotate']['days'],
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
            'vms_docker_root': localsettings['locations']['vms_docker_root'],
            'docker_root': localsettings['locations']['docker_root'],
            'resetperms': 'file://{msr}/_scripts/reset-perms.sh',
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
        saltMinionData = __salt__['mc_utils.dictupdate'](saltCommonData.copy(), {
            'service_name': 'minion',
            'master': '127.0.0.1',
            'master_port': '4506',
            'retry_dns': '30',
            'id': __salt__['config.option']('id', None),
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
                            '{salt_root}/makina-states/ext_mods/mc_modules'],
            'returner_dirs': ['{salt_root}/_returners',
                              '{salt_root}/makina-states/ext_mods/mc_returners'],
            'grain_dirs': ['{salt_root}/_grains',
                            '{salt_root}/makina-states/ext_mods/mc_grains'],
            'states_dirs': ['{salt_root}/_states',
                            '{salt_root}/makina-states/ext_mods/mc_states'],
            'render_dirs': ['{salt_root}/_renderers',
                            '{salt_root}/makina-states/ext_mods/mc_renderers'],
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
        saltMasterData = __salt__['mc_utils.dictupdate'](saltCommonData.copy(), {
            'service_name': 'master',
            'interface': '127.0.0.1',
            'publish_port': '4505',
            'ret_port': '4506',
            'max_open_files': '100000',
            'worker_threads': '5',
            'dev_worker_threads': '2',
            'keep_jobs': '744',
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
                            '{salt_root}/makina-states/ext_mods/mc_runners'],
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
        })
        #  mastersalt daemon overrides
        mastersaltCommonData = __salt__['mc_utils.dictupdate'](
            saltCommonData.copy(), {'pref_name': 'master',
                                    'pillar_root': locs['prefix'] + '/{name}-pillar'})
        mastersaltMasterData = __salt__['mc_utils.dictupdate'](
            saltMasterData.copy(), mastersaltCommonData.copy())
        mastersaltMinionData = __salt__['mc_utils.dictupdate'](
            saltMinionData.copy(), mastersaltCommonData.copy())
        mastersaltMasterData = __salt__['mc_utils.dictupdate'](
            mastersaltMasterData, {
                'publish_port': '4605',
                'ret_port': '4606'})
        mastersaltMinionData = __salt__['mc_utils.dictupdate'](
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
        saltMasterData = __salt__['mc_utils.dictupdate'](
            saltMasterData,  saltCommonPillar.copy())
        saltMinionData = __salt__['mc_utils.dictupdate'](
            saltMinionData, saltCommonPillar.copy())
        mastersaltMasterData = __salt__['mc_utils.dictupdate'](
            mastersaltMasterData, mastersaltCommonPillar.copy())
        mastersaltMinionData = __salt__['mc_utils.dictupdate'](
            mastersaltMinionData, mastersaltCommonPillar.copy())
        #  per daemon pillar overrides
        saltMasterData = __salt__['mc_utils.dictupdate'](
            saltMasterData,  saltMasterPillar.copy())
        saltMinionData = __salt__['mc_utils.dictupdate'](
            saltMinionData, saltMinionPillar.copy())
        #  per mastersalt daemon pillar overrides
        mastersaltMasterData = __salt__['mc_utils.dictupdate'](
            mastersaltMasterData, mastersaltMasterPillar.copy())
        mastersaltMinionData = __salt__['mc_utils.dictupdate'](
            mastersaltMinionData, mastersaltMinionPillar.copy())
        #
        ########################################
        # default exposed global variables
        ########################################
        # SALT VARIABLES

        saltCommonData = resolver(saltCommonData)
        saltMasterData = resolver(saltMasterData)
        saltMinionData = resolver(saltMinionData)
        saltname = saltCommonData['name']
        saltprefix = saltCommonData['prefix']
        prefix = saltprefix
        projectsRoot = saltCommonData['projects_root']
        vagrantRoot = saltCommonData['vagrant_root']
        dockerRoot = saltCommonData['docker_root']
        saltroot = saltCommonData['salt_root']
        saltRoot = saltroot
        confPrefix = saltCommonData['conf_prefix']
        cachePrefix = saltCommonData['cache_prefix']
        runPrefix = saltCommonData['run_prefix']
        logPrefix = saltCommonData['log_prefix']
        pillarRoot = saltCommonData['pillar_root']
        msr = saltroot + '/makina-states'
        resetperms = 'file://' + msr + '/_scripts/reset-perms.sh'
        saltbinpath = msr + '/bin'
        #  MASTERSALT VARIABLES
        mastersaltCommonData = resolver(mastersaltCommonData)
        mastersaltMasterData = resolver(mastersaltMasterData)
        mastersaltMinionData = resolver(mastersaltMinionData)
        msaltname = mastersaltCommonData['name']
        msaltprefix = mastersaltCommonData['prefix']
        mprefix = msaltprefix
        mprojects_root = mastersaltCommonData['projects_root']
        mvagrant_root = mastersaltCommonData['vagrant_root']
        msaltroot = mastersaltCommonData['salt_root']
        msaltRoot = msaltroot
        mconfPrefix = mastersaltCommonData['conf_prefix']
        mcachePrefix = mastersaltCommonData['cache_prefix']
        mrunPrefix = mastersaltCommonData['run_prefix']
        mlogPrefix = mastersaltCommonData['log_prefix']
        mpillarRoot = mastersaltCommonData['pillar_root']
        mmsr = msaltroot + '/makina-states'
        mresetperms = 'file://' + mmsr + '/_scripts/reset-perms.sh'
        msaltbinpath = mmsr + '/bin'
        #  mappings
        data_mappings = {
            'master': {
                'salt': saltMasterData,
                'mastersalt': mastersaltMasterData,
            },
            'minion': {
                'salt': saltMinionData,
                'mastersalt': mastersaltMinionData,
            }
        }
        return locals()
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
