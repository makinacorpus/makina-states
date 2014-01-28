# -*- coding: utf-8 -*-
'''
Salt related variables
============================================

'''

import unittest
# Import salt libs
import salt.utils
import os
import salt.utils.dictupdate
import salt.utils

__name = 'bootstraps'


def _metadata(REG):
    return __salt__['mc_macros.metadata']('bootstraps')


def get_reg():
    return __salt__['mc_macros.registry_kind_get'](__name)


def set_reg(reg):
    return __salt__['mc_macros.registry_kind_set'](__name, reg)


def metadata():
    REG = get_reg()
    ret = REG.setdefault('metadata', _metadata(REG))
    set_reg(REG)
    return ret


def _settings(REG):
    resolver = salt['mc_utils.format_resolve']
    metadata = salt['mc_bootstraps.metadata']()
    pillar = __pillar__
    grains = __grains__
    return locals()


def settings():
    REG = get_reg()
    ret = REG.setdefault('settings', _settings(REG))
    set_reg(REG)
    return ret


def _registry(REG):
    settings = __salt__['mc_bootstraps.settings']()
    REG['registry'] = __salt__[
        'mc_macros.construct_registry_configuration'
    ](settings, defaults={})


def registry():
    REG = get_reg()
    ret = REG.setdefault('registry', _registry(REG))
    set_reg(REG)
    return ret


if (
    __name__ == '__main__'
    and os.environ.get('makina_test', None) == 'mc_utils'
):
    unittest.main()
