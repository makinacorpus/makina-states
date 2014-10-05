#!/usr/bin/env python
'''
Utilities functions
===================
'''

# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import copy
from time import time
import logging
import socket


log = logging.getLogger(__name__)
AUTO_NAMES = {'_registry': 'registry',
              '_settings': 'settings',
              '_metadata': 'metadata'}



_CACHEKEY = 'localreg_{0}_{1}'
_LOCAL_CACHE = {}


def lazy_subregistry_get(__salt__, registry):
    """
    1. lazy load registries by calling them
       and then use memoize caching on them for 5 minutes.
    2. remove problematic variables from the registries like the salt
       dictionnary
    """
    def wrapper(func):
        key = AUTO_NAMES.get(func.__name__, func.__name__)
        def _call(*a, **kw):
            # TODO: replace the next line with the two others with a better test
            # cache each registry 5 minutes. which should be sufficient
            # to render the whole sls files
            # remember that the registry is a reference and even cached
            # it will be editable
            force_run = False
            if kw:
                force_run = True
            ttl = 5 * 60
            def _do(func, a, kw):
                ret = func(*a, **kw)
                ret = filter_locals(ret)
                return ret
            ckey = _CACHEKEY.format(registry, key)
            ret = memoize_cache(
                _do, [func, a, kw], {},  ckey,
                seconds=ttl, force_run=force_run)
            return ret
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


def is_valid_ip(ip_or_name):
    valid = False
    for familly in socket.AF_INET, socket.AF_INET6:
        if not valid:
            try:
                if socket.inet_pton(familly, ip_or_name):
                    valid = True
            except:
                pass
    return valid


def cache_check(cache, time_key, key, ttl_key):
    '''Invalidate record in cache  if expired'''
    time_check = "{0}".format(time() // cache[ttl_key])
    if time_key not in cache:
        cache[time_key] = 0.0
    if time_check != cache[time_key] and key in cache:
        for k in [time_key, ttl_key, key]:
            if k in cache:
                # log.error('poping stale cache {0}'.format(k))
                cache.pop(k)
    return cache


def memoize_cache(func, args=None, kwargs=None,
                  key='cache_key_{0}',
                  seconds=60, cache=None, force_run=False):
    '''Memoize the func in the cache
    in the key 'key' and store
    the cached time in 'cache_key'
    for further check of stale cache

    if force_run is set, we will uncondionnaly run.
    EG::

      >>> def serial_for(domain,
      ...                serials=None,
      ...                serial=None,
      ...                autoinc=True):
      ...     def _do(domain):
      ...         serial = int(
      ...                 datetime.datetime.now().strftime(
      ...                         '%Y%m%d01'))
      ...         return db_serial
      ...     cache_key = 'dnsserials_t_{0}'.format(domain)
      ...     return memoize_cache(
      ...         _do, [domain], {}, cache_key, 60)

    '''
    try:
        seconds = int(seconds)
    except Exception:
        # in case of errors on seconds, try to run without cache
        seconds = 1
    if not seconds:
        seconds = 1
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    if cache is None:
        cache = _LOCAL_CACHE
    key += '_'
    now = time()
    time_key = '{0}_time_check'.format(key)
    ttl_key = '{0}_ttl'.format(key)
    cache[ttl_key] = seconds
    last_access = cache.setdefault('last_access', now)
    # log.error(cache.keys())
    # global cleanup each 2 minutes
    if last_access > (now + (2 * 60)):
        for old_time_key in [a
                             for a in cache
                             if a.endswith('_time_check')]:
            old_key = old_time_key.split('_time_check')[0]
            old_ttl_key = old_time_key.split('_time_check')[0] + '_ttl'
            cache_check(cache, old_time_key, old_key, old_ttl_key)
    cache['last_access'] = now
    cache_check(cache, time_key, key, ttl_key)
    ret = cache.get(key, None)
    if force_run or (key not in cache):
        ret = func(*args, **kwargs)
    if not force_run and ret is not None:
        cache[key] = ret
        cache[time_key] = "{0}".format(time() // (seconds))
        cache[ttl_key] = seconds
    return ret


def invalidate_memoize_cache(key='cache_key_{0}', cache=None):
    if cache is None:
        cache = _LOCAL_CACHE
    key += '_'
    keys = [key,
            '{0}_time_check'.format(key),
            '{0}_ttl'.format(key)]
    for k in keys:
        cache.pop(k, None)



# vim:set et sts=4 ts=4 tw=80:
