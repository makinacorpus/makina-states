# -*- coding: utf-8 -*-

'''
.. _module_mc_services:

mc_cloud / cloud registries & functions
==============================================

'''

# Import salt libs
import mc_states.utils

__name = 'cloud'


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
        return data
    return _settings()


def registry():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'cloud.generic': {'active': False},
            'cloud.lxc': {'active': False},
            'cloud.saltify': {'active': False},
        })
    return _registry()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
