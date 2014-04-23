# -*- coding: utf-8 -*-
'''
.. _module_mc_controllers:

mc_controllers / controllers related variables
================================================

'''

# Import salt libs
import os
import mc_states.utils

__name = 'controllers'


def metadata():
    '''controllers metadata registry'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings'])
    return _metadata()


def has_mastersalt():
    has_mastersalt = False
    try:
        with open('/etc/makina-states/mode') as fic:
            has_mastersalt = 'mastersalt' in fic.read()
    except Exception:
        pass
    if not has_mastersalt:
        has_mastersalt = os.path.exists('/etc/mastersalt')
    if not has_mastersalt:
        has_mastersalt = os.path.exists('/usr/bin/mastersalt')
    return has_mastersalt


def mastersalt_mode():
    return (
        (has_mastersalt() 
         and 'mastersalt' in __salt__['mc_utils.get']('config_dir'))
        or (not has_mastersalt() 
            and not 'mastersalt' in __salt__['mc_utils.get']('config_dir')))


def settings():
    '''controllers settings registry'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        data = dict(resolver=saltmods['mc_utils.format_resolve'],
                    metadata=saltmods['mc_{0}.metadata'.format(__name)]())
        return data
    return _settings()


def registry():
    '''controllers registry registry'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        has_m = has_mastersalt()
        return  __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
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
