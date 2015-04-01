#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
.. _mc_states_api:

mc_states_api / general API functions
=======================================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import time
import copy
import hashlib
import json
import logging
import os
import re
import socket
import traceback
import salt.output
from salt.utils.odict import OrderedDict
import salt.loader


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

ONE_MINUTE = 60
FIVE_MINUTES = 5 * ONE_MINUTE
TEN_MINUTES = 10 * ONE_MINUTE
ONE_HOUR = 6 * TEN_MINUTES
HALF_HOUR = ONE_HOUR / 2
ONE_DAY = 24 * ONE_HOUR
ONE_MONTH = 31 * ONE_DAY
HALF_DAY = ONE_DAY / 2

_MC_SERVERS = {'cache': {}, 'error': {}}
_CACHE_PREFIX = 'mcstates_api_cache_'
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
_DEFAULT_MC = 'default'
_LOCAL_CACHES = {}
_DEFAULT_KEY = 'cache_key_{0}'
_default = object()
log = logging.getLogger('mc_states.api')


RE_FLAGS = re.M | re.U | re.S
_CACHE_KEYS = {}
STRIP_FLAGS = re.M | re.U | re.S
STRIPPED_RES = [
    re.compile(r"\x1b\[[0-9;]*[mG]", STRIP_FLAGS),
    re.compile(r"\x1b.*?[mGKH]", STRIP_FLAGS)]

_USE_MEMCACHE_FIRST = OrderedDict()
_USE_MEMOIZE_FIRST = OrderedDict()


def get_local_cache(key=None):
    if not key:
        key = 'local'
    if isinstance(key, six.string_types):
        return _LOCAL_CACHES.setdefault(key, {})
    else:
        # real cache
        return key


def register_memcache_first(pattern):
    if pattern not in _USE_MEMCACHE_FIRST:
        _USE_MEMCACHE_FIRST[pattern] = re.compile(pattern, RE_FLAGS)


def register_memoize_first(pattern):
    if pattern not in _USE_MEMOIZE_FIRST:
        _USE_MEMOIZE_FIRST[pattern] = re.compile(pattern, RE_FLAGS)


def get_mc_server(key=None,
                  addrs=None,
                  ping_test=True,
                  binary=None,
                  behaviors=None):
    if not key:
        key = _DEFAULT_MC
    if not addrs:
        addrs = os.environ.get('MC_SERVER', '127.0.0.1')
    if not behaviors:
        behaviors = {"tcp_nodelay": True, "ketama": True}
    if binary is None:
        binary = True
    if isinstance(addrs, basestring):
        addrs = addrs.split(',')
    if not addrs:
        addrs = ['127.0.0.1']
    # log.error('addrs: {0}'.format(addrs))
    error, error_key = False, (key, tuple(addrs))
    if HAS_PYLIBMC and key not in _MC_SERVERS['cache']:
        try:
            _MC_SERVERS['cache'][key] = pylibmc.Client(
                addrs, binary=binary, behaviors=behaviors)
        except (pylibmc.WriteError,) as exc:
            error = True
        except (Exception,) as exc:
            error = True
            trace = traceback.format_exc()
            log.error('mc_statesMemcached error:\n{0}'.format(trace))
        if error:
            _MC_SERVERS['error'][error_key] = time.time()
    if error_key in _MC_SERVERS['error']:
        # retry failed memcache server in ten minutes
        if time.time() < (_MC_SERVERS['error'][error_key] + (10 * 60)):
            ping_test = False
    if HAS_PYLIBMC and ping_test:
        try:
            _MC_SERVERS['cache'][key].set('mc_states_ping', 'ping')
        except (pylibmc.WriteError,) as exc:
            error = True
        except (Exception,) as exc:
            error = True
            trace = traceback.format_exc()
            log.error('mc_statesMemcached error:\n{0}'.format(trace))
        if error:
            _MC_SERVERS['error'][error_key] = time.time()
    if error_key in _MC_SERVERS['error']:
        _MC_SERVERS['cache'].pop(key, None)
    return _MC_SERVERS['cache'].get(key, None)


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


def is_memcache(cache):
    if HAS_PYLIBMC:
        if isinstance(cache, pylibmc.client.Client):
            return True
    return False


def get_cache_key(key, __opts__=None, *args, **kw):
    '''
    Get an unique cache key from a key (string) candidate

    This return a key in the force mcstates_api_cache_<SHA1SUM of args>

    If the key is already a 'unique cache key', it wont be reprocessed

    This cache key will be adapted to be unique per salt daemon
    if we have enougth information to gather from the __opts__
    optional dictionnary.

    If the key contains format ({0}, {name})
    it will try to be formatted with additionnal arguments from kwargs:

        func
            func name
        arg
            arg to func
        kwarg
            kwarg for func

    EG::

        >>> key = get_cache_key(mystring)
        >>> key = get_cache_key(_CACHE_PREFIX + '<some-sha1>')
        >>> key = get_cache_key('foo_{0}{1}{name}',
                                {'fun': 'mc_states.foo',
                                 'arg': [1],
                                 'kwarg': {'name': 'foobar'}})

    '''
    ckey = None
    # if we have a sha key, use that
    if key in six.iterkeys(_CACHE_KEYS):
        ckey = key
    if not ckey:
        func = kw.get('fun', None)
        arg = kw.get('arg', None)
        kwarg = kw.get('kwarg', {})
        if not __opts__:
            __opts__ = {}
        prefix = []
        try:
            if not ('{' in key and '}' in key):
                raise IndexError('key is not formatted')
            format_args = []
            if arg is None:
                arg = []
            if not isinstance(arg, list):
                arg = list(arg)
            # someshow deep copy before inserting func for repr
            arg = [a for a in arg]
            if func is not None:
                arg.insert(0, func)
            if format_args or kwarg:
                key = key.format(*format_args, **kwarg)
        except Exception:
            pass  # key may not be meaned to be formated afterall

        # if we are called from a salt function and have enougth
        # information, be sure to modulate the cache from the daemon
        # we are calling from (master, minion, syndic & etc.)
        for k in ['master',
                  'config_dir',
                  'local',
                  'conf_file',
                  'master_port',
                  'file_roots',
                  'pillar_roots',
                  '__role',
                  'user',
                  'username',
                  'conf_prefix',
                  'publish_port',
                  'id',
                  'ret_port']:
            val = __opts__.get(k, None)
            if val:
                prefix.append("{0}".format(val))
        prefix = '_'.join(prefix)
        if prefix and not key.startswith(prefix):
            sha = "{0}_{1}".format(prefix, key)
        else:
            sha = key
        ckey = _CACHE_PREFIX + hashlib.sha1(key).hexdigest()
        _CACHE_KEYS[ckey] = (sha, key)
    return ckey


def cache_order(key=None, memcache_first=None, memoize_first=None):
    '''
    Try to determine the priority of cache servers based on the cache
    key.
        - mc_pillar.* use memcache first
        - everything else use memoize cache first

    If you want something to use memcache first, arrange for
    doging this before calling this function:
    ::

        >>> from mc_states.api import register_memcache_first
        >>> register_memcache_first(
        ...     'function call pattern (re pattern str or str)')

    '''
    def sort_cache_key(cache,
                       key=key,
                       memoize_first=memoize_first,
                       memcache_first=memcache_first):
        memoize_found = False
        memcache_found = False
        if key:
            ckey = get_cache_key(key)
            fun_args = _CACHE_KEYS.get(ckey, ('', None))[1]
            for spattern, repattern in six.iteritems(_USE_MEMOIZE_FIRST):
                if spattern in fun_args:
                    memoize_found = True
                    break
                if repattern.search(fun_args):
                    memoize_found = True
                    break
            for spattern, repattern in six.iteritems(_USE_MEMCACHE_FIRST):
                if spattern in fun_args:
                    memcache_found = True
                    break
                if repattern.search(fun_args):
                    memcache_found = True
                    break
        if memoize_found and memoize_first is None:
            memoize_first = True
        if memcache_found and memcache_first is None:
            memcache_first = True
        if memcache_first is None:
            memcache_first = False
        if memoize_first is None:
            memoize_first = False
        # memcache wins, but explitly tell that the opposite
        # cache action is first or seccond
        if memcache_first:
            memoize_first = False
        else:
            memoize_first = True
        if memoize_first:
            memcache_first = False
        else:
            memcache_first = True
        value = 0
        FORCE_LAST = 10000
        DEFAULT_FIRST = 300
        DEFAULT_SECOND = 500
        if is_memcache(cache):
            if memoize_first:
                value += DEFAULT_SECOND
            elif memcache_first:
                value += DEFAULT_FIRST
            else:
                value += FORCE_LAST
        else:
            if memoize_first:
                value += DEFAULT_FIRST
            else:
                value += DEFAULT_SECOND
        # if we gave a special cache= kwarg, take at at the most
        # priority
        if not is_memcache(cache):
            if cache is not get_local_cache():
                value = 0
        return "{0}".format(value)
    return sort_cache_key


def get_cache_servers(cache=None,
                      memcache=None,
                      key=None,
                      try_memcache=True,
                      memoize_first=None,
                      memcache_first=None):
    cache = get_local_cache(cache)
    caches = [cache]
    if try_memcache:
        mc_server = get_mc_server(memcache)
        if mc_server and mc_server not in caches:
            caches.append(mc_server)
    caches.sort(key=cache_order(key,
                                memoize_first=memoize_first,
                                memcache_first=memcache_first))
    return caches


def cache_check(key,
                cache=None,
                memcache=None,
                __opts__=None,
                __salt__=None,
                *args,
                **kwargs):
    '''
    Invalidate record in cache  if expired
    '''
    key = get_cache_key(key, __opts__=__opts__, **kwargs)
    for cache in get_cache_servers(
        cache,
        memcache,
        memoize_first=kwargs.get('memoize_first'),
        memcache_first=kwargs.get('memcache_first'),
        key=key
    ):
        try:
            entry = cache[key]
        except (IndexError, KeyError):
            continue
        now = time.time()
        try:
            ctime = float(entry.get('time', now))
        except (ValueError, TypeError,):
            ctime = now
        try:
            ttl = int(entry.get('ttl', 0))
        except (ValueError, TypeError,):
            ttl = 0
        if abs(now - ctime) >= ttl:
            remove_cache_entry(key, cache=cache, __opts__=__opts__)


def memoize_cache(func,
                  args=None,
                  kwargs=None,
                  key=_DEFAULT_KEY,
                  seconds=60,
                  cache=None,
                  memoize_first=None,
                  memcache_first=None,
                  memcache=None,
                  __salt__=None,
                  __opts__=None,
                  force_run=False,
                  pdb=None):
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
    if not isinstance(__salt__, (dict, salt.loader.LazyLoader)):
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
    if not seconds:
        seconds = 1
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    if isinstance(func, six.string_types):
        if func in __salt__:
            func = __salt__[func]
        else:
            raise ValueError('{0} is not resolvable to a salt'
                            ' func'.format(func))
    key = get_cache_key(
        key, __opts__=__opts__, fun=func, arg=args, kwarg=kwargs)

    cached, trace = False, ''
    # try to cache the result, but do not hardfail
    # while setting cache,
    # Also, if we have a result then, a failure here means
    # that the result wont be cached at first but will
    # be returned to the user
    #
    # It lets also a chance to be cached by the next cache server
    # By default, we try first on a local memcached server
    # then fallback on python module memoizing.

    # first try to find a non expired cache entry
    caches = get_cache_servers(cache,
                               memcache,
                               memcache_first=memcache_first,
                               memoize_first=memoize_first,
                               key=key)
    ret = _default
    put_in_cache = True
    for cache in caches:
        now = time.time()
        if 'last_access' not in cache:
            cache['last_access'] = now
        last_access = cache['last_access']
        # global cleanup each 2 minutes
        if last_access > (now + (2 * 60)):
            for k in [a for a in cache if a not in ['last_access']]:
                cache_check(k,
                            cache=cache,
                            memoize_first=memoize_first,
                            memcache_first=memcache_first,
                            __opts__=__opts__)
        cache['last_access'] = now
        # if the cache value is expired, this call will cleanup
        # the cache from the expired value, and thus invalidating
        # the cache result
        cache_check(key,
                    cache=cache,
                    memoize_first=memoize_first,
                    memcache_first=memcache_first,
                    __opts__=__opts__)
        try:
            # memcached has not get(k, default)
            entry = cache[key]
        except (KeyError, IndexError):
            entry = {}
        if not isinstance(entry, dict):
            entry = {}
        ret = entry.get('value', _default)
        # if we found a value that seems to be a cached result,
        # we are set, break the cache servers resultsget loop
        if ret is not _default:
            put_in_cache = False
            break

    # if either we force the run or the cached value is expired
    # run the function
    if force_run or (ret is _default):
        try:
            logger = log.garbage
        except AttributeError:
            logger = log.debug
        try:
            logger(
                "memoizecache: Calling {0}".format(
                    _CACHE_KEYS[key][1]))
        except Exception:
            try:
                logger(
                    "memoizecache: Calling {0}({3}): "
                    "args: {1} kwargs: {2}".format(func, args, kwargs))
            except Exception:
                try:
                    logger(
                        "memoizecache: Calling {0} args: {1}".format(
                            func, args))
                except Exception:
                    try:
                        logger("memoizecache: Calling {0}".format(func))
                    except Exception:
                        pass
        ret = func(*args, **kwargs)

    # after the run, try to cache on any cache server
    # and fallback on next server in case of failures

    if put_in_cache and (ret is not _default):
        cached = False
        for cache in caches:
            try:
                cache[key] = {'value': ret,
                              'time': time.time(),
                              'ttl': seconds}
                cached = True
            except Exception:
                cached = False
                trace = traceback.format_exc()
            if cached:
                break
        if caches and not cached:
            if trace:
                log.error('error while settings cache {0}'.format(trace))
            else:
                log.error('error while settings cache')
    return ret


def remove_cache_entry(key=_DEFAULT_KEY,
                       cache=None,
                       memcache=None,
                       __salt__=None,
                       __opts__=None,
                       *args,
                       **kwargs):
    key = get_cache_key(key, __opts__=__opts__, **kwargs)
    if cache is not None:
        caches = [cache]
    else:
        caches = get_cache_servers(
            cache=cache,
            memcache=memcache,
            key=key,
            memoize_first=kwargs.get('memoize_first'),
            memcache_first=kwargs.get('memcache_first'))
    for cache in caches:
        # do not garbage collector now, so not del !
        try:
            if is_memcache(cache):
                if key in cache:
                    cache.delete(key)
            else:
                cache.pop(key, None)
        except KeyError:
            pass


def remove_entry(cache, key, *args, **kw):
    '''
    Retro compat wrapper
    '''
    log.error('Please use mc_states.api.remove_cache_entry instead of'
              ' remove_entry')
    kw['cache'] = cache
    return remove_cache_entry(key, *args, **kw)


def invalidate_memoize_cache(key=_DEFAULT_KEY,
                             cache=None,
                             memcache=None,
                             __salt__=None,
                             __opts__=None,
                             *args,
                             **kw):
    kw = copy.deepcopy(kw)
    kw.setdefault('cache', cache)
    kw.setdefault('memcache', memcache)
    kw['__opts__'] = __opts__
    kw['__salt__'] = __salt__
    if key.lower() in ['all', 'purge', 'purge_all', 'all_entries']:
        caches = []
        if cache is not None:
            caches.append(cache)
        if is_memcache(cache):
            caches.append(memcache)
        if isinstance(memcache, six.string_types):
            caches.append(get_mc_server(memcache))
        if not caches:
            caches = get_cache_servers(cache=cache, memcache=memcache)
        for c in caches:
            if is_memcache(c):
                for i in range(5):
                    try:
                        c.flush_all()
                        break
                    except pylibmc.NoServers:
                        pass
                    except (Exception,) as exc:
                        trace = traceback.format_exc()
                        if i == 9:
                            log.error(exc.__class__)
                            log.error(exc.__module__)
                            log.error(trace)
                            time.sleep(0.0001)
            else:
                for i in [a for a in c]:
                    remove_cache_entry(i, **kw)
    else:
        remove_cache_entry(key, **kw)


def purge_memoize_cache(*args, **kwargs):
    return invalidate_memoize_cache('all', *args, **kwargs)
# vim:set et sts=4 ts=4 tw=80:
