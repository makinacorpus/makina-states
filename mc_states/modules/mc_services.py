# -*- coding: utf-8 -*-

'''
.. _module_mc_services:

mc_services / servives registries & functions
==============================================

'''

# Import salt libs
import mc_states.utils

__name = 'services'

def _bindEn(__salt__):
    nodetypes_registry = __salt__['mc_nodetypes.registry']()
    return not (
        ('dockercontainer' in nodetypes_registry['actives'])
        or ('lxccontainer' in nodetypes_registry['actives'])
    )


def _ntpEn(__salt__):
    nodetypes_registry = __salt__['mc_nodetypes.registry']()
    return not (
        ('dockercontainer' in nodetypes_registry['actives'])
        or ('lxccontainer' in nodetypes_registry['actives'])
    )


def metadata():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings'])
    return _metadata()


def settings():
    '''
    Global services registry

    locs
        See :ref:`module_mc_localsettings`
    resolver
        See :ref:`module_mc_utils`
    bindSettings
        See :ref:`module_mc_bind`
    sshServerSettings
        See :ref:`module_mc_ssh`
    sshClientSettings
        See :ref:`module_mc_ssh`
    lxcSettings
        See :ref:`module_mc_lxc`
    apacheSettings
        See :ref:`module_mc_apache`
    postfixSettings
        See :ref:`module_mc_postfix`
    circusSettings
        See :ref:`module_mc_lxc`
    etherpadSettings
        See :ref:`module_mc_etherpad`
    nginxSettings
        See :ref:`module_mc_nginx`
    phpSettings
        See :ref:`module_mc_php`
    rdiffbackupSettings
        See :ref:`module_mc_rdiffbackup`
    dbsmartbackupSettings
        See :ref:`module_mc_dbsmartbackup`
    ntpEn
        is ntp active
    fail2ban
        See :ref:`module_mc_fail2ban`
    mysqlSettings:
        See :ref:`module_mc_mysql`
    upstart
        See are we using upstart
    tomcatSettings
        See :ref:`module_mc_tomcat`
    Pure ffpd:
        See :ref:`module_mc_pureftpd`
    Postgresql:
        See :ref:`module_mc_pgsql`
    Shorewall:
        See :ref:`module_mc_shorewall`


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

        # SSH Settings
        data['sshSettings'] = __salt__['mc_ssh.settings']()

        # lxc:  (services.virt.lxc)
        data['lxcSettings'] = __salt__['mc_lxc.settings']()

        # Apache:  (services.http.apache)
        data['apacheSettings'] = __salt__['mc_apache.settings']()

        # bind:  (services.dns.bind)
        data['bindSettings'] = __salt__['mc_bind.settings']()

        # Circus:  (services.monitoring.circus)
        data['circusSettings'] =  __salt__['mc_circus.settings']()

        # Snmpd: (services.monitoring.snmpd)
        data['snmpdSettings'] = __salt__['mc_snmpd.settings']()

        # psad:  (services.firewall.psdad)
        data['psadSettings'] =  __salt__['mc_psad.settings']()

        # Etherpad:  (services.collab.etherpad)
        data['etherpadSettings'] = __salt__['mc_etherpad.settings']()
        # fail2ban:  (services.firewall.fail2ban)
        data['fail2banSettings'] = __salt__['mc_fail2ban.settings']()

        # Postfix:  (services.mail.postfix)
        data['postfixSettings'] = __salt__['mc_postfix.settings']()

        # Nginx:  (services.http.nginx)
        data['nginxSettings'] = __salt__['mc_nginx.settings']()

        # PHP:  (services.php)
        data['phpSettings'] = __salt__['mc_php.settings']()

        # Tomcat:  (services.tomcat)
        data['tomcatSettings'] = __salt__['mc_tomcat.settings']()

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

        # mysql
        data['mysqlSettings'] = mysqlSettings = __salt__['mc_mysql.settings']()
        data['myCnf'] = mysqlSettings['myCnf']
        data['myDisableAutoConf'] = mysqlSettings['noautoconf']

        # Rdiff backup
        data['rdiffbackupSettings'] = __salt__['mc_rdiffbackup.settings']()

        # db_smart_backup
        data['dbsmartbackupSettings'] = __salt__['mc_dbsmartbackup.settings']()

        # ntp is not applied to LXC containers ! (services.base.ntp)
        # So we just match when our grain is set and not have a value of lxc
        data['ntpEn'] = _ntpEn(__salt__)
        # init systems flags
        data['upstart'] = __salt__['mc_utils.get'](
            'makina-states.upstart', False)
        return data
    return _settings()


def registry():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'backup.bacula-fd': {'active': False},
            'backup.rdiff-backup': {'active': False},
            'backup.dbsmartbackup': {'active': False},
            'base.ntp': {'active': _ntpEn(__salt__)},
            'base.ssh': {'active': True},
            'cloud.salt_cloud': {'active': False},
            'cloud.lxc': {'active': False},
            'cloud.saltify': {'active': False},
            'dns.bind': {'active': _bindEn(__salt__)},
            'db.mysql': {'active': False},
            'db.postgresql': {'active': False},
            'firewall.fail2ban': {'active': False},
            'firewall.shorewall': {'active': False},
            'firewall.psad': {'active': False},
            'ftp.pureftpd': {'active': False},
            'gis.postgis': {'active': False},
            'gis.qgis': {'active': False},
            'http.apache': {'active': False},
            'java.solr4': {'active': False},
            'java.tomcat7': {'active': False},
            'mail.dovecot': {'active': False},
            'mail.postfix': {'active': False},
            'monitoring.circus': {'active': False},
            'monitoring.snmpd': {'active': False},
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
