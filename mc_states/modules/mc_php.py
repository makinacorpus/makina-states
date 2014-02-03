# -*- coding: utf-8 -*-
'''
Management of PHP, Makina Corpus version
============================================

If you alter this module and want to test it, do not forget to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_php

'''

# Import python libs
import logging
import mc_states.utils


__name = 'php'

log = logging.getLogger(__name__)


def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        '''
        This is called from mc_services, loading all PHP default settings

        Settings are merged with grains and pillar via mc_utils.defaults

        PHP Fine Settings ------------------------------------------------
        -------- MODULE ZEND OPCACHE --------------------------
        replacement for APC!
        @see for details of options:
        https://raw.github.com/zendtech/ZendOptimizerPlus/master/README

        -------- MODULE APC ---------------------------------
        WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
        WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
        WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
        WARNING : APC is somewhat deprecated and Zend opcache is the replacment
        So the default behavior will not be to install it!!!

        APC: General shared settings

            shm_segments
              seems to perform better with only one shared segment
              but if you cannot upgrade this segment size, then create several
              setting ignored in mmap mode
              (so chances are this will always be 1)

        shm_size
            so here the segment size, but you may need to allow it in your OS
            for 128M Put in /etc/sysctl.conf::

                * kernel.shmmax=134217728
                * kernel.shmall=2097152

            default in most OS is 32M

        mmap_file_mask
            If compiled with MMAP support by using --enable-mmap this is the
            mktemp-style file_mask to pass to the mmap module
            for determining whether your mmap'ed memory region is going to be
            file-backed or shared memory backed

        APC:
            Per virtualhost/php-fpm pool:
                enabled
                    enabling apc

                rfc1867
                    allow progress upload bars

        APC
            want to gain speed? ------------------

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

        APC: cache lifetime managmenent ----------------
            ttl
                time (s) we can stay on the cache even when the cache is full
                -- Cache full count -- that means Garbage Collector is never
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

        APC: What to cache ? ----------------------------

            filters
                could be used to prevent some caching on specific files
                but it's better to cache often used files, isn't it?
                At least in production

            max_file_size
                factory default to 1M, files bigger than that won't be cached

        APC: various things -------------------------------

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


        MODULE XDEBUG ----------------------------------------
        php_admin_value[xdebug.default_enable] =   xdebug_default_enable ;
        ; http://xdebug.org/docs/all_settings#collect_params (0|1|2|3|4)
        php_admin_value[xdebug.collect_params] = xdebug_collect_params  0;
        php_admin_value[xdebug.profiler_enable] = xdebug_profiler_enable ;
        php_admin_value[
            xdebug.profiler_enable_trigger
        ] = xdebug_profiler_enable_trigger  0;
        php_admin_value[
            xdebug.profiler_output_name
        ] = xdebug_profiler_output_name  /cachegrind.out.%p;
        '''
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locations = localsettings['locations']

        phpdefaults = {
            'register-pools': {},
            'timezone': 'Europe/Paris',
            'open_basedir': True,
            'open_basedir_additions': '',
            'file_uploads': True,
            'upload_max_filesize': '5M',
            'max_input_vars': 500,
            'max_input_time': 300,
            'display_errors': False,
            'error_reporting': 6143,
            'memory_limit': '32M',
            'max_execution_time': 120,
            'allow_url_fopen': 0,
            'session': {
                'gc_maxlifetime': 3600,
                'gc_probability': 1,
                'gc_divisor': 100,
                'auto_start': 0,
            },
            'custom_sessions': {
                'enabled': False,
                'save_handler': 'redis',
                'save_path': (
                    'tcp://127.0.0.1:6379?weight=2&timeout=2.5, '
                    'tcp://10.0.0.1:6379?weight=2'
                ),
            },
            'fpm': {
                'chroot': False,
                'use_socket': True,
                'socket_relative_path': 'var/fcgi',
                'socket_name': 'fpm.sock',
                'listen_backlog': 128,
                'listen_allowed_clients': '127.0.0.1',
                'phpuser': 'www-data',
                'phpgroup': 'www-data',
                'listen_mod': '0660',
                'statuspath': '/fpmstatus',
                'ping': '/ping',
                'pong': 'pong',
                'request_terminate_timeout': '300s',
                'request_slowlog_timeout': '5s',
                'pm': {
                    'max_requests': 500,
                    'max_children': 10,
                    'start_servers': 3,
                    'min_spare_servers': 3,
                    'max_spare_servers': 8
                }
            },
            'modules': {
                'opcache': {
                    'install': True,
                    'enabled': True,
                    'enable_cli': True,
                    'memory_consumption': 64,
                    'interned_strings_buffer': '4',
                    'max_accelerated_files': 2000,
                    'max_wasted_percentage': 5,
                    'use_cwd': 1,
                    'validate_timestamps': 1,
                    'revalidate_freq': 2,
                    'revalidate_path': 0,
                    'save_comments': 0,
                    'load_comments': 0,
                    'fast_shutdown': 0,
                    'enable_file_override': 1,
                    'optimization_level': '0xffffffff',
                    'blacklist_filename': '',
                    'max_file_size': '0',
                    'force_restart_timeout': '180',
                    'error_log': '',
                    'log_verbosity_level': '1',
                    'interned_strings_buffer': '8'
                },
                'apc': {
                    'install': True,
                    'enabled': False,
                    'enable_cli': False,
                    'shm_segments': 1,
                    'shm_size': '16M',
                    'mmap_file_mask': '/apc.shm.XXXXXX',
                    'rfc1867': True,
                    'include_once_override': True,
                    'canonicalize': True,
                    'stat': True,
                    'stat_ctime': True,
                    'num_files_hint': 1000,
                    'user_entries_hint': 1000,
                    'ttl': 300,
                    'user_ttl': 300,
                    'gc_ttl': 0,
                    'filters': '-config.php-.ini',
                    'max_file_size': '5M',
                    'write_lock': True,
                    'file_update_protection': '2',
                    'lazy_functions': '',
                    'lazy_classes': ''
                },
                'xdebug': {
                    'install': True,
                    'enabled': True,
                    'collect_params': False,
                    'profiler_enable': False,
                    'profiler_enable_trigger': False,
                    'profiler_output_name': '/cachegrind.out.%p'
                }
            }
        }

        # now filter defaults with dev/prod alterations
        phpStepTwo = __salt__['grains.filter_by']({
            'dev': {
            },
            'prod': {
                'memory_limit': '64M',
                'fpm': {
                    'pm': {
                        'max_requests': 1000,
                        'max_children': 50,
                        'start_servers': 10,
                        'min_spare_servers': 10,
                        'max_spare_servers': 10
                    }
                },
                'modules': {
                    'opcache': {
                        'memory_consumption': 64,
                        'enable_file_override': 0,
                        'validate_timestamps': 1,
                        # 15 min before checking for changes
                        'revalidate_freq': 900,
                    },
                    'apc': {
                        'shm_size': '64M',
                        'stat': False,
                        'stat_ctime': False,
                        'filters': '',
                    },
                    'xdebug': {
                        'install': False,
                        'enabled': False,
                    }
                }
            }
        },
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
                    'mod_php': 'libapache2-mod-php5',
                    'mod_php_filter': 'libapache2-mod-php5filter',
                    'php5_cgi': 'php5-cgi',
                    'php_fpm': 'php5-fpm',
                    'apc': 'php-apc',
                    'cli': 'php-cli',
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

        # FINAL STEP: merge with data from pillar and grains
        phpData = __salt__['mc_utils.defaults'](
            'makina-states.services.php', phpStepThree)

        if grains['os'] in ['Ubuntu']:
            phpData['s_ALL'] = '-s ALL'
        else:
            phpData['s_ALL'] = ''

        return phpData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
