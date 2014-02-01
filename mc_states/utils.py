#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import copy
from time import time


AUTO_NAMES = {'_registry': 'registry',
              '_settings': 'settings',
              '_metadata': 'metadata'}



_CACHEKEY = '{0}__CACHEKEY'


def lazy_subregistry_get(__salt__, registry):
    """
    1. lazy load registries
    2. remove problematic variables from the registries like the salt
       dictionnary
    """
    def wrapper(func):
        key = AUTO_NAMES.get(func.__name__, func.__name__)
        def _call(*a, **kw):
            REG = __salt__['mc_macros.registry_kind_get'](registry)
            # TODO: replace the next line with the two others with a better test
            # cache each registry 3 minutes, which should be sufficient
            # to render the whole sls files
            tkey = "{0}".format(time() // (3 * 60))
            ckey = _CACHEKEY.format(key)
            if not ckey in REG:
                REG[ckey] = ''
            if tkey != REG[ckey] and key in REG:
                del REG[key]
            if not key in REG:
                REG[key] = func(*a, **kw)
                REG[key]['reg_kind'] = registry
                REG[key]['reg_func_name'] = key
                filter_locals(REG[key])
                REG[ckey] = tkey
                __salt__['mc_macros.registry_kind_set'](registry, REG)
                REG = __salt__['mc_macros.registry_kind_get'](registry)
            return REG[key]
        return _call
    return wrapper


def dump(__salt__, kind, filters=None):
    if not filters:
        filters = []
    REG = copy.deepcopy(
        __salt__['mc_macros.registry_kind_get'](kind)
    )
    for filt in filters:
        if not filt in REG:
            del REG[filt]
    return REG


def filter_locals(reg, filter_list=None):
    '''
    Filter a dictionnary feeded with all the local
    variables in a context.

    We select what to remove depending on the original callee
    function (eg: {services, metadata, registry})
    '''
    # kind = reg.get('reg_kind', None)
    subreg = reg.get('reg_func_name', None)
    if not filter_list:
        filter_list = {
            'settings': [
                'REG',
                '__salt__',
                'pillar',
                'grains',
                '__pillar__',
                '__grains__',
                'saltmods',
            ]}.get(subreg, [])
    for item in filter_list:
        if item in reg:
            del reg[item]
    return reg


# vim:set et sts=4 ts=4 tw=80:
