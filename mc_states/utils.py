#!/usr/bin/env python
'''
Utilities functions
===================
'''

# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import copy
from time import time
import os
import logging
import socket


log = logging.getLogger(__name__)
AUTO_NAMES = {'_registry': 'registry',
              '_settings': 'settings',
              '_metadata': 'metadata'}



_CACHEKEY = 'localreg_{0}_{1}'
_LOCAL_CACHE = {}
_default = object()

try:
    import pylibmc
    HAS_PYLIBMC = True
except:
    HAS_PYLIBMC = False


try:
    if not HAS_PYLIBMC:
        raise Exception()
    _MC = pylibmc.Client(
        [os.environ.get('MC_SERVER', "127.0.0.1")],
        binary=True,
        behaviors={"tcp_nodelay": True,
                   "ketama": True})
    _MC.set('ping', 'ping')
except:
    _MC = None



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


def cache_check(cache, key):
    '''Invalidate record in cache  if expired'''
    if key not in cache:
        cache[key] = {}
    entry = cache[key]
    ttl = entry.get('ttl', 0)
    if not ttl:
        ttl = 0
    entry.setdefault('time', 0)
    if abs(time() - entry['time']) > ttl:
        # log.error(
        #      'poping stale cache {0}'.format(k))
        remove_entry(cache, key)
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
        if _MC:
            cache = _MC
    now = time()
    if 'last_access' not in cache:
        cache.set('last_access', now)
    last_access = cache['last_access']
    # log.error(cache.keys())
    # global cleanup each 2 minutes
    if last_access > (now + (2 * 60)):
        for k in [a for a in cache
                  if a not in ['last_access']]:
            cache_check(cache, k)
    cache['last_access'] = now
    cache_check(cache, key)
    if key not in cache:
        cache[key] = {}
    entry = cache[key]
    ret = entry.get('value', _default)
    if force_run or (ret is _default):
        ret = func(*args, **kwargs)
    # else:
    #     log.error("return cached")
    if not force_run and ret is not _default:
        cache[key] = {'value': ret,
                      'time': time(),
                      'ttl': seconds}
    return ret


def remove_entry(cache, key):
    if cache is None:
        cache = _LOCAL_CACHE
        if _MC:
            cache = _MC
    if key not in cache:
        return
    # do not garbage collector now, so not del !
    if not _MC:
        cache.pop(key, None)
    else:
        cache.delete(key)


def invalidate_memoize_cache(key='cache_key_{0}', cache=None, *a, **kw):
    remove_entry(cache, key)
    if key == 'ALL_ENTRIES':
        if _MC:
            _MC.flush_all()
        else:
            for i in cache:
                remove_entry(cache, i)
# vim:set et sts=4 ts=4 tw=80:
