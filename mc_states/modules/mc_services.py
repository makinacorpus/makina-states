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
from salt.ext import six as six


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


def get_service_function(pm=None,
                         enable_toggle=None,
                         has_system_services_manager=None,
                         activate_function='service.running',
                         deactivate_function='service.dead'):
    '''
    Return the appropriate service function for the activated process manager
    For the API conveniance, we reflect back any service.function.
    If pm is system, or manually forced, we want to return the appropriate
    service function (one of: activate_function/deactivate_function).
    We take care to check not to return any function when we are in a docker
    hence we do not have any system level function, nor the access to the service
    module

        pm
            the processes manager
            (one of none|forced|system|circus|supervisor|service.{running,dead})
            system or forced means to return a function between activate or deactivate
        enable_toggle
            choose if we are in system mode either to return the 'activate' or 'deactivate'
            function, by default we return the activate function
        activate_function
            salt module function to activate a service (api compatible with service.*)
        deactivate_function
            salt module function to deactivate a service (api compatible with service.*)
        has_system_services_manager
            overrides the makina-states detection of the presence of a system services
            manager

    '''
    _s = __salt__
    # pm is the service function, early return
    if isinstance(pm, six.string_types):
        for func in ['running', 'dead', 'absent']:
            if pm.endswith(func):
                return pm
    if pm is None:
        pm = 'system'
    if has_system_services_manager is None:
        has_system_services_manager = _s['mc_nodetypes.has_system_services_manager']()
    if enable_toggle is None:
        enable_toggle = True
    if not has_system_services_manager:
        return
    if pm not in ['system', 'forced']:
        return
    return enable_toggle and activate_function or deactivate_function


def get_service_enabled_state(pm=None, enable_toggle=None):
    '''
    Return if a service should be enabled at boot or not
    depending on the service function.

    if service func is 'running' -> enabled
    if service func is 'dead' -> disaabled
    '''
    service_function = get_service_function(pm, enable_toggle=enable_toggle)
    if not isinstance(service_function, six.string_types):
        service_function = ''
    return 'running'in service_function and True or False


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
