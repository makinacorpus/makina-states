#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
.. _mc_states_api:

mc_states_api / general API functions
=======================================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from time import time
import copy
import hashlib
import json
import logging
import os
import re
import socket
import traceback
import salt.output


# try to import fix from various places (readthedoc!!!)
try:
    import salt.ext.six as six
    HAS_SIX = True
except ImportError:
    try:
        import six
        HAS_SIX = True
    except ImportError:
        HAS_SIX = False
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

_GLOBAL_KINDS = [
    'localsettings',
    'services',
    'controllers',
    'nodetypes',
    'cloud',
]
_SUB_REGISTRIES = [
    'metadata',
    'settings',
    'registry',
]
NETWORK = '10.5.0.0'
NETMASK = '16'
RUNNER_CACHE_TIME = 24 * 60 * 60
AUTO_NAMES = {'_registry': 'registry',
              '_settings': 'settings',
              '_metadata': 'metadata'}
_CACHEKEY = 'localreg_{0}_{1}'
_LOCAL_CACHE = {}
_DEFAULT_KEY = 'cache_key_{0}'
_default = object()
log = logging.getLogger(__name__)


RE_FLAGS = re.M | re.U | re.S
_SHA1_CACHE = {}
STRIP_FLAGS = re.M | re.U | re.S
STRIPPED_RES = [
    re.compile(r"\x1b\[[0-9;]*[mG]", STRIP_FLAGS),
    re.compile(r"\x1b.*?[mGKH]", STRIP_FLAGS)]


def strip_colors(line):
    stripped_line = line
    for stripped_re in STRIPPED_RES:
        stripped_line = stripped_re.sub('', stripped_line)
    stripped_line = salt.output.strip_esc_sequence(line)
    return stripped_line


def asbool(item):
    if isinstance(item, six.string_types):
        item = item.lower()
    if item in [None, False, 0, '0', 'no', 'n', 'n', 'non']:
        item = False
    if item in [True, 1, '1', 'yes', 'y', 'o', 'oui']:
        item = True
    return bool(item)


def uniquify(seq):
    '''uniquify a list'''
    seen = set()
    return [x
            for x in seq
            if x not in seen and not seen.add(x)]


def splitstrip(string):
    '''Strip empty lines'''
    endl = string.endswith('\n')
    ret = '\n'.join(
        [a for a in string.splitlines() if a.strip()])
    if endl and not ret.endswith('\n'):
        ret += '\n'
    return ret


def msplitstrip(mapping, keys=None):
    '''Make the defined keys values stripped of
    their empty lines'''
    if not keys:
        keys = ['trace', 'comment', 'raw_comment']
    for k in keys:
        if k in mapping:
            mapping[k] = splitstrip(mapping[k])
    return mapping


def indent(string_or_list, indent='    ', sep='\n'):
    if isinstance(string_or_list, basestring):
        string_or_list = string_or_list.splitlines()
    if ''.join(string_or_list).strip():
        string_or_list = indent + '{1}{0}'.format(
            indent, sep).join(string_or_list)
    return string_or_list


def yencode(string):
    if isinstance(string, basestring):
        re_y = re.compile(' \.\.\.$', re.M)
        string = re_y.sub('', string)
    return string


def json_load(data):
    content = data.replace(' ---ANTLISLASH_N--- ', '\n')
    content = json.loads(content)
    return content


def json_dump(data, pretty=False):
    if pretty:
        content = json.dumps(
            data, indent=4, separators=(',', ': '))
    else:
        content = json.dumps(data)
        content = content.replace('\n', ' ---ANTLISLASH_N--- ')
    return content


def b64json_dump(data):
    return json_dump(data).encode('base64')


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
            # TODO: change the next line with the two others with a better test
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
        if filt not in REG:
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


def get_cache_key(key, __opts__):
    '''
    Configure a key per daemon
    '''
    if (
        (not key.startswith('mcstates_api_cache_')) or
        (key not in _SHA1_CACHE)
    ):
        if not __opts__:
            __opts__ = {}
        prefix = []
        # if we are called from a salt function and have enougth
        # information, be sure to modulate the cache from the minion
        # we are calling from
        for k in ['master',
                  'config_dir',
                  'conf_file',
                  'master_port',
                  'file_roots',
                  'pillar_roots',
                  'conf_prefix',
                  'publish_port',
                  'id',
                  'ret_port']:
            val = __opts__.get(k, None)
            if val:
                prefix.append("{0}".format(val))
        prefix = '_'.join(prefix)
        if prefix and not key.startswith(prefix):
            key = "{0}_{1}".format(prefix, key)
        if key not in _SHA1_CACHE:
            # hex digest is CPÜ intensive, cache it a bit too
            _SHA1_CACHE[key] = (
                "mcstates_api_cache_" + hashlib.sha1(key).hexdigest())
    ckey = _SHA1_CACHE[key]
    return ckey


def cache_check(cache, key, __opts__=None):
    '''
    Invalidate record in cache  if expired
    '''
    key = get_cache_key(key, __opts__=__opts__)
    try:
        entry = cache[key]
    except KeyError:
        entry = {}
    ttl = entry.get('ttl', 0)
    if not ttl:
        ttl = 0
    entry.setdefault('time', 0)
    if abs(time() - entry['time']) > ttl:
        # log.error(
        #      'poping stale cache {0}'.format(k))
        remove_entry(cache, key)
    return cache



def memoize_cache(func,
                  args=None,
                  kwargs=None,
                  key=_DEFAULT_KEY,
                  seconds=60,
                  cache=None,
                  use_memcache=False,
                  __salt__=None,
                  __opts__=None,
                  force_run=False):
    '''
    Memoize the func in the cache in the key 'key'
    and store the cached time in 'cache_key'
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
    if __salt__ is None:
        __salt__ = {}
    if not isinstance(__opts__, dict):
        __salt__ = {}
    if __opts__ is None:
        __opts__ = {}
    if not isinstance(__opts__, dict):
        __opts__ = {}
    try:
        seconds = int(seconds)
    except Exception:
        # in case of errors on seconds, try to run without cache
        seconds = 1
    memcached_users = [re.compile('.*mc_pillar.*', RE_FLAGS)]
    if not use_memcache:
        for memcached_user in memcached_users:
            if memcached_user.search(key):
                use_memcache = True
    if not seconds:
        seconds = 1
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    if isinstance(func, six.string_types):
        if func in __salt__:
            func = __salt__[func]
    if cache is None:
        cache = _LOCAL_CACHE
        if use_memcache and _MC:
            cache = _MC
    key = get_cache_key(key, __opts__=__opts__)
    now = time()
    if 'last_access' not in cache:
        cache['last_access'] = now
    last_access = cache['last_access']
    # log.error(cache.keys())
    # global cleanup each 2 minutes
    if last_access > (now + (2 * 60)):
        for k in [a for a in cache
                  if a not in ['last_access']]:
            cache_check(cache, k, __opts__=__opts__)
    cache['last_access'] = now
    cache_check(cache, key, __opts__=__opts__)
    if key not in cache:
        cache[key] = {}
    entry = cache[key]
    ret = entry.get('value', _default)
    if force_run or (ret is _default):
        ret = func(*args, **kwargs)
    # else:
    #     log.error("return cached")
    if not force_run and ret is not _default:
        try:
            cache[key] = {'value': ret,
                          'time': time(),
                          'ttl': seconds}
        except Exception:
            trace = traceback.format_exc()
            log.error('error while settings cache {0}'.format(trace))
    return ret


def remove_entry(cache,
                 key=_DEFAULT_KEY,
                 __opts__=None):
    key = get_cache_key(key, __opts__=__opts__)
    if cache is None:
        cache = _LOCAL_CACHE
        if _MC:
            cache = _MC
    if key not in cache:
        return
    # do not garbage collector now, so not del !
    try:
        if not _MC:
            cache.pop(key, None)
        else:
            cache.delete(key)
    except KeyError:
        pass


def invalidate_memoize_cache(key=_DEFAULT_KEY,
                             cache=None,
                             __opts__=None,
                             *a,
                             **kw):
    key = get_cache_key(key, __opts__=__opts__)
    remove_entry(cache, key, __opts__=__opts__)
    if key == 'ALL_ENTRIES':
        if _MC:
            _MC.flush_all()
        else:
            for i in cache:
                remove_entry(cache, i, __opts__=__opts__)
# vim:set et sts=4 ts=4 tw=80:
