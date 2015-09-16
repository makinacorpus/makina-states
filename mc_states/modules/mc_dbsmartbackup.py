# -*- coding: utf-8 -*-
'''
.. _module_mc_dbsmartbackup:

mc_dbsmartbackup / db_smart_backup functions
============================================

'''
# Import salt libs
import mc_states.api

__name = 'dbsmartbackup'

def settings():
    '''
    Configuration registry for dbsmartbackup (https://github.com/kiorky/db_smart_backup)

    cron_activated
        toggle on/off the nightly cron
    cron_hour
        which hour of the day do we run the script

    cron_minute
        which minute of the day do we run the script

    backup_path_prefix
        root level dir for the backup storage

    dbexclude
        exclude some databases from the backup

    dbnames
        select databases to backup (default: all)

    disable_mail
        to disable the summary email

    global_backup
        do we also store the global objects and privileges (default: 1)

    owner
        owner of the files

    group
        group of the backup files

    keep_days
        how many days to keep

    keep_lasts
        how many 'last' backups to leep

    keep_logs
        how many logs to keep

    keep_monthes
        how many monthes to keep
    keep_weeks': '8',
        how many weeks to keep

    mail
        summary email recipient

    mysqldump_autocommit
        do we use mysqldump autocommit

    mysqldump_completeinserts

    mysqldump_debug

    mysqldump_locktables

    mysqldump_noroutines

    mysqldump_no_single_transaction

    mysql_password
        mysql root password

    mysql_sock_paths
        list of directories where to find mysql socket

    mysql_use_ssl
        do we use ssl to connect to mysql

    mongodb_path
        path to mongodb
    mongodb_user
        mongodb admin
    mongodb_password
        mongodb admin password



    servername
        servername tied to those backups
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        mongoSettings = __salt__['mc_mongodb.settings']()
        mysqlSettings = __salt__['mc_mysql.settings']()
        pillar = __pillar__
        locs = __salt__['mc_locations.settings']()
        env = __salt__['mc_env.settings']()['env']
        cron_activated = True
        if env not in ['prod', 'staging']:
            cron_activated = False
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.backup.db_smart_backup', {
                'cron_activated': cron_activated,
                'cron_minute': '1',
                'types': ['mongod', 'slapd', 'mysql', 'postgresql', 'elasticsearch'],
                'backup_path_prefix': locs['srv_dir'] + '/backups',
                'cron_hour': '1',
                'dbexclude': '',
                'dbnames': 'all',
                'disable_mail': '',
                'global_backup': '',
                'es_global_backup': '',
                'global_backup': '1',
                'mongodb_path': '/var/lib/mongodb',
                'group': 'root',
                'keep_days': '14',
                'keep_lasts': '24',
                'keep_logs': '60',
                'keep_monthes': '12',
                'keep_weeks': '8',
                'mail': 'root@localhost',
                'mysqldump_autocommit': '1',
                'mysqldump_completeinserts': '1',
                'mysqldump_debug': '',
                'mysqldump_locktables': '',
                'mysqldump_noroutines': '',
                'mysqldump_no_single_transaction': '',
                'mongodb_user': mongoSettings['admin'],
                'mongodb_password': mongoSettings['password'],
                'mysql_password': mysqlSettings['root_passwd'],
                'mysql_sock_paths': mysqlSettings['sockdir'] + '/mysqld.sock',
                'mysql_use_ssl': '',
                'owner': 'root',
                'servername': __grains__['fqdn'],
            }
        )
        return data
    return _settings()



#
