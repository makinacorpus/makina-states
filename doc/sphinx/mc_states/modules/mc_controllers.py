# -*- coding: utf-8 -*-
'''
.. _module_mc_controllers:

mc_controllers / controllers related variables
================================================

'''

# Import salt libs
import os
import mc_states.api
import logging

log = logging.getLogger(__name__)
__name = 'controllers'


def metadata():
    '''controllers metadata registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings'])
    return _metadata()


@mc_states.api.no_more_mastersalt
def allow_lowlevel_states():
    return True


@mc_states.api.no_more_mastersalt
def masterless():
    return True


def settings():
    '''controllers settings registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        data = dict(metadata=saltmods['mc_{0}.metadata'.format(__name)]())
        return data
    return _settings()


def registry():
    '''controllers registry registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _registry():
        return  __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'salt': {'active': False},
        })
    return _registry()
