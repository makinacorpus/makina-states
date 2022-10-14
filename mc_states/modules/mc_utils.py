# -*- coding: utf-8 -*-
'''
.. _module_mc_utils:

mc_utils / Some usefull small tools
====================================



'''

# Import salt libs
from pprint import pformat
import sys
import copy
import cProfile
import crypt
import collections
try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping
import datetime
import traceback
import socket
import hashlib
import logging
import os
import pstats
import re


import salt.loader
import salt.template
from salt.config import master_config, minion_config
from salt.exceptions import SaltException
import salt.utils
import salt.utils.dictupdate
import salt.utils.network
from salt.utils.pycrypto import secure_password
from salt.utils.odict import OrderedDict
from salt.ext import six as six
from mc_states import api, saltcompat
import mc_states.api
import mc_states.saltapi
from distutils.version import LooseVersion

from mc_states.saltcompat import DEFAULT_TARGET_DELIM

_CACHE = {'mid': None}
_default_marker = object()
_marker = object()
log = logging.getLogger(__name__)
is_really_a_var = re.compile('(\{[^:}]+\})', re.M | re.U)


def loose_version(*args, **kw):
    return LooseVersion(*args, **kw)


def empty_caches(extras=None):
    if not extras:
        extras = []
    for i in extras + [_CACHE]:
        if isinstance(i, dict):
            for a in [b for b in i]:
                i.pop(a, None)
    for cache in [
        mc_states.api._LOCAL_CACHES,
    ]:
        for i in [a for a in cache]:
            val = cache[a]
            if isinstance(val, dict):
                for v in [b for b in val]:
                    val.pop(v, None)
            else:
                cache.pop(i, None)
    _CACHE['mid'] = None


def assert_good_grains(grains):
     ''''
     no time to search/debug why,
     but sometimes grains dict is empty depending on the call context
     grains loading bug retriggered (i fixed once, do not remember where, FU SALT ...
     '''
     if not grains:
         grains = salt.loader.grains(__opts__)
     return grains


def hash(string, typ='md5', func='hexdigest'):
    '''
    Return the hash of a string
    CLI Examples::

        salt-call --local mc_utils.hash foo
        salt-call --local mc_utils.hash foo md5
        salt-call --local mc_utils.hash foo sha1
        salt-call --local mc_utils.hash foo sha224
        salt-call --local mc_utils.hash foo sha256
        salt-call --local mc_utils.hash foo sha384
        salt-call --local mc_utils.hash foo sha512

    '''
    if func not in ['hexdigest', 'digest']:
        func = 'hexdigest'

    if typ not in [
        'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'
    ]:
        raise TypeError('{0} is not valid hash'.format(typ))
    if sys.version[0] > "2" and hasattr(string, 'encode'):
        string = string.encode()
    return getattr(getattr(hashlib, typ)(string), func)()


def uniquify(*a, **kw):
    return api.uniquify(*a, **kw)


def odict(instance=True):
    if instance:
        return OrderedDict()
    return OrderedDict


def local_minion_id(force=False):
    '''
    search in running config root
    then in well known config salt root
    then use regular salt function
    '''
    mid = _CACHE['mid']
    if mid and not force:
        return mid
    paths = api.uniquify([__opts__['config_dir'], '/etc/salt'])
    for path in paths:
        for cfgn, fun in OrderedDict(
            [('master', master_config),
             ('minion', minion_config)]
        ).items():
            cfg = os.path.join(path, cfgn)
            if os.path.exists(cfg):
                try:
                    cfgo = fun(cfg)
                    mid = cfgo.get('id', None)
                    if mid.endswith('_master'):
                        mid = None
                except Exception:
                    pass
            if mid:
                break
        if mid:
            break
    # normally we should never hit this case as salt generates
    # internally during config parsing the minion id
    if not mid:
        mid = salt.utils.network.generate_minion_id()
    _CACHE['mid'] = mid
    return mid


def magicstring(thestr):
    """
    Convert any string to UTF-8 ENCODED one
    """
    return api.magicstring(thestr)


def generate_stored_password(key, length=None, force=False, value=None):
    '''
    Generate and store a password.
    At soon as one is stored with a specific key, it will never be renegerated
    unless you set force to true.
    '''
    if length is None:
        length = 16
    reg = __salt__[
            'mc_macros.get_local_registry'](
                'local_passwords', registry_format='pack')
    sav = False
    if not key in reg:
        sav = True
    rootpw = reg.setdefault(key, __salt__['mc_utils.generate_password'](length))
    if force or not rootpw:
        rootpw = __salt__['mc_utils.generate_password'](length)
        sav = True
    if value is not None:
        rootpw = value
    reg[key] = rootpw
    __salt__['mc_macros.update_local_registry'](
        'local_passwords', reg, registry_format='pack')
    return rootpw


def generate_password(length=None):
    if length is None:
        length = 16
    return secure_password(length)


class _CycleError(Exception):
    '''.'''
    def __init__(self, msg, new=None, original_dict=None, *args, **kwargs):
        super(_CycleError, self).__init__(msg, *args, **kwargs)
        self.new = new
        self.original_dict = original_dict


def deepcopy(arg):
    return copy.deepcopy(arg)


def update_no_list(dest, upd, recursive_update=True):
    return mc_states.saltapi.update_no_list(dest, upd, recursive_update=recursive_update)


def dictupdate(dict1, dict2):
    '''
    Merge two dictionnaries recursively

    test::

      salt '*' mc_utils.dictupdate '{foobar:
                  {toto: tata, toto2: tata2},titi: tutu}'
                  '{bar: toto, foobar: {toto2: arg, toto3: arg2}}'
      ----------
      bar:
          toto
      foobar:
          ----------
          toto:
              tata
          toto2:
              arg
          toto3:
              arg2
      titi:
          tutu
    '''
    return mc_states.saltapi.dictupdate(dict1, dict2)


def copy_dictupdate(dict1, dict2):
    '''
    Similar to dictupdate but with deepcopy of two
    merged dicts first.
    '''
    return dictupdate(copy.deepcopy(dict1),
                      copy.deepcopy(dict2))


def unresolved(data):
    ret = None
    if isinstance(data, six.string_types):
        if '{' in data and '}' in data:
            if is_really_a_var.search(data):
                ret = True
            else:
                ret = False
        else:
            ret = False
    elif isinstance(data, dict):
        for k, val in six.iteritems(data):
            ret1 = unresolved(k)
            ret2 = unresolved(val)
            ret = ret1 or ret2
            if ret:
                break
    elif isinstance(data, (list, set)):
        for val in data:
            ret = unresolved(val)
            if ret:
                break
    return ret


def _str_resolve(new, original_dict=None, this_call=0, topdb=False):

    '''
    low level and optimized call to format_resolve
    '''
    init_new = new
    # do not directly call format to handle keyerror in original mapping
    # where we may have yet keyerrors
    if isinstance(original_dict, dict):
        for k in original_dict:
            reprk = k
            if not isinstance(reprk, six.string_types):
                reprk = '{0}'.format(k)
            subst = '{' + reprk + '}'
            if subst in new:
                subst_val = original_dict[k]
                if isinstance(subst_val, (list, dict)):
                    inner_new = format_resolve(
                        subst_val, original_dict,
                        this_call=this_call, topdb=topdb)
                    # composed, we take the repr
                    if new != subst:
                        new = new.replace(subst, str(inner_new))
                    # no composed value, take the original list
                    else:
                        new = inner_new
                else:
                    if new != subst_val:
                        new = new.replace(subst, str(subst_val))
            if not unresolved(new):
                # new value has been totally resolved
                break
    return new, new != init_new


def str_resolve(new, original_dict=None, this_call=0, topdb=False):
    return _str_resolve(
        new, original_dict=original_dict, this_call=this_call, topdb=topdb)[0]


def _format_resolve(value,
                    original_dict=None,
                    this_call=0,
                    topdb=False,
                    retry=None,
                    **kwargs):
    '''
    low level and optimized call to format_resolve
    '''
    if not original_dict:
        original_dict = OrderedDict()

    if this_call == 0:
        if not original_dict and isinstance(value, dict):
            original_dict = value

    changed = False

    if kwargs:
        original_dict.update(kwargs)

    if not unresolved(value):
        return value, False

    if isinstance(value, dict):
        new = type(value)()
        for key, v in value.items():
            val, changed_ = _format_resolve(v, original_dict, topdb=topdb)
            if changed_:
                changed = changed_
            new[key] = val
    elif isinstance(value, (list, tuple)):
        new = type(value)()
        for v in value:
            val, changed_ = _format_resolve(v, original_dict, topdb=topdb)
            if changed_:
                changed = changed_
            new = new + type(value)([val])
    elif isinstance(value, six.string_types):
        new, changed_ = _str_resolve(value, original_dict, topdb=topdb)
        if changed_:
            changed = changed_
    else:
        new = value

    if retry is None:
        retry = unresolved(new)

    while retry and (this_call < 100):
        new, changed = _format_resolve(new,
                                       original_dict,
                                       this_call=this_call,
                                       retry=False,
                                       topdb=topdb)
        if not changed:
            retry = False
        this_call += 1
    return new, changed


def format_resolve(value,
                   original_dict=None,
                   this_call=0, topdb=False, **kwargs):

    '''
    Resolve a dict of formatted strings, mappings & list to a valued dict
    Please also read the associated test::

        {"a": ["{b}", "{c}", "{e}"],
         "b": 1,
         "c": "{d}",
         "d": "{b}",
         "e": "{d}",
        }

        ====>
        {"a": ["1", "1", "{e}"],
         "b": 1,
         "c": "{d}",
         "d": "{b}",
         "e": "{d}",
        }

    '''
    return _format_resolve(value,
                           original_dict=original_dict,
                           this_call=this_call,
                           topdb=topdb,
                           **kwargs)[0]


def is_a_str(value):
    '''
    is the value a stirng
    '''
    return isinstance(value, six.string_types)


def is_a_bool(value):
    '''
    is the value a bool
    '''
    return isinstance(value, bool)


def is_a_int(value):
    '''
    is the value an int
    '''
    return isinstance(value, int)


def is_a_float(value):
    '''
    is the value a float
    '''
    return isinstance(value, float)


def is_a_complex(value):
    '''
    is the value a complex
    '''
    return isinstance(value, complex)


def is_a_long(value):
    '''
    is the value a long
    '''
    return isinstance(value, long)


def is_a_number(value):
    '''
    is the value a number
    '''
    return (
        is_a_int(value) or
        is_a_float(value) or
        is_a_complex(value) or
        is_a_long(value)
    )


def is_a_set(value):
    '''
    is the value a set
    '''
    return isinstance(value, set)


def is_a_tuple(value):
    '''
    is the value a tuple
    '''
    return isinstance(value, tuple)


def is_a_list(value):
    '''
    is the value a list
    '''
    return isinstance(value, list)


def is_a_dict(value):
    '''
    is the value a dict
    '''
    return isinstance(value, dict)


def is_iter(value):
    '''
    is the value iterable (list, set, dict tuple)
    '''
    return (
        is_a_list(value) or
        is_a_dict(value) or
        is_a_tuple(value) or
        is_a_set(value)
    )


def traverse_dict(data, key, delimiter=DEFAULT_TARGET_DELIM):
    '''
    Handle the fact to traverse dicts with '.' as it was an old
    default and makina-states relies a lot on it

    This restore the old behavior of something that can be traversed

    makina-states.foo:
        bar:
            c: true

    can be traversed with makina-states.foo.bar.c
    '''
    delimiters = uniquify([delimiter, DEFAULT_TARGET_DELIM,
                           ':', '.'])
    ret = dv = '_|-'
    for dl in delimiters:
        for cdl in reversed(delimiters):
            ret = saltcompat.traverse_dict(data, key, dv, delimiter=dl)
            if ret != dv:
                return ret
            if cdl in key and dl not in key:
                nkey = key.replace(cdl, dl)
                ret = saltcompat.traverse_dict(data, nkey, dv, delimiter=dl)
                if ret != dv:
                    return ret
                # if the dict is not at the end, we try to progressivily
                # combine the delimiters from the start of the key
                # a.c.d.e will be tested then for
                # a.c:d:e will be tested then for
                # a.c.d:e will be tested then for
                # we do not test the last element as it is the exact key !
                for i in range(key.count(cdl)-1):
                    dkey = nkey.replace(dl, cdl, i+1)
                    ret = saltcompat.traverse_dict(
                        data, dkey, dv, delimiter=dl)
                    if ret != dv:
                        return ret
    return ret


def uncached_get(key, default='',
                 local_registry=None, registry_format='pack',
                 delimiter=DEFAULT_TARGET_DELIM):
    '''
    Same as 'config.get' but with different retrieval order.

    This routine traverses these data stores in this order:

        - Local minion config (opts)
        - Minion's pillar
        - Dict:
            - passed in local_registry argument
            - or automaticly loaded global registries
        - Minion's grains
        - Master config

    CLI Example:

    .. code-block:: bash

        salt '*' mc_utils.get pkg:apache

    '''
    _s, _g, _p, _o = __salt__, __grains__, __pillar__, __opts__
    if local_registry is None:
        for reg, pref in api._LOCAL_PREFS:
            if key.startswith(pref):
                local_registry = reg
                break
    if (
        isinstance(local_registry, six.string_types) and
        local_registry not in ['localsettings']
    ):
        local_registry = _s['mc_macros.get_local_registry'](
            local_registry, registry_format=registry_format)
    elif not isinstance(local_registry, dict):
        local_registry = None
    ret = traverse_dict(_o, key, delimiter=delimiter)
    if ret != '_|-':
        return ret
    ret = traverse_dict(_p, key, delimiter=delimiter)
    if ret != '_|-':
        return ret
    if local_registry is not None:
        ret = traverse_dict(local_registry, key, delimiter=delimiter)
        if ret != '_|-':
            return ret
    ret = traverse_dict(_g, key, delimiter=delimiter)
    if ret != '_|-':
        return ret
    ret = traverse_dict(_p.get('master', {}), key, delimiter=delimiter)
    if ret != '_|-':
        return ret
    return default


def cached_get(key, default='',
               local_registry=None, registry_format='pack',
               delimiter=DEFAULT_TARGET_DELIM, ttl=60):
    cache_key = 'mc_utils_get.{0}{1}{2}{3}'.format(key,
                                                   local_registry,
                                                   registry_format,
                                                   delimiter)
    return __salt__['mc_utils.memoize_cache'](
        uncached_get,
        [key],
        {'default': default,
         'local_registry': local_registry,
         'registry_format': registry_format,
         'delimiter': delimiter},
        cache_key,
        ttl)


get = uncached_get


def get_uniq_keys_for(prefix):
    '''
    Return keys for prefix:

        - if prefix is in conf
        - All other keys of depth + 1

    With makina.foo prefix:

        - returns makina.foo
        - returns makina.foo.1
        - dont returns makina.foo.1.1
        - dont returns makina
        - dont returns makina.other
    '''

    keys = OrderedDict()
    for mapping in (__pillar__,
                    __grains__):
        skeys = []
        for k in mapping:
            if any([
                k == prefix,
                k.startswith("{0}.".format(prefix))
            ]):
                testn = k[len(prefix):]
                try:
                    if testn.index('.') < 2:
                        skeys.append(k)
                except (IndexError, ValueError):
                    continue
        skeys.sort()
        for k in skeys:
            keys[k] = mapping[k]
    return keys


def defaults(prefix,
             datadict,
             ignored_keys=None,
             overridden=None,
             noresolve=False,
             firstcall=True):
    '''
    Magic defaults settings configuration getter

    - Get the "prefix" value from the configuration (pillar/grain)
    - Then overrides or append to it with the corresponding
      key in the given "datadict" if value is a dict or a list.

      - If we get from pillar/grains/local from the curent key in the form:
        "{prefix}-overrides: it overrides totally the original value.
      - if the datadict contains a key "{prefix}-append and
        the value is a list, it appends to the original value

    - If the datadict contains a key "{prefix}":
        - If a list: override to the list the default list in conf
        - Elif a dict: update the default dictionnary with the one in conf
        - Else take that as a value if the value is not a mapping or a list
    '''
    if not ignored_keys:
        ignored_keys = []
    if firstcall:
        global_pillar = copy.deepcopy(
            __salt__['mc_utils.get'](prefix))
        if isinstance(global_pillar, dict):
            for k in [a for a in ignored_keys if a in global_pillar]:
                if k in global_pillar:
                    del global_pillar[k]
            datadict = __salt__['mc_utils.dictupdate'](datadict, global_pillar)

    # if we overrided only keys of a dict
    # but this dict is an empty dict in the default mapping
    # be sure to load them inside this dict
    items = get_uniq_keys_for(prefix)
    dotedprefix = '{0}.'.format(prefix)
    for fullkey in items:
        key = dotedprefix.join(fullkey.split(dotedprefix)[1:])
        val = items[fullkey]
        if isinstance(datadict, dict):
            curval = datadict.get(key, None)
            if isinstance(curval, dict):
                val = __salt__['mc_utils.dictupdate'](curval, val)
            elif isinstance(curval, (list, set)):
                if val is not None:
                    for subitem in val:
                        if subitem in curval:
                            continue
                        curval.append(subitem)
                val = curval
            datadict[key] = val
    if overridden is None:
        overridden = OrderedDict()
    if prefix not in overridden:
        overridden[prefix] = OrderedDict()
    pkeys = OrderedDict()
    for a in datadict:
        if a not in ignored_keys and isinstance(a, six.string_types):
            to_unicode = False
            for i in prefix, a:
                if isinstance(i, six.text_type):
                    to_unicode = True
                    break
            k = '{0}.{1}'.format(magicstring(prefix), magicstring(a))
            if to_unicode:
                if sys.version[0] < '3':
                    k = k.decode('utf-8')
            pkeys[a] = (k, datadict[a])
    for key, value_data in pkeys.items():
        value_key, default_value = value_data
        # special key to completly override the dictionnary
        avalue = _default_marker
        value = __salt__['mc_utils.get'](
            value_key + "-override",
            __salt__['mc_utils.get'](
                value_key + "-overrides", _default_marker)
            )
        if isinstance(default_value, list):
            avalue = __salt__['mc_utils.get'](
                value_key + "-append", _default_marker)
        if value is not _default_marker:
            overridden[prefix][key] = value
        else:
            value = __salt__['mc_utils.get'](value_key, _default_marker)
        if not isinstance(default_value, list) and value is _default_marker:
            value = default_value
        if isinstance(default_value, list):
            if key in overridden[prefix]:
                value = overridden[prefix][key]
            else:
                nvalue = default_value[:]
                if (
                    value and
                    (value != nvalue) and
                    (value is not _default_marker)
                ):
                    if nvalue is None:
                        nvalue = []
                    for subitem in value:
                        if subitem in nvalue:
                            continue
                        nvalue.append(subitem)
                value = nvalue
            if isinstance(avalue, list):
                for subitem in avalue:
                    if subitem in value:
                        continue
                    value.append(subitem)
        elif isinstance(value, dict):
            # recurvive and conservative dictupdate
            ndefaults = defaults(value_key,
                                 value,
                                 overridden=overridden,
                                 noresolve=noresolve,
                                 firstcall=firstcall)
                                 # firstcall=False)
            if overridden[value_key]:
                for k, value in overridden[value_key].items():
                    default_value[k] = value
            # override specific keys values handle:
            # eg: makina-states.services.firewall.params.RESTRICTED_SSH = foo
            # eg: makina-states.services.firewall.params:
            #        foo: var
            for k, subvalue in get_uniq_keys_for(value_key).items():
                ndefaults[k.split('{0}.'.format(value_key))[1]] = subvalue
            value = __salt__['mc_utils.dictupdate'](default_value, ndefaults)
        datadict[key] = value
        for k, value in overridden[prefix].items():
            datadict[k] = value
    if not noresolve:
        datadict = format_resolve(datadict)
    return datadict


def sanitize_kw(kw):
    ckw = copy.deepcopy(kw)
    for k in kw:
        if ('__pub_' in k) and (k in ckw):
            ckw.pop(k)
    return ckw


def salt_root():
    '''get salt root from either pillar or opts (minion or master)'''
    salt = __salt__['mc_salt.settings']()
    return salt['salt_root']


def msr():
    '''get salt root from either pillar or opts (minion or master)'''
    salt = __salt__['mc_salt.settings']()
    return salt['msr']


def remove_stuff_from_opts(__opts):
    if 'mc_opts' in __opts:
        globals().update({'__opts__': __opts['mc_opts']})
    return globals()['__opts__']


def copy_dunder(dunder):
    ndunder = OrderedDict()
    dclass = dunder.__class__.__name__.lower()
    if (
        isinstance(dunder, dict) or
        'dict' in dclass or
        'loader' in dclass
    ):
        for k in dunder:
            val = dunder[k]
            ndunder[k] = copy_dunder(val)
    else:
        ndunder = copy.deepcopy(dunder)
    return ndunder


def add_stuff_to_opts(__opts):
    if 'mc_opts' not in __opts:
        # UGLY HACK for the lazyloader
        # that may fail deepcopying NamespacedDictWrapper
        # in recent salt versions
        nopts = copy_dunder(__opts)
        nopts['mc_opts'] = __opts
        try:
            nopts['grains'] = __grains__
        except Exception:
            pass
        try:
            nopts['pillar'] = __pillar__
        except Exception:
            pass
        globals().update({'__opts__': nopts})
    return globals()['__opts__']


def sls_load(sls, get_inner=False):
    if not os.path.exists(sls):
        raise OSError('does not exists: {0}'.format(sls))
    # if we do not deepcopy _opts__ it may fail with
    # AttributeError: 'ContextDict' object has no attribute 'global_data'
    # on dunders, later on executions, i do not know why
    # see: https://github.com/saltstack/salt/issues/29123
    __opts = copy_dunder(__opts__)
    try:
        add_stuff_to_opts(__opts)
        jinjarend = salt.loader.render(__opts, __salt__)
        data_l = salt.template.compile_template(
            sls, jinjarend, __opts['renderer'], saltenv='base',
            blacklist=None, whitelist=None)
    except Exception:
        trace = traceback.format_exc()
        log.error(trace)
    finally:
        remove_stuff_from_opts(__opts)
    if isinstance(data_l, (dict, list, set)) and get_inner:
        if len(data_l) == 1:
            if isinstance(data_l, dict):
                for key in six.iterkeys(data_l):
                    data_l = data_l[key]
                    break
            else:
                data_l = data_l[0]
    return data_l


def indenter(text, amount, ch=' '):
    padding = amount * ch
    return ''.join(padding+line for line in text.splitlines(True))


def file_read(fic, indent=None, ch=' '):
    '''
    read the content a file
    '''
    data = ''
    with open(fic, 'r') as f:
        data = f.read()
    if indent:
        data = indenter(data, indent, ch)
    return data


def unix_crypt(passwd):
    '''Encrypt the stringed password in the unix crypt format (/etc/shadow)'''
    return crypt.crypt(passwd, '$6$SALTsalt$')


def sls_available(sls, pillar=True):
    ret = True
    if pillar:
        root = __opts__['pillar_roots']['base'][0]
    else:
        root = __opts__['pillar_roots']['base'][0]
    fp = os.path.join(root, sls.replace('.', '/') + '.sls')
    try:
        ret = os.path.exists(fp)
    except OSError:
        ret = False
    return ret


def indent(tstring, spaces=16, char=' '):
    data = ''
    for ix, i in enumerate(tstring.split('\n')):
        if ix > 0:
            data += char * spaces
        data += i + '\n'
    return data


def profile(func, *args, **kw):
    if not __opts__.get('ms_profile_enabled', False):
        raise Exception('Profile not enabled')
    kw = copy.deepcopy(kw)
    for i in [a for a in kw if a.startswith('__')]:
        kw.pop(i, None)
    pr = cProfile.Profile()
    pr.enable()
    ret = __salt__[func](*args, **kw)
    pr.disable()
    if not os.path.isdir('/tmp/stats'):
        os.makedirs('/tmp/stats')
    ficp = '/tmp/stats/{0}.pstats'.format(func)
    fico = '/tmp/stats/{0}.dot'.format(func)
    ficcl = '/tmp/stats/{0}.calls.stats'.format(func)
    ficn = '/tmp/stats/{0}.cumulative.stats'.format(func)
    fict = '/tmp/stats/{0}.total.stats'.format(func)
    for i in [ficp, fico, ficn, fict, ficcl]:
        if os.path.exists(i):
            os.unlink(i)
    pr.dump_stats(ficp)
    with open(ficn, 'w') as fic:
        ps = pstats.Stats(
            pr, stream=fic).sort_stats('cumulative')
        ps.print_stats()
    with open(ficcl, 'w') as fic:
        ps = pstats.Stats(
            pr, stream=fic).sort_stats('calls')
        ps.print_stats()
    with open(fict, 'w') as fic:
        ps = pstats.Stats(
            pr, stream=fic).sort_stats('tottime')
        ps.print_stats()
    msr = __salt__['mc_locations.msr']()
    os.system(
        msr + '/bin/pyprof2calltree '
        '-i {0} -o {1}'.format(ficp, fico))
    return ret, ficp, fico, ficn, ficcl, fict


def manage_file(name, **kwargs):
    '''
    Easier wrapper to file.manage_file
    '''
    for i in [a for a in kwargs if '__' in a]:
        kwargs.pop(i, None)
    log.error(kwargs.keys())
    kwargs.setdefault('mode', '755')
    kwargs.setdefault('backup', None)
    kwargs.setdefault('contents', None)
    kwargs.setdefault('makedirs', True)
    kwargs.setdefault('user', 'root')
    kwargs.setdefault('group', 'root')
    kwargs.setdefault('saltenv', 'base')
    kwargs.setdefault('ret', None)
    kwargs.setdefault('sfn', None)
    kwargs.setdefault('source', None)
    kwargs.setdefault('source_sum', None)
    return __salt__['file.manage_file'](name, **kwargs)


def _outputters(outputter=None):
    outputters = salt.loader.outputters(__opts__)
    if outputter:
        return outputters[outputter]
    return outputters


def output(mapping, raw=False, outputter='highstate'):
    '''
    This return a formatted output
    '''
    color = __opts__.get('color', None)
    slashre = re.compile('[\\\]+', re.S | re.U | re.X)
    __opts__['color'] = not raw
    try:
        if isinstance(mapping, dict) and (outputter == 'highstate'):
            ret = _outputters(outputter)({'local': mapping})
        else:
            ret = _outputters(outputter)(mapping)
    except MemoryError:
        # try to print out something in RAW MODE
        mmapping = copy.deepcopy(mapping)
        # ugly hack inside:
        # on error while display message
        # with recursive \\, just try to strip them
        # and reuse the outputter
        try:
            if not isinstance(mmapping, dict):
                raise ValueError('not a dict, trying raw output')
            for state in [
                i for i in mmapping
                if isinstance(mmapping[i], dict)
            ]:
                if not isinstance(mmapping[state], dict):
                    continue
                for k in [
                    j for j in mmapping[state]
                    if isinstance(mapping[state][j], six.string_types)
                ]:
                    mmapping[state][k] = slashre.sub('', mmapping[state][k])
            if outputter == 'highstate':
                ret = _outputters(outputter)({'local': mmapping})
            else:
                ret = _outputters(outputter)(mmapping)
        except Exception:
            # try to print out something in RAW MODE
            # without outputter formatting
            try:
                ret = pformat(mmapping)
            except Exception:
                try:
                    ret = u"{0}".format(mmapping)
                except Exception:
                    try:
                        ret = "{0}".format(mmapping)
                    except Exception:
                        raise
    __opts__['color'] = color
    return ret


def get_container(pid):
    '''
    On a main host context, for a non containerized process
    this return MAIN_HOST

    On a container context, this return MAIN_HOST
    On a hpot context, this return MAIN_HOST


    '''
    context = 'MAIN_HOST'
    cg = '/proc/{0}/cgroup'.format(pid)
    content = ''
    # lxc ?
    if os.path.isfile(cg):
        with open(cg) as fic:
            content = fic.read()
            if 'lxc' in content:
                # 9:blkio:NAME
                context = content.split('\n')[0].split(':')[-1]
    if '/lxc' in context:
        context = context.split('/lxc/', 1)[1]
    if '/' in context and (
        '.service' in context or
        '.slice' in context or
        '.target' in context
    ):
        context = context.split('/')[0]
    if 'docker' in content:
        context = 'docker'
    return context


def is_this_lxc(pid=1):
    container = get_container(pid)
    if container not in ['MAIN_HOST']:
        return True
    envf = '/proc/{0}/environ'.format(pid)
    if os.path.isfile(envf):
        with open(envf) as fic:
            content = fic.read()
            if 'container=lxc' in content:
                return True
            if 'docker' in content:
                return True
            if os.path.exists('/.dockerinit'):
                return True
    return False


def filter_host_pids(pids):
    res = [pid for pid in pids
           if get_container(pid) != 'MAIN_HOST']
    return res


def cache_kwargs(*args, **kw):
    shared = {'__opts__': __opts__, '__salt__': __salt__}
    to_delete = [i for i in kw
                 if i.startswith('__') and i not in shared]
    dc = len(to_delete)
    for i in shared:
        if i not in kw:
            dc = True
    if dc:
        kw2 = {}
        for i in kw:
            kw2[i] = kw[i]
        kw = kw2
    [kw.pop(i, None) for i in to_delete]
    for i, val in six.iteritems(shared):
        if not kw.get(i):
            kw[i] = val
    return kw


def memoize_cache(*args, **kw):
    '''
    Wrapper for :meth:`~mc_states.api.memoize_cache` to set __opts__

    CLI Examples::

        salt-call -lall mc_pillar.memoize_cache test.ping

    '''
    return api.memoize_cache(*args, **cache_kwargs(*args, **kw))


def test_cache(ttl=120):
    '''.'''
    def _do():
        return "a"
    cache_key = 'mc_utils.test_cache'
    __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)
    ret = list_cache_keys()
    remove_cache_entry(ret[0], debug=True)
    return ret


def remove_entry(*args, **kw):
    '''
    Wrapper for :meth:`~mc_states.api.remove_cache_entry` to set __opts__
    '''
    return mc_states.api.remove_entry(*args, **cache_kwargs(*args, **kw))


def list_cache_keys(*args, **kw):
    '''
    Wrapper for :meth:`~mc_states.api.list_cache_keys` to set __opts__
    '''
    return mc_states.api.list_cache_keys(*args, **cache_kwargs(*args, **kw))


def remove_cache_entry(*args, **kw):
    '''
    Wrapper for :meth:`~mc_states.api.remove_cache_entry` to set __opts__
    '''
    return mc_states.api.remove_cache_entry(*args, **cache_kwargs(*args, **kw))


def get_mc_server(*args, **kw):
    '''
    Wrapper for :meth:`~mc_states.api.get_local_cache`
    '''
    return mc_states.api.get_mc_server(*args, **kw)


def get_local_cache(*args):
    '''
    Wrapper for :meth:`~mc_states.api.get_local_cache`
    '''
    return mc_states.api.get_local_cache(*args)


def register_memcache_first(pattern):
    '''
    Wrapper for :meth:`~mc_states.api.invalidate_memoize_cache` to set __opts__
    '''
    return mc_states.api.register_memcache_first(pattern)


def invalidate_memoize_cache(*args, **kw):
    '''
    Wrapper for :meth:`~mc_states.api.invalidate_memoize_cache` to set __opts__
    '''
    return mc_states.api.invalidate_memoize_cache(*args,
                                                  **cache_kwargs(*args, **kw))


def purge_memoize_cache(*args, **kw):
    '''
    Wrapper for :meth:`~mc_states.api.invalidate_memoize_cache` to set __opts__
    '''
    return mc_states.api.purge_memoize_cache(*args,
                                             **cache_kwargs(*args, **kw))


def cache_check(*args, **kw):
    '''
    Wrapper for :meth:`~mc_states.api.invalidate_memoize_cache` to set __opts__
    '''
    return mc_states.api.cache_check(*args, **cache_kwargs(*args, **kw))


def yencode(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.yencode`
    '''
    return __salt__['mc_dumper.yencode'](*args, **kw)


def cyaml_load(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.cyaml_load`
    '''
    return __salt__['mc_dumper.cyaml_load'](*args, **kw)


def yaml_load(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.yaml_load`
    '''
    return __salt__['mc_dumper.yaml_load'](*args, **kw)


def yaml_dump(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.old_yaml_dump`
    '''
    return __salt__['mc_dumper.old_yaml_dump'](*args, **kw)


def cyaml_dump(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.cyaml_dump`
    '''
    return __salt__['mc_dumper.cyaml_dump'](*args, **kw)


def old_yaml_dump(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.old_yaml_dump`
    '''
    return __salt__['mc_dumper.old_yaml_dump'](*args, **kw)


def nyaml_dump(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.yaml_dump`
    '''
    return __salt__['mc_dumper.yaml_dump'](*args, **kw)


def iyaml_dump(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.iyaml_dump`
    '''
    return __salt__['mc_dumper.iyaml_dump'](*args, **kw)


def msgpack_load(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.msgpack_load`
    '''
    return __salt__['mc_dumper.msgpack_load'](*args, **kw)


def msgpack_dump(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.old_msgpack_dump`
    '''
    return __salt__[
        'mc_dumper.msgpack_dump'](*args, **kw)


def json_load(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.json_load`
    '''
    return __salt__['mc_dumper.json_load'](*args, **kw)


def json_dump(*args, **kw):
    '''
    Retro compat to :meth:`mc_states.modules.mc_dump.old_json_dump`
    '''
    return __salt__['mc_dumper.json_dump'](*args, **kw)

def pdb(**kw):
    '''
    Add a breakpoint
    '''
    import pdb
    pdb.set_trace()

def epdb(**kw):
    '''
    add a network attachable breakpoint
    '''
    import epdb
    epdb.serve()


def deepcopy_unicode_free(data, done=None):
    if done is None:
        done = {}
    oid = id(data)
    if oid in done:
        return done[oid]
    else:
        done[oid] = data
    if isinstance(data, six.string_types):
        return magicstring(data)
    elif isinstance(data, list):
        ndata = []
        for i in data:
            ndata.append(unicode_free(i, done=done))
        return ndata
    elif isinstance(data, set):
        ndata = set()
        for i in data:
            ndata.add(unicode_free(i, done=done))
        return ndata
    elif isinstance(data, tuple):
        ndata = []
        for i in data:
            ndata.append(unicode_free(i, done=done))
        return tuple(ndata)
    elif isinstance(data, dict):
        ndata = type(data)()  # handle any class of mapping
        for i, val in six.iteritems(data):
            ndata[i] = unicode_free(data, done=done)
        return ndata
    else:
        return data


def unicode_free(data, done=None):
    if done is None:
        done = {}
    oid = id(data)
    if oid in done:
        return done[oid]
    else:
        done[oid] = data
    if isinstance(data, six.string_types):
        return magicstring(data)
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = unicode_free(data[i], done=done)
    elif isinstance(data, dict):
        for i in [a for a in data]:
            data[i] = unicode_free(data[i], done=done)
    elif isinstance(data, set):
        ndata = set()
        for i in data:
            ndata.add(unicode_free(i, done=done))
        return ndata
    elif isinstance(data, tuple):
        ndata = []
        for i in data:
            data.append(unicode_free(i, done=done))
        return ndata
    return data
