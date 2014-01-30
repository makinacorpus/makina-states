# -*- coding: utf-8 -*-
'''
Salt related variables
============================================

'''

import unittest
# Import salt libs
import mc_states.utils

__name = 'bootstraps'


def metadata():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata(REG):
        return __salt__['mc_macros.metadata']('bootstraps')
    return _metadata()


def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings(REG):
        resolver = __salt__['mc_utils.format_resolve']
        metadata = __salt__['mc_bootstraps.metadata']()
        pillar = __pillar__
        grains = __grains__
        return locals()
    return _settings()


def registry():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry(REG):
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](settings, defaults={})
    return _registry()

def dump():
    return mc_states.utils.dump(__salt__, __name)

#
