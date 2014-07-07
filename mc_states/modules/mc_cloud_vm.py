#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_vm:

mc_cloud_vm / vm registry for compute nodes
===============================================

'''
__docformat__ = 'restructuredtext en'

# Import python libs
import logging
import mc_states.utils

from mc_states import saltapi
from salt.utils.odict import OrderedDict
from mc_states.utils import memoize_cache

__name = 'mc_cloud_vm'

log = logging.getLogger(__name__)


def vm_settings(suf='', ttl=60):
    '''
    VM cloud related settings
    THIS IS USED ON THE VM SIDE !
    '''
    def _do(suf):
        reg = __salt__['mc_macros.get_local_registry'](
            'cloud_vm_settings{0}'.format(suf),
            registry_format='pack')
        if 'vmSettings' not in reg:
            raise ValueError(
                'Registry not yet configured {0}'.format(
                    suf))
        return reg
    cache_key = 'mc_cloud_vm.vm_settings{0}'.format(suf)
    return memoize_cache(_do, [suf], {}, cache_key, ttl)


def settings(suf='', ttl=60):
    '''
    Alias to vm_settings
    '''
    return vm_settings(suf=suf, ttl=ttl)


def vm_settings_for(vm, ttl=60):
    '''
    VM cloud related settings
    THIS IS USED ON THE COMPUTE NODE SIDE !
    '''
    def _do(vm):
        return vm_settings('_' + vm)
    cache_key = ('mc_cloud_vm.vm_settings_for'
                 '{0}').format(vm)
    return memoize_cache(_do, [vm], {}, cache_key, ttl)


# vim:set et sts=4 ts=4 tw=80:
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=81:
