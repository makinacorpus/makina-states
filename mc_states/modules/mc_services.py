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
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        pillar = __pillar__
        grains = __grains__
        data = {}
        # mysql
        data['mysqlSettings'] = mysqlSettings = __salt__['mc_mysql.settings']()
        data['myCnf'] = mysqlSettings['myCnf']
        data['myDisableAutoConf'] = mysqlSettings['noautoconf']
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
            'cloud.lxc': {'active': False},
            'cloud.computenode': {'active': False},
            'cloud.cloudcontroller': {'active': False},
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
            'proxy.haproxy': {'active': False},
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
