# -*- coding: utf-8 -*-

'''
mc_services / servives registries & functions
==============================================

'''

# Import salt libs
import mc_states.utils

__name = 'services'



def metadata():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings'])
    return _metadata()


def settings():
    '''
    Global services registry

    resolver
        TDB
    locs
        TDB
    sshServerSettings
        TDB
    sshClientSettings
        TDB
    lxcSettings
        TDB
    apacheSettings
        TDB
    circusSettings
        TDB
    etherpadSettings
        TDB
    nginxSettings
        TDB
    phpSettings
        TDB
    rdiffbackupSettings
        TDB
    dbsmartbackupSettings
        TDB
    ntpEn
        TDB
    upstart
        TDB

    Pure ffpd:
        pureftpdRreg
            TDB
        pureftpdSettings
            TDB
        pureftpdDefaultSettings
            TDB

    Postgresql:
        pgSettings
            TDB
        pgDbs
            TDB
        postgresqlUsers
            TDB
        defaultPgVersion
            TDB
        pgVers
            TDB
        postgisVers
            TDB
        postgisDbName
            TDB
        postgresqlUser
            TDB

    Shorewall:
        shorewall
            All the shorewall registry
        shw_enabled
            TDB
        shwIfformat
            TDB
        shwPolicies
            TDB
        shwZones
            TDB
        shwInterfaces
            TDB
        shwParams
            TDB
        shwMasqs
            TDB
        shwRules
            TDB
        shwDefaultState
            TDB
        shwData
            TDB

    mysql:
        mysqlSettings
            TDB
        myCnf
            TDB
        myDisableAutoConf
            TDB

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        resolver = __salt__['mc_utils.format_resolve']
        metadata = __salt__['mc_{0}.metadata'.format(__name)]()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        localsettings = __salt__['mc_localsettings.settings']()
        pillar = __pillar__
        grains = __grains__
        locs = localsettings['locations']
        data = {}
        data['resolver'] = resolver
        data['locs'] = locs
        # localsettings shortcuts
        for i in ['SSLSettings', 'ldapVariables', 'ldapEn']:
            data[i] = localsettings[i]

        # SSHD Settings
        data['sshServerSettings'] = __salt__['mc_ssh.settings']()['server']

        # SSH
        data['sshClientSettings'] = __salt__['mc_ssh.settings']()['client']

        # lxc:  (services.virt.lxc)
        data['lxcSettings'] = __salt__['mc_lxc.settings']()

        # Apache:  (services.http.apache)
        data['apacheSettings'] = __salt__['mc_apache.settings']()

        # Circus:  (services.monitoring.circus)
        data['circusSettings'] =  __salt__['mc_circus.settings']()

        # Etherpad:  (services.collab.etherpad)
        data['etherpadSettings'] = __salt__['mc_etherpad.settings']()

        # Nginx:  (services.http.nginx)
        data['nginxSettings'] = __salt__['mc_nginx.settings']()

        # PHP:  (services.http.nginx)
        data['phpSettings'] = __salt__['mc_php.settings']()

        # Pureftpd:  (services.ftp.pureftpd)
        data['pureftpdRreg'] = pureftpd = __salt__['mc_pureftpd.settings']()
        data['pureftpdSettings'] = pureftpd['conf']
        data['pureftpdDefaultSettings'] = pureftpd['defaults']

        # PostGRESQL:  (services.db.postgresql)
        # default postgresql/ grains configured databases (see service doc)
        data['pgSettings'] = pgSettings = __salt__['mc_pgsql.settings']()
        data['pgDbs'] = pgSettings['pgDbs']
        data['postgresqlUsers'] = pgSettings['postgresqlUsers']
        data['defaultPgVersion'] = pgSettings['defaultPgVersion']
        data['pgVers'] = pgSettings['versions']
        data['postgisVers'] = pgSettings['postgis']
        data['postgisDbName'] = pgSettings['postgis_db']
        data['postgresqlUser'] = pgSettings['user']

        # shorewall pillar parsing
        data['shorewall'] = __salt__['mc_shorewall.settings']()
        for i in ['shw_enabled', 'shwIfformat', 'shwPolicies', 'shwZones',
                  'shwInterfaces', 'shwParams', 'shwMasqs', 'shwRules',
                  'shwDefaultState', 'shwData']:
            data[i] = data['shorewall'][i]

        # mysql
        data['mysqlSettings'] = mysqlSettings = __salt__['mc_mysql.settings']()
        data['myCnf'] = mysqlSettings['myCnf']
        data['myDisableAutoConf'] = mysqlSettings['noautoconf']

        # Rdiff backup
        data['rdiffbackupSettings'] = __salt__['mc_utils.defaults'](
            'makina-states.services.backup.rdiff-backup', {})
        #
        data['dbsmartbackupSettings'] = __salt__['mc_dbsmartbackup.settings']()

        # ntp is not applied to LXC containers ! (services.base.ntp)
        # So we just match when our grain is set and not have a value of lxc
        data['ntpEn'] = (
            not (
                ('dockercontainer' in nodetypes_registry['actives'])
                or ('lxccontainer' in nodetypes_registry['actives'])
            ))
        # init systems flags
        data['upstart'] = __salt__['mc_utils.get']('makina-states.upstart', False)
        return data
    return _settings()


def registry():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        settings_reg = __salt__['mc_{0}.settings'.format(__name)]()
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'backup.bacula-fd': {'active': False},
            'backup.rdiff-backup': {'active': False},
            'backup.dbsmartbackup': {'active': False},
            'base.ntp': {'active': settings_reg['ntpEn']},
            'base.ssh': {'active': True},
            'db.mysql': {'active': False},
            'db.postgresql': {'active': False},
            'firewall.shorewall': {'active': False},
            'ftp.pureftpd': {'active': False},
            'gis.postgis': {'active': False},
            'gis.qgis': {'active': False},
            'http.apache': {'active': False},
            'java.solr4': {'active': False},
            'java.tomcat7': {'active': False},
            'mail.dovecot': {'active': False},
            'mail.postfix': {'active': False},
            #'php.common': {'active': False},
            'php.modphp': {'active': False},
            'php.phpfpm': {'active': False},
            'http.apache_modfcgid': {'active': False},
            'http.apache_modfastcgi': {'active': False},
            'php.phpfpm_with_apache': {'active': False},
            'virt.docker': {'active': False},
            'virt.docker-shorewall': {'active': False},
            'virt.lxc': {'active': False},
            'virt.lxc-shorewall': {'active': False},
            'mastersalt_minion': {'active': False},
            'mastersalt_master': {'active': False},
            'mastersalt': {'active': False},
            'salt_minion': {'active': False},
            'salt_master': {'active': False},
            'salt': {'active': False},
        })
    return _registry()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
