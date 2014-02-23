# -*- coding: utf-8 -*-
'''

.. _module_mc_mysql:

mc_mysql / mysql functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'mysql'

log = logging.getLogger(__name__)


def settings():
    '''
    MySQL Fine Settings

    TODO: review this comment: when not in dev
    you MUST define AT LEAST mysql-default-settings.root_passwd
    in your PILLAR, else you'll have state failures

    isPercona
        TDB
    isOracle
        TDB
    isMariaDB
        TDB
    nb_connections
        TDB
    innodb_buffer_pool_size_M
        TDB
    query_cache_size_M
        TDB
    innodb_buffer_pool_instances
        TDB
    innodb_log_buffer_size_M
        TDB
    innodb_flush_method
        TDB
    innodb_thread_concurrency
        TDB
    sync_binlog
        TDB
    innodb_flush_log_at_trx_commit
        TDB
    innodb_additional_mem_pool_size_M
        TDB
    tmp_table_size_M
        TDB
    number_of_table_indicator
        TDB
    packages
        TBD
    service
        TBD
    port
        TBD
    user
        TBD
    group
        TBD
    root_passwd
        TBD
    sharedir
        TBD
    datadir
        TBD
    tmpdir
        TBD
    etcdir
        TBD
    logdir
        TBD
    basedir
        TBD
    sockdir
        TBD
    conn_host / conn_user / conn_pass
        Connection settings, user/pass/host used by salt
        to manage users, grants and database creations
    character_set
        default character set on CREATE DATABASE (use utf8' not 'utf-8')
    collate
        default collate on CREATE DATABASE
    noDNS
        Avoid name resolution on connections checks, must-have.
        This is the skip-name-resolv option
    memory_usage_percent
        the macro will compute magiccaly the settings to
        fit this percentage of full memory on the host. So by default it's 50%
        of all RAM on a dev envirronment and 85% for a production one where
        the MySQl server should be alone on a server. Then all others settings
        parameters in the 'tunning' key could be set to False to let the macro
        fill the gaps. If you set somtehing other than False for one of theses
        settings it will be used instead of the value computed by the macro,
        check the macro for details and comments on all theses parameters.
        Note the "_M" means Mo, so for 2Go of innodb_buffer_pool_size use
        2024, that is 2024Mo.
        Tweak the 'number_of_table_indicator' to adjust some settings
        automatically from that, for example several Drupal instances
        using a lot of fields
        could manage several hundreds of tables. <=== IMPORTANT
    myCnf
        MySQL default custom configuration (services.db.mysql)
        To override the default makina-states configuration file,
        Use the 'makina-states.services.mysql.cnf pillar/grain
    noautoconf
        disable mysql automatic configuration
        (if you want to call the mysql macros yourself
        (makina-states.services.mysql.noautoconf)
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locs = localsettings['locations']
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.db.mysql',
            __salt__['grains.filter_by'](
                {
                    'Debian': {
                        'packages': {
                            'main': 'mysql-server',
                            'dev': 'libmysqlclient-dev',
                            'python': 'python-mysqldb',
                            'php': 'php-mysql'
                        },
                        'service': 'mysql',
                        'port': '5432',
                        'user': 'mysql',
                        'group': 'mysql',
                        'root_passwd': '',
                        'sharedir': locs['share_dir'] + '/mysql',
                        'datadir': locs['var_lib_dir'] + '/mysql',
                        'tmpdir': locs['tmp_dir'],
                        'etcdir': locs['conf_dir'] + '/mysql/conf.d',
                        'logdir': locs['var_log_dir'] + '/mysql',
                        'basedir': locs['usr_dir'],
                        'sockdir': locs['var_run_dir'] + '/mysqld'
                    },
                    'RedHat': {},
                },
                merge=__salt__['grains.filter_by'](
                    {
                        'dev': {
                            'conn_host': 'localhost',
                            'myCnf': None,
                            'noautoconf': False,
                            'conn_user': 'root',
                            'conn_pass': '',
                            'character_set': 'utf8',
                            'collate': 'utf8_general_ci',
                            'noDNS': True,
                            'isPercona': False,
                            'isOracle': True,
                            'isMariaDB': False,
                            'memory_usage_percent': 15,
                            'nb_connections': 25,
                            'innodb_buffer_pool_size_M': False,
                            'query_cache_size_M': False,
                            'innodb_buffer_pool_instances': False,
                            'innodb_log_buffer_size_M': False,
                            'innodb_flush_method': 'O_DSYNC',
                            'innodb_thread_concurrency': False,
                            'sync_binlog': False,
                            'innodb_flush_log_at_trx_commit': 0,
                            'innodb_additional_mem_pool_size_M': False,
                            'tmp_table_size_M': False,
                            'number_of_table_indicator': 500
                        },
                        'prod': {
                            'myCnf': None,
                            'noautoconf': False,
                            'conn_host': 'localhost',
                            'conn_user': 'root',
                            'conn_pass': '',
                            'character_set': 'utf8',
                            'collate': 'utf8_general_ci',
                            'noDNS': True,
                            'isPercona': False,
                            'isOracle': True,
                            'isMariaDB': False,
                            'memory_usage_percent': 85,
                            'nb_connections': 250,
                            'innodb_buffer_pool_size': False,
                            'query_cache_size_M': False,
                            'innodb_buffer_pool_instances': False,
                            'innodb_log_buffer_size_M': False,
                            'innodb_flush_method': 'O_DIRECT',
                            'innodb_thread_concurrency': False,
                            'sync_binlog': False,
                            'innodb_flush_log_at_trx_commit': 2,
                            'innodb_additional_mem_pool_size_M': False,
                            'tmp_table_size_M': False,
                            'number_of_table_indicator': 1000
                        },
                    },
                    grain='default_env',
                    default='dev'
                ),
                grain='os_family'
            )
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
