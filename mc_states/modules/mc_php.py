# -*- coding: utf-8 -*-
'''

.. _module_mc_php:

mc_php / php registry
============================================

If you alter this module and want to test it, do not forget to deploy it on
minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_php

'''

# Import python libs
import logging
import mc_states.api
import copy
import os
from distutils.version import LooseVersion

# Import salt libs
from salt import utils, exceptions

__name = 'php'

log = logging.getLogger(__name__)


def settings():
    '''
    This is called from mc_services, loading all PHP default settings

    Settings are merged with grains and pillar via mc_utils.defaults

    ::

        ------------------------------------------------
        -------- MODULE ZEND OPCACHE --------------------------
        replacement for APC!
        @see for details of options:
        https://raw.github.com/zendtech/ZendOptimizerPlus/master/README

    ::

        -------- MODULE APC ---------------------------------
        WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
        WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
        WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
        WARNING : APC is somewhat deprecated and Zend opcache is the replacment
        So the default behavior will not be to install it!!!

    APC General shared settings

        shm_segments
          seems to perform better with only one shared segment
          but if you cannot upgrade this segment size, then create several
          setting ignored in mmap mode
          (so chances are this will always be 1)

    shm_size
        so here the segment size, but you may need to allow it in your OS
        for 128M Put in /etc/sysctl.conf

            * kernel.shmmax=134217728
            * kernel.shmall=2097152

        default in most OS is 32M
    mmap_file_mask
        If compiled with MMAP support by using --enable-mmap this is the
        mktemp-style file_mask to pass to the mmap module
        for determining whether your mmap'ed memory region is going to be
        file-backed or shared memory backed
    APC
        Per virtualhost/php-fpm pool:
            enabled
                enabling apc
            rfc1867
                allow progress upload bars
    APC
        include_once_override
            Optimisation of include/require_once calls
        canonicalize
            transform paths in absolute ones (no effect
            if apc.stat is not 0), files from stream wrappers (extended
            includes) won't be cached if this is activated as they cannot
            be used with php's realpath()
        stat
            In production set it to False, then file changes won't be
            observed before apache or php-fpm is restarted, significant
            boost, else file time is stated at each access
            (needed at True in dev)
        stat_ctime
            avoid problems with rsync or svn not modifying mtime but only
            ctime so if you're in production set this to False,
            like for the previous one
        num_files_hint
            indication on number of files (ZF=1300, nude Drupal 7=1000)
        user_entries_hint
            indication on the number of cache variables

    APC: cache lifetime managmenent
        ttl
            time (s) we can stay on the cache even when the cache is full

            Cache full count
                that means Garbage Collector is never
                inactivating theses datas before this time is over
            >0
                old data could stay in the cache while new data wants
                to come, if no data is deprecated
            7200
                entries older than 2 hours will be thrown to make
                some place
            0
                emptying full cache when full
        user_ttl
            same as above, for user cache
        gc_ttl
            this one is the same but you should note this prevents
            Garbage collecting after each source change.

    APC
        filters
            could be used to prevent some caching on specific files
            but it's better to cache often used files, isn't it?
            At least in production
        max_file_size
            factory default to 1M, files bigger than that won't be cached

    APC: various things
        write_lock
            if True only one process caching a same file
            (better than apc.slam_defense)
        file_update_protection
            "2" prevents caching half written files (by cp for example)
            by waiting x seconds for new files caching.
            set it to 0 if using only rsync or mv
        lazy_functions
            early versions of APC only
            optimisations from Facebook,
            adding a lazy loding capabilities, so you can parse a lot of
            files and only used things are cached
            NEED TO BE TESTED: DANGEROUS!!
        lazy_classes
            same as above


    MODULE XDEBUG::

        php_admin_value[xdebug.default_enable] =   xdebug_default_enable ;
        ; http://xdebug.org/docs/all_settings#collect_params (0|1|2|3|4)
        php_admin_value[xdebug.collect_params] = xdebug_collect_params  0;
        php_admin_value[xdebug.profiler_enable] = xdebug_profiler_enable ;
        php_admin_value[xdebug.remote_enable] = xdebug_remote_enable 0;
        php_admin_value[xdebug.remote_host] = xdebug_remote_host localhost;
        php_admin_value[
            xdebug.profiler_enable_trigger
        ] = xdebug_profiler_enable_trigger  0;
        php_admin_value[
            xdebug.profiler_output_name
        ] = xdebug_profiler_output_name  /cachegrind.out.%p;
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():

        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        www_reg = __salt__['mc_www.settings']()
        if grains['os'] in ['Ubuntu']:
            s_all = '-s ALL'
        else:
            s_all = ''

        if (
            __grains__.get('os', '') == 'Ubuntu' and
            LooseVersion(__grains__.get('osrelease', '0')) >= LooseVersion('16.04')
        ):
            php7_onward = True
            apc_install = 0
        else:
            php7_onward = False
            apc_install = 1

        phpdefaults = {
            's_all': s_all,
            'rotate': __salt__['mc_logrotate.settings']()['days'],
            'composer': (
                'http://downloads.sourceforge.net/project'
                '/makinacorpus/makina-states/'
                'composer-e77435cd0c984e2031d915a6b42648e7b284dd5c'
            ),
            'composer_sha1': '017a611cd72cc1878d3ca1db2c0cc7f0a5f58541',
            'fpm_pools': {},
            'timezone': 'Europe/Paris',
            'open_basedir': 1,
            'open_basedir_additions': '',
            'file_uploads': 1,
            'upload_max_filesize': www_reg['upload_max_filesize'],
            'max_input_vars': 500,
            'max_input_time': 300,
            'html_errors': 0,
            'define_syslog_variables': 1,
            'display_errors': 0,
            'display_startup_errors': 0,
            'log_errors': 1,
            'error_reporting': 6143,
            'memory_limit': '256M',
            'max_execution_time': 120,
            'session_auto_start': 1,
            'allow_url_fopen': 0,
            'session_gc_maxlifetime': 3600,
            'session_gc_probability': 1,
            'session_gc_divisor': 100,
            'custom_sessions_enabled': False,
            'session_save_handler': 'redis',
            'session_save_path': (
                'tcp://127.0.0.1:6379?weight=2&timeout=2.5, '
                'tcp://10.0.0.1:6379?weight=2'
            ),
            'fpm_chroot': False,
            'fpm_use_socket': True,
            'fpm_socket_name': 'fpm.sock',
            'fpm_listen_backlog': 128,
            'fpm_listen_allowed_clients': '127.0.0.1',
            'fpm_user': 'www-data',
            'fpm_group': 'www-data',
            'fpm_listen_mod': '0660',
            'fpm_statuspath': '/fpmstatus',
            'fpm_ping': '/ping',
            'fpm_pong': 'pong',
            'fpm_pool_nice_priority': -19,
            'fpm_request_terminate_timeout': '300s',
            'fpm_request_slowlog_timeout': '5s',
            'fpm_pm_max_requests': 500,
            'fpm_pm_max_children': 10,
            'fpm_pm_start_servers': 3,
            'fpm_pm_min_spare_servers': 3,
            'fpm_pm_max_spare_servers': 8,
            'fpm_clear_env': False,
            'opcache_install': 1,
            'opcache_enabled': 1,
            'opcache_enable_cli': 1,
            'opcache_memory_consumption': 64,
            'opcache_interned_strings_buffer': 8,
            'opcache_max_accelerated_files': 2000,
            'opcache_max_wasted_percentage': 5,
            'opcache_validate_timestamps': 1,
            'opcache_revalidate_freq': 2,
            'opcache_revalidate_path': 0,
            'opcache_use_cwd': 1,
            'opcache_save_comments': 1,
            'opcache_load_comments': 1,
            'opcache_fast_shutdown': 0,
            'opcache_enable_file_override': 1,
            'opcache_optimization_level': '0xffffffff',
            'opcache_blacklist_filename': '',
            'opcache_max_file_size': 0,
            'opcache_force_restart_timeout': 180,
            'opcache_error_log': '',
            'opcache_log_verbosity_level': 1,
            'apc_install': apc_install,
            'apc_enabled': 0,
            'apc_enable_cli': 0,
            'apc_shm_segments': 1,
            'apc_shm_size': '32M',
            'apc_mmap_file_mask': '/apc.shm.XXXXXX',
            'apc_rfc1867': 1,
            'apc_include_once_override': 1,
            'apc_canonicalize': 1,
            'apc_stat': 1,
            'apc_stat_ctime': 1,
            'apc_num_files_hint': 1000,
            'apc_user_entries_hint': 1000,
            'apc_ttl': 300,
            'apc_user_ttl': 300,
            'apc_gc_ttl': 0,
            'apc_filters': '-config.php-.ini',
            'apc_max_file_size': '5M',
            'apc_write_lock': 1,
            'apc_file_update_protection': '2',
            'apc_lazy_functions': '',
            'apc_lazy_classes': '',
            'xdebug_install': True,
            'xdebug_enabled': True,
            'xdebug_collect_params': 0,
            'xdebug_profiler_enable': 0,
            'xdebug_profiler_enable_trigger': False,
            'xdebug_remote_enable': 0,
            'xdebug_remote_host': 'localhost',
            'xdebug_profiler_output_name': '/cachegrind.out.%p'
        }

        # now filter defaults with dev/prod alterations
        phpStepTwo = __salt__['grains.filter_by']({
            'dev': {
            },
            'prod': {
                'memory_limit': '256M',
                'fpm_pm_max_requests': 1000,
                'fpm_pm_max_children': 50,
                'fpm_pm_start_servers': 10,
                'fpm_pm_min_spare_servers': 10,
                'fpm_pm_max_spare_servers': 10,
                'modules_opcache_memory_consumption': 64,
                'modules_opcache_enable_file_override': 0,
                'modules_opcache_validate_timestamps': 1,
                # modules_opcache_ 15 min before checking for changes
                'modules_opcache_revalidate_freq': 900,
                'modules_apc_shm_size': '64M',
                'modules_apc_stat': False,
                'modules_apc_stat_ctime': False,
                'modules_apc_filters': '',
                'modules_xdebug_install': False,
                'modules_xdebug_enabled': False,
            }},
            grain='default_env',
            merge=phpdefaults,
            default='dev'
        )
        apacheSettings = __salt__['mc_apache.settings']()

        # Default OS-based paths settings added on phpData
        phpStepThree = __salt__['grains.filter_by']({
            'Debian': {
                'packages': {
                    'main': 'php5',
                    'mod_fcgid': apacheSettings['mod_packages']['mod_fcgid'],
                    'mod_fastcgi': (
                        apacheSettings['mod_packages']['mod_fastcgi']),
                    'mod_php': 'libapache2-mod-php5',
                    'mod_php_filter': 'libapache2-mod-php5filter',
                    'php5_cgi': 'php5-cgi',
                    'php_fpm': 'php5-fpm',
                    'apc': 'php-apc',
                    'cli': 'php5-cli',
                    'cas': 'php-cas',
                    'imagemagick': 'php5-imagick',
                    'memcache': 'php5-memcache',
                    'memcached': 'php5-memcached',
                    'mysql': 'php5-mysql',
                    'postgresql': 'php5-pgsql',
                    'sqlite': 'php5-sqlite',
                    'pear': 'php-pear',
                    'soap': 'php-soap',
                    'dev': 'php5-dev',
                    'snmp': 'php5-snmp',
                    'xmlrpc': 'php5-xmlrpc',
                    'json': 'php5-json',
                    'xdebug': 'php5-xdebug',
                    'curl': 'php5-curl',
                    'gd': 'php5-gd',
                    'ldap': 'php5-ldap',
                    'mcrypt': 'php5-mcrypt',
                },
                'ppa_ver': '5.6',
                'service': 'php5-fpm',
                'etcdir': locations['conf_dir'] + '/php5',
                'confdir': locations['conf_dir'] + '/php5/mods-available',
                'logdir': locations['var_log_dir'] + '/php',
                'fpm_sockets_dir': (
                    locations['var_lib_dir'] + '/apache2/fastcgi')
            }
        },
            grain='os_family',
            merge=phpStepTwo
        )
        if php7_onward:
            phpStepFour = __salt__['mc_utils.dictupdate'](
                phpStepThree, {
                'packages': {
                    'main': 'php',
                    'mod_fcgid': apacheSettings['mod_packages']['mod_fcgid'],
                    'mod_fastcgi': (
                        apacheSettings['mod_packages']['mod_fastcgi']),
                    'php_fpm': 'php-fpm',
                    'apc': 'php-apc',
                    'cli': 'php-cli',
                    'cas': 'php-cas',
                    'imagemagick': 'php-imagick',
                    'memcache': 'php-memcache',
                    'memcached': 'php-memcached',
                    'mysql': 'php-mysql',
                    'postgresql': 'php-pgsql',
                    'sqlite': 'php-sqlite',
                    'pear': 'php-pear',
                    'soap': 'php-soap',
                    'dev': 'php-dev',
                    'snmp': 'php-snmp',
                    'xmlrpc': 'php-xmlrpc',
                    'json': 'php-json',
                    'xdebug': 'php-xdebug',
                    'curl': 'php-curl',
                    'gd': 'php-gd',
                    'ldap': 'php-ldap',
                    'mcrypt': 'php-mcrypt',
                },
                'ppa_ver': '7.0',
                'service': 'php-fpm',
                'etcdir': locations['conf_dir'] + '/php/7.0',
                'confdir': locations['conf_dir'] + '/php/7.0/mods-available',
                'logdir': locations['var_log_dir'] + '/phpfpm',
                'fpm_sockets_dir': (
                    locations['var_lib_dir'] + '/apache2/fastcgi')
            }
        )

        # FINAL STEP: merge with data from pillar and grains
        phpData = __salt__['mc_utils.defaults'](
            'makina-states.services.php', phpStepFour)
        # retro compat
        if 'register-pools' in phpData:
            phpData['fpm_pools'] = __salt__[
                'mc_utils.dict_update'](
                    phpData['fpm_pools'], phpData['register-pools'])
        if not phpData['fpm_pools'].get('localhost',
                                        {}):
            phpData['fpm_pools']['localhost'] = {
                'doc_root': '/var/www/default'
            }
        return phpData
    return _settings()


def get_fpm_socket_name(project):
    settings = __salt__['mc_php.settings']()
    project = __salt__['mc_project.gen_id'](project)
    return '{0}.{1}'.format(project,
                            settings['fpm_socket_name'])




def _composer_infos(composer='/usr/local/bin/composer'):
    '''
    Extract informations from installed composer
    '''
    ret = {'status': False, 'msg': ''}
    if not os.path.exists(composer):
        ret['msg'] = '{0}: File not Found.'.format(composer)
        return ret

    cmd = '"{0}" --version'.format(composer)
    result = __salt__['cmd.run_all'](cmd, python_shell=True, runas='root')
    retcode = result['retcode']
    if retcode == 0:
        ret['version'] = result['stdout']
    else:
        raise exceptions.CommandExecutionError(result['stderr'])

    cmd = '"{0}" list --raw'.format(composer)
    result = __salt__['cmd.run_all'](cmd, python_shell=True, runas='root')
    retcode = result['retcode']
    commandlines = []
    commands = {}
    if retcode == 0:
        commandlines = result['stdout'].split("\n")
    else:
        raise exceptions.CommandExecutionError(result['stderr'])
    for line in commandlines:
        parts = line.split()
        if len(parts) > 0:
            commands[parts[0]] = ' '.join(parts[1:])
    ret['commands'] = commands
    ret['status'] = True

    return ret


def composer_command(command=None, cwd=None, args=None, composer=None):
    '''
    Run a composer command.
    Result of the command is in the 'msg' key of the returnded dictionnary

    composer
        full path to composer, defaulting to '/usr/local/bin/composer'

    command
        the command you want in composer.

    args
       string of command arguments, optionnal
    '''
    ret = {'status': False, 'msg': ''}

    if not composer:
        composer = '/usr/local/bin/composer'
    if not args:
        args = ''

    if not cwd:
        ret['status'] = False
        ret['msg'] = 'Composer command needs a working directory (cwd).'
        return ret

    if not os.path.exists(cwd):
        ret['status'] = False
        ret['msg'] = 'Given working directory ({0}) does not exists.'.format(
            cwd)
        return ret

    infos = _composer_infos(composer)
    if not infos['status']:
        ret['msg'] = '"{0}": Composer infos are not available. {1}'.format(
            infos['status'],
            infos['msg'])
        return ret

    commands = infos['commands']
    if not command or command not in commands.keys():
        ret['msg'] = '"{0}": unknown command for composer'.format(command)
        return ret

    cmd = '"{0}" {1} {2}'.format(composer, command, args)
    result = __salt__['cmd.run_all'](cmd, cwd=cwd, python_shell=True, runas='root')

    retcode = result['retcode']
    ret['msg'] = result['stdout']
    if retcode == 0:
        ret['status'] = True

    return ret


def fpmpool_settings(domain, doc_root, **kw):
    '''Generate options to be given for the pool configuration generation
    Some on the main options:

    session_cookie_domain
        Special cookie domain string for cookies (totally optionnal)
    listen
        Custom listen string for php fpm listen directive
        For example, if you do not want to use the default sockets scheme
    pool_name
        force the fpm pool name (useful for multiple projects
        to use the same pool)
    chroot
        Do we run in a fpm chrooted env.
        (certainly defaults to true in current layout)
    active
        True by default, set to False to disable the
        Virtualhost even if it will be generated.
    '''
    www_reg = copy.deepcopy(__salt__['mc_www.settings']())
    default_mode = 'production'
    if __salt__['mc_nodetypes.is_devhost']():
        default_mode = 'dev'
    kw['domain'] = domain
    kw['docroot'] = kw['doc_root'] = doc_root
    project_root = kw.setdefault('project_root', os.path.dirname(doc_root))
    kw['pool_root'] = project_root
    pool_name = kw.setdefault('pool_name',
                              domain.replace('.', '_'))
    kw.setdefault(
        'socket_name',
        __salt__['mc_php.get_fpm_socket_name'](pool_name))
    kw.setdefault(
        'pool_template_source',
        'salt://makina-states/files/etc/php5'
        '/fpm/pool.d/pool.conf')
    kw.setdefault('mode', default_mode)
    chroot = kw.setdefault('chroot', False)
    if chroot and not doc_root.startswith(project_root):
        chroot = False
    kw['chroot'] = chroot
    private_dir = kw.setdefault(
        'private_dir', '{0}/{1}'.format(project_root, "private"))
    log_dir = kw.setdefault(
        'log_dir', '{0}/{1}'.format(project_root, "log"))
    tmp_dir = kw.setdefault(
        'tmp_dir', '{0}/{1}'.format(project_root, "tmp"))

    sessions_dir = kw.setdefault(
        'sessions_dir', '{0}/{1}'.format(tmp_dir, "sessions"))
    kw.setdefault('session_cookie_domain', domain)
    kw.setdefault(
        'listen',
        os.path.join(www_reg['socket_directory'],
                     kw['socket_name']))
    open_basedir = [".", "..", doc_root, "/tmp",
                    tmp_dir, private_dir, log_dir,
                    sessions_dir]
    include_path = [".", "..", doc_root,
                    os.path.join(doc_root, 'include'),
                    "/usr/lib/php5/20121212"]
    for glob_inc in ['/usr/lib/php5']:
        if os.path.exists(glob_inc):
            for i in os.listdir(glob_inc):
                if os.path.isdir(i):
                    include_path.append(
                        os.path.join(glob_inc, i))

    custom_open_basedir = kw.pop('open_basedir', '')
    if custom_open_basedir and not isinstance(custom_open_basedir, list):
        custom_open_basedir = custom_open_basedir.split(':')
    if isinstance(custom_open_basedir, list):
        open_basedir.extend(custom_open_basedir)
    open_basedir = [a for a in open_basedir if a.strip()]

    custom_include_path = kw.pop('include_path', '')
    if custom_include_path and not isinstance(custom_include_path, list):
        custom_include_path = custom_include_path.split(':')
    if isinstance(custom_include_path, list):
        include_path.extend(custom_include_path)
    include_path = [a for a in include_path if a.strip()]
    if open_basedir:
        kw['open_basedir'] = ":".join(
            __salt__['mc_utils.uniquify'](open_basedir))
    if include_path:
        kw['include_path'] = ":".join(
            __salt__['mc_utils.uniquify'](include_path))
    phpData = __salt__['mc_utils.dictupdate'](
        copy.deepcopy(__salt__['mc_php.settings']()), kw)
    return phpData
#
