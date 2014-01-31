#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import copy

AUTO_NAMES = {'_registry': 'registry',
              '_settings': 'settings',
              '_metadata': 'metadata'}


def lazy_subregistry_get(__salt__, registry):
    def wrapper(func):
        key = AUTO_NAMES.get(func.__name__, func.__name__)
        def _call(*a, **kw):
            REG = __salt__['mc_macros.registry_kind_get'](registry)
            # TODO: replace the next line with the two others with a better test
            REG[key] = func(REG, *a, **kw)
            # to enable caching
            # if not key in REG:
            #     REG[key] = func(REG, *a, **kw)
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


# vim:set et sts=4 ts=4 tw=80:
