# -*- coding: utf-8 -*-
'''
Salt related variables
============================================

'''

# Import salt libs
import mc_states.utils

__name = 'controllers'


def metadata():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings'])
    return _metadata()

def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        resolver = saltmods['mc_utils.format_resolve']
        metadata = saltmods['mc_{0}.metadata'.format(__name)]()
        return locals()
    return _settings()


def registry():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        settings_reg = __salt__['mc_{0}.settings'.format(__name)]()
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
