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
import datetime
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
from mc_states import ping

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False


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
# trick to be mutable and changed in tests
_CACHE_PREFIX = {'key': 'mcstates_api_cache_'}
_GLOBAL_KINDS = ['localsettings',
                 'services',
                 'services_managers',
                 'controllers',
                 'nodetypes',
                 'cloud']
_LOCAL_PREFS = [(a, 'makina-states.{0}.'.format(a))
                for a in _GLOBAL_KINDS]
_SUB_REGISTRIES = ['metadata', 'settings', 'registry']
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
RE_FLAGS = re.M | re.U | re.S
STRIP_FLAGS = RE_FLAGS
_CACHE_KEYS = {}
STRIPPED_RES = [
    re.compile(r"\x1b\[[0-9;]*[mG]", STRIP_FLAGS),
    re.compile(r"\x1b.*?[mGKH]", STRIP_FLAGS)]

_USE_MEMCACHE_FIRST = OrderedDict()
_USE_MEMOIZE_FIRST = OrderedDict()
log = logging.getLogger('mc_states.api')
OKEYS = {}


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


def cache_pop(cache, key, default=None):
    if isinstance(cache, pylibmc.ThreadMappedPool):
        with cache.reserve() as cs:
            return cs.delete(key)
    else:
        return cache.pop(key, default)


def default_get(mapping, key, default=_default):
    try:
        return mapping[key]
    except KeyError:
        if default is not _default:
            return default
        raise


def cache_get(cache, key, default=_default):
    if isinstance(cache, pylibmc.ThreadMappedPool):
        with cache.reserve() as cs:
            return default_get(cs, key, default)
    else:
        return default_get(cache, key, default)


def cache_set(cache, key, val=None):
    if isinstance(cache, pylibmc.ThreadMappedPool):
        with cache.reserve() as cs:
            cs.set(key, val)
    else:
        cache[key] = val
    return cache_get(cache, key)


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
            mcs = pylibmc.Client(
                addrs, binary=binary, behaviors=behaviors)
            # threadsafe pools
            _MC_SERVERS['cache'][key] = pylibmc.ThreadMappedPool(mcs)
        except (pylibmc.WriteError,):
            error = True
        except (Exception,):
            error = True
            trace = traceback.format_exc()
            log.error('Memcached error:\n{0}'.format(trace))
        if error:
            _MC_SERVERS['error'][error_key] = time.time()
    if error_key in _MC_SERVERS['error']:
        # retry failed memcache server in ten minutes
        if time.time() < (_MC_SERVERS['error'][error_key] + (10 * 60)):
            ping_test = False
    pinguable = False
    if HAS_PYLIBMC and ping_test:
        try:
            cache_set(_MC_SERVERS['cache'][key], 'mc_states_ping', 'ping')
            pinguable = True
        except (pylibmc.WriteError,):
            error = True
        except (Exception,):
            error = True
            trace = traceback.format_exc()
            log.error('Memcached error:\n{0}'.format(trace))
        if error:
            _MC_SERVERS['error'][error_key] = time.time()
    if pinguable and (error_key in _MC_SERVERS['error']):
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


def asstring(val):
    ret = ''
    if isinstance(val, six.string_types):
        ret = val
    elif val is None:
        ret = ''
    elif isinstance(val, (bool, int, float, complex, long)):
        ret = "{0}".format(val)
    else:
        ret = repr(val)
    return ret


def uniquify(seq):
    '''uniquify a list'''
    seen = set()
    return [x for x in seq
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
        if isinstance(cache, (pylibmc.ThreadMappedPool)):
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

    .. code-block:: python

        key = get_cache_key(mystring)
        key = get_cache_key(_CACHE_PREFIX + '<some-sha1>')
        key = get_cache_key('foo_{0}{1}{name}',
                            {'fun': 'mc_states.foo',
                             'arg': [1],
                             'kwarg': {'name': 'foobar'}})

    '''
    ckey = None
    # if we have a sha key, use that
    # use viewkeys => threadsafe, no iterator on
    # continelously mutating dict
    if key in six.viewkeys(_CACHE_KEYS):
        ckey = key
    if key.startswith(_CACHE_PREFIX['key']):
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
                raise IndexError('key is not formatted,'
                                 ' skip early'
                                 ' (error is passed later)')
            format_args = []
            if arg is None:
                arg = []
            if not isinstance(arg, list):
                arg = list(arg)
            # someshow deep copy before inserting func for repr
            arg = [a for a in arg]
            if func is not None and key is not _DEFAULT_KEY:
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
        ckey = "{0}_{1}".format(
            _CACHE_PREFIX['key'],
            hashlib.sha1(key).hexdigest())
        _CACHE_KEYS[ckey] = (sha, key)
    return ckey


def get_cache_servers(cache=None,
                      memcache=None,
                      key=None,
                      use_memcache=None,
                      debug=None):
    caches = []
    if is_memcache(cache):
        memcache = cache
        cache = None
    explicit_local_cache = isinstance(cache, (six.string_types, dict))
    if explicit_local_cache or (cache is None):
        caches.append(get_local_cache(cache))
    if (
        HAS_PYLIBMC and
        key and
        (use_memcache is not False) and
        not explicit_local_cache
    ):
        if isinstance(memcache, (pylibmc.Client, pylibmc.ThreadMappedPool)):
            mc_server = memcache
        else:
            mc_server = get_mc_server(memcache)
        if mc_server and mc_server not in caches:
            caches.append(mc_server)
        ckey = get_cache_key(key)
        fun_args = _CACHE_KEYS.get(ckey, ('', None))[1]
        for spattern, repattern in six.iteritems(_USE_MEMCACHE_FIRST):
            if spattern in fun_args:
                use_memcache = True
                break
            if repattern.search(fun_args):
                use_memcache = True
                break
        if use_memcache:
            caches.reverse()
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
    for cache in get_cache_servers(cache, memcache, key=key):
        try:
            entry = cache_get(cache, key)
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
                  memcache=None,
                  use_memcache=None,
                  __salt__=None,
                  __opts__=None,
                  force_run=False,
                  debug=None):
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

    # get the sha'ed key only after having ordered the cache
    # servers depending on the clear cache key
    okey = key
    key = get_cache_key(
        key, __opts__=__opts__, fun=func, arg=args, kwarg=kwargs)

    # first try to find a non expired cache entry
    caches = get_cache_servers(
        cache, memcache, use_memcache=use_memcache, key=key)
    ret = _default
    put_in_cache = True
    if put_in_cache:
        for cache in caches:
            now = time.time()
            last_access = cache_get(cache, 'last_access', None)
            if last_access is None:
                cache_set(cache, 'last_access', now)
                last_access = cache_get(cache, 'last_access')
            # global cleanup each 2 minutes
            if last_access and (last_access > (now + (2 * 60))):
                for k in [a for a in cache if a not in ['last_access']]:
                    cache_check(k, cache=cache, __opts__=__opts__)
            cache_set(cache, 'last_access', now)
            # if the cache value is expired, this call will cleanup
            # the cache from the expired value, and thus invalidating
            # the cache result
            cache_check(key, cache=cache, __opts__=__opts__)
            try:
                entry = cache_get(cache, key)
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

    OKEYS.setdefault(okey, 0)
    if force_run or (put_in_cache and ret is _default):
        OKEYS[okey] = OKEYS[okey] + 1
        ret = func(*args, **kwargs)

    # after the run, try to cache on any cache server
    # and fallback on next server in case of failures
    if not force_run and put_in_cache and (ret is not _default):
        cached = False
        for ix, cache in enumerate(caches):
            try:
                # never cache in the less priority caches more than 1 minute
                if ix:
                    try:
                        if seconds > 60:
                            seconds = 60
                    except (ValueError, TypeError):
                        seconds = 60
                val = {'value': ret, 'time': time.time(), 'ttl': seconds}
                cache_set(cache, key, val)
                cached = True
            except Exception:
                cached = False
                trace = traceback.format_exc()
                log.error('error while settings cache {0}'.format(trace))
            if cached:
                break
    return ret


def list_cache_keys(*args, **kwargs):
    keys = []
    for k in _LOCAL_CACHES:
        for l in _LOCAL_CACHES[k]:
            if l not in keys:
                keys.append(l)
    return keys


def small_sleep(*a, **kw):
    time.small_sleep(0.0001)


def _grace_retry(callback, tries, exceptions=None,
                 grace_callback=None, grace_args=None, grace_kw=None,
                 *args, **kw):
    if not exceptions:
        exceptions = (Exception,)
    for ctry in range(tries):
        try:
            return callback(*args, **kw)
        except exceptions as exc:
            if ctry >= (tries - 1):
                raise exc
            elif grace_callback:
                callback(ctry, tries, exc, *grace_args, **grace_kw)


def remove_cache_entry(key=_DEFAULT_KEY,
                       cache=None,
                       memcache=None,
                       __salt__=None,
                       __opts__=None,
                       *args,
                       **kwargs):
    key = get_cache_key(key, __opts__=__opts__, **kwargs)
    caches = get_cache_servers(cache=cache, memcache=memcache, key=key)
    for cache in caches:
        # do not garbage collector now, so not del !
        def pop(*a, **kw):
            cache_pop(cache, key)
        _grace_retry(pop, 200, exceptions=(pylibmc.NoServers,),
                     grace_callback=small_sleep)


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
                             caches=None,
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
    if not caches:
        caches = []
    if key.lower() in ['all', 'purge', 'purge_all', 'all_entries']:
        caches.extend([
            a for a in get_cache_servers(
                cache=cache, memcache=memcache, key=key)
            if a not in caches])
        for c in caches:
            if is_memcache(c):
                with c.reserve() as cs:
                    def flush(*a, **kw):
                        cs.flush_all()
                    _grace_retry(flush, 200,
                                 exceptions=(pylibmc.NoServers,),
                                 grace_callback=small_sleep)
            else:
                for i in [a for a in c]:
                    remove_cache_entry(i, **kw)
    else:
        remove_cache_entry(key, **kw)


def purge_memoize_cache(*args, **kwargs):
    return invalidate_memoize_cache('all', *args, **kwargs)


def magicstring(thestr):
    """
    Convert any string to UTF-8 ENCODED one
    """
    if not HAS_CHARDET:
        log.error('No chardet support !')
        return thestr
    seek = False
    if (
        isinstance(thestr, (int, float, long,
                            datetime.date,
                            datetime.time,
                            datetime.datetime))
    ):
        thestr = "{0}".format(thestr)
    if isinstance(thestr, unicode):
        try:
            thestr = thestr.encode('utf-8')
        except Exception:
            seek = True
    if seek:
        try:
            detectedenc = chardet.detect(thestr).get('encoding')
        except Exception:
            detectedenc = None
        if detectedenc:
            sdetectedenc = detectedenc.lower()
        else:
            sdetectedenc = ''
        if sdetectedenc.startswith('iso-8859'):
            detectedenc = 'ISO-8859-15'

        found_encodings = [
            'ISO-8859-15', 'TIS-620', 'EUC-KR',
            'EUC-JP', 'SHIFT_JIS', 'GB2312', 'utf-8', 'ascii',
        ]
        if sdetectedenc not in ('utf-8', 'ascii'):
            try:
                if not isinstance(thestr, unicode):
                    thestr = thestr.decode(detectedenc)
                thestr = thestr.encode(detectedenc)
            except Exception:
                for idx, i in enumerate(found_encodings):
                    try:
                        if not isinstance(thestr, unicode) and detectedenc:
                            thestr = thestr.decode(detectedenc)
                        thestr = thestr.encode(i)
                        break
                    except Exception:
                        if idx == (len(found_encodings) - 1):
                            raise
    if isinstance(thestr, unicode):
        thestr = thestr.encode('utf-8')
    thestr = thestr.decode('utf-8').encode('utf-8')
    return thestr


def prefered_ips(bclients):
    clients = []
    for client in bclients:
        try:
            clients.append(socket.gethostbyname(client))
        except Exception:
            # try to ping
            ret = None
            for i in range(4):
                try:
                    ret = ping.do_one(client, 4)
                except:
                    ret = None
                if ret is not None:
                    break
            if ret is not None:
                clients.append(client)
            else:
                log.error(
                    'target for dnsaddr is neither pinguable '
                    'or resolvable: {0}'.format(client))
    return [a.strip() for a in clients if a.strip()]


def param_as_list(data, param):
    if data.get(param) is None:
        data.pop(param, None)
    data.setdefault(param, [])
    if isinstance(data[param], (int, float)):
        data[param] = [data[param]]
    if isinstance(data[param], six.string_types):
        data[param] = [a.strip()
                       for a in data[param].split()
                       if a.strip()]
    return data
# vim:set et sts=4 ts=4 tw=80:
