# -*- coding: utf-8 -*-

'''
.. _module_mc_services:

mc_services / servives registries & functions
=============================================



'''

# Import salt libs
import os
import logging
import mc_states.api

__name = 'services'
six = mc_states.api.six
PREFIX = 'makina-states.{0}'.format(__name)
logger = logging.getLogger(__name__)


def _bindEn(**kwargs):
    is_container = __salt__['mc_nodetypes.is_container']()
    return not is_container


def _rsyslogEn(**kwargs):
    return __grains__.get('os', '').lower() in ['ubuntu']


def _ulogdEn(**kwargs):
    is_container = __salt__['mc_nodetypes.is_container']()
    is_docker = __salt__['mc_nodetypes.is_docker']()
    ret = False
    if (
        __grains__['os'].lower() in ['ubuntu'] and
        __grains__.get('osrelease') >= '13.10'
    ):
        ret = is_container and not is_docker
    return ret


def _ntpEn(**kwargs):
    is_container = __salt__['mc_nodetypes.is_container']()
    return not is_container


def metadata():
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings'])
    return _metadata()


def settings():
    '''
    Global services registry
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        processes_manager = None
        is_docker = _s['mc_nodetypes.is_docker']()
        is_docker_service = _s['mc_nodetypes.is_docker_service']()
        if not is_docker:
            if not is_docker_service:
                processes_manager = 'system'
        if is_docker_service:
            processes_manager = 'circus'
        DEFAULTS = {
            #  one of None | system | circus | supervisor
            #  None means no service
            'processes_manager': processes_manager
        }
        data = _s['mc_utils.defaults'](PREFIX, DEFAULTS)
        return data
    return _settings()


def get_processes_manager(data=None):
    if not data:
        data = {}
    return data.get('processes_manager',
                    settings()['processes_manager'])


def toggle_service(pm='system'):
    if pm == 'system' or not __salt__['mc_nodetypes.is_docker']():
        return (pm == 'system') and 'running' or 'dead'


def toggle_enable(pm='system'):
    is_running = toggle_service(pm)
    return is_running == 'running' and True or False


def registry():
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _registry():
        # only some services will be fully done  on mastersalt side if any
        # in scratch mode, deactivating all default configuration for services
        true = not __salt__['mc_nodetypes.is_scratch']()
        allow_lowlevel_states = __salt__['mc_controllers.allow_lowlevel_states']()
        is_docker = __salt__['mc_nodetypes.is_docker']()
        is_travis = __salt__['mc_nodetypes.is_travis']()
        ids = __salt__['mc_nodetypes.is_docker_service']()
        # sshen = true and (ids or (allow_lowlevel_states and not is_docker))
        sshen = true and ((is_docker and ids) or allow_lowlevel_states)
        ntpen = _ntpEn() and true
        binden = _bindEn() and true and not is_travis
        rsyslogen = _rsyslogEn() and true
        ulogden = _ulogdEn() and true
        ntp_u = False
        vagrantvm = __salt__['mc_nodetypes.is_vagrantvm']() and true
        if __salt__['mc_nodetypes.is_container']():
            ntp_u = True
        if ntp_u:
            ntpen = False
        ntp_u = ntp_u and true
        ntpen = ntpen and true
        data = {'backup.bacula-fd': {'active': False},
                'backup.burp.server': {'active': False},
                'backup.burp.client': {'active': False},
                'backup.dbsmartbackup': {'active': False},
                'log.rsyslog': {'force': True, 'active': rsyslogen},
                'log.ulogd': {'force': True, 'active': ulogden},
                'base.ntp': {'force': True, 'active': ntpen},
                'base.ntp.uninstall': {'active': ntp_u},
                'base.dbus': {'force': True, 'active': not (is_travis or is_docker)},
                'base.ssh': {'force': True, 'active': sshen},
                'base.cron': {'force': True, 'active': true},
                'dns.dhcpd': {'active': False},
                'dns.bind': {'force': True, 'active': binden},
                'dns.slapd': {'active': False},
                'db.mongodb': {'active': False},
                'db.mysql': {'active': False},
                'db.postgresql': {'active': False},
                'firewall.fail2ban': {'active': sshen},
                'firewall.shorewall': {'active': False},
                'firewall.firewalld': {'active': False},
                'firewall.ms_iptables': {'active': False},
                'firewall.firewall': {'active': False},
                'firewall.psad': {'active': False},
                'ftp.pureftpd': {'active': False},
                'gis.postgis': {'active': False},
                'gis.ubuntgis': {'active': False},
                'gis.qgis': {'active': False},
                'http.nginx': {'active': False},
                'http.apache': {'active': False},
                'http.apache_modproxy': {'active': False},
                'http.apache_modfastcgi': {'active': False},
                'http.apache_modfcgid': {'active': False},
                'java.solr4': {'active': False},
                'java.tomcat7': {'active': False},
                'mail.dovecot': {'active': False},
                'mail.postfix': {'active': False},
                'monitoring.supervisor': {'active': False},
                'monitoring.circus': {'active': False},
                'monitoring.snmpd': {'active': False},
                'monitoring.client': {'active': False},
                # 'php.common': {'active': False},
                'proxy.haproxy': {'active': False},
                'queue.rabbitmq': {'active': False},
                'php.common': {'active': False},
                'php.modphp': {'active': False},
                'php.phpfpm': {'active': False},
                'php.phpfpm_with_apache': {'active': False},
                'cache.memcached': {'active': False},
                'virt.docker-shorewall': {'active': False},
                'virt.virtualbox': {'active': False},
                'virt.kvm': {'active': vagrantvm},
                'virt.lxc': {'active': vagrantvm},
                'virt.docker': {'active': vagrantvm},
                'virt.lxc-shorewall': {'active': False},
                'mastersalt_minion': {'active': False},
                'mastersalt_master': {'active': False},
                'mastersalt': {'active': False},
                'salt_minion': {'active': False},
                'salt_master': {'active': False},
                'salt': {'active': False}}
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        if 'laptop' in nodetypes_registry['actives']:
            data.update({
                'backup.burp.client': {'active': true},
                'virt.virtualbox': {'active': true},
                'virt.docker': {'active': true},
                'virt.lxc': {'active': true},
                'virt.kvm': {'active': true}})
        data = __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults=data)
        return data
    return _registry()
