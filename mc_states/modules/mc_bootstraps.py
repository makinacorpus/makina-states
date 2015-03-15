# -*- coding: utf-8 -*-
'''
.. _module_mc_bootstraps:

mc_bootstraps / bootstraps related registry
============================================



'''

# Import salt libs
import mc_states.api

__name = 'bootstraps'


def metadata():
    '''metadata registry for bootstraps'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata']('bootstraps')
    return _metadata()


def settings():
    '''settings registry for bootstraps'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        data = {
            'metadata': saltmods['mc_{0}.metadata'.format(__name)](),
        }
        return data
    return _settings()


def registry():
    '''registry registry for bootstraps'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _registry():
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={})
    return _registry()
