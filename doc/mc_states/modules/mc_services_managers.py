# -*- coding: utf-8 -*-

'''
.. _module_mc_services_managers:

mc_services_managers / servives managers registries & functions
=================================================================



'''

# Import salt libs
import os
import logging
import mc_states.api
from salt.ext import six as six


__name = 'services_managers'
six = mc_states.api.six
PREFIX = 'makina-states.{0}'.format(__name)
logger = logging.getLogger(__name__)


def metadata():
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](__name, bases=['services'])
    return _metadata()


def registry():
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _registry():
        data = __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={'supervisor': {'active': False},
                            'circus': {'active': False},
                            'system': {'active': False}}
        return data
    return _registry()


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
        DEFAULTS = {
            #  one of None | system | circus | supervisor
            #  None means no service
            'processes_managers': ['system', 'circus', 'supervisor'],
            'processes_manager': processes_manager}
        data = _s['mc_utils.defaults'](PREFIX, DEFAULTS)
        return data
    return _settings()


def processes_managers():
    return settings()['processes_managers']


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
    if not (has_system_services_manager or pm not in ['system', 'forced']):
        return
    if enable_toggle is None:
        enable_toggle = True
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
