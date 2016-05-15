# -*- coding: utf-8 -*-
'''
.. _module_mc_macros:

mc_macros / macros helpers
============================================

'''

# Import salt libs
import msgpack
import os
import copy
import json
import tempfile
import hashlib
import logging
import time
import traceback
import yaml
from salt.utils import yamldumper
from salt.renderers.yaml import get_yaml_loader
from salt.exceptions import SaltException
from salt.utils.odict import OrderedDict
from mc_states.api import _GLOBAL_KINDS
from mc_states.api import _SUB_REGISTRIES
import mc_states.api
import mc_states.saltapi

# retrocompat
from mc_states.saltapi import NoRegistryLoaderFound


six = mc_states.api.six

# cache variable
_REGISTRY = {}
_default_activation_status = object()
_LOCAL_REG_CACHE = {}



NOT_SHARED = ['controllers', 'services', 'nodetypes',
              'services_managers', 'localsettings', 'cloud']
log = logging.getLogger(__name__)
DEFAULT_SUF = 'makina-states.local'
DEFAULT_LOCAL_REG_NAME = '{0}.{{0}}'.format(DEFAULT_SUF)
RKEY = 'mcreg_{0}_{1}'
REGISTRY_FORMATS = ['pack', 'yaml']
_default = object()


def get_registry_formats():
    return copy.deepcopy(REGISTRY_FORMATS)


# normally not more used
# def registry_kind_get(kind):
#     if not kind in _REGISTRY:
#         _REGISTRY[kind] = {}
#     return _REGISTRY[kind]
# def registry_kind_set(kind, value):
#     _REGISTRY[kind] = value


def is_item_active(registry_name,
                   item,
                   default_status=False,
                   grains_pref=None,
                   force=False):
    '''
    Look in pillar/grains/localconfig for registry
    activation status
    '''
    if not grains_pref:
        grains_pref = 'makina-states.{0}'.format(registry_name)
    local_reg = get_local_registry(registry_name)
    for config_entry in [
        grains_pref + ".is." + item,
        grains_pref + "." + item
    ]:
        if force:
            val = default_status
        else:
            val = __salt__['mc_utils.get'](config_entry,
                                           _default,
                                           local_registry=local_reg)
        if val is not _default:
            break
    if val is _default:
        val = default_status
    return val


def get_lock_name(registry_name, registry_format):
    lockp = 'localregistry_{0}_{1}'.format(registry_name, registry_format)
    return lockp


def load_kind_registries(kind):
    # load all registries
    if kind not in _REGISTRY:
        _REGISTRY[kind] = {}
    for registry in _SUB_REGISTRIES:
        if registry in _REGISTRY[kind]:
            continue
        try:
            _REGISTRY[kind][registry] = __salt__[
                'mc_{0}.{1}'.format(kind, registry)]()
        except KeyError:
            trace = traceback.format_exc()
            raise mc_states.saltapi.NoRegistryLoaderFound(
                'mc_{0}.{1} is unavailable\n{2}'.format(kind, registry, trace))
    return _REGISTRY[kind]


def load_registries():
    # load all registries
    for kind in _GLOBAL_KINDS:
        load_kind_registries(kind)
    return sorted([a for a in _REGISTRY])


def kinds():
    # py3 compatible dict keys()
    return [a for a in _GLOBAL_KINDS]


def metadata(kind, grain=None, state=None, bases=None):
    if bases is None:
        bases = []
    return {'kind': kind, 'bases': bases}


def is_active(registry, name):
    '''
    Is the queried service active in the registry
    '''
    try:
        return name in registry['actives']
    except:
        return False


def get_registry_paths(name, registry_format='pack'):
    locs = __salt__['mc_locations.settings']()
    etc = locs['conf_dir']
    confs = {
        'mastersalt': '{0}/{1}/makina-states/{2}.{3}'.format(
            etc, 'mastersalt',  name, registry_format),
        'salt': '{0}/{1}/makina-states/{2}.{3}'.format(
            etc, 'salt',  name, registry_format),
        'global': '{0}/{1}/{2}.{3}'.format(
            etc, 'makina-states',  name, registry_format),
        'context': '{0}/makina-states/{1}.{2}'.format(
            __opts__['config_dir'],  name, registry_format)}
    return confs


def get_registry_path(name,
                      registry_format='yaml',
                      registryf=None,
                      context=None):
    confs = get_registry_paths(
        name, registry_format=registry_format)
    if registryf and os.path.exists(registryf):
        return registryf
    if context is None or context not in confs:
        if name in NOT_SHARED:
            context = 'context'
        else:
            context = 'global'
    registryf = confs[context]
    return registryf


def json_load_local_registry(name, registryf=None):

    try:
        with open(
            get_registry_path(name,
                              registryf=registryf,
                              registry_format='json')
        ) as f:
            registry = __salt__['mc_utils.json_load'](f.read())
    except IOError:
        pass
    if not registry:
        registry = {}
    return registry


def json_dump_local_registry(registry):
    content = __salt__['mc_utils.json_dump'](registry,
                                             pretty=True)
    return content


def yaml_load_local_registry(name, registryf=None):
    registry = __salt__['mc_utils.yaml_load'](
        get_registry_path(name,
                          registryf=registryf,
                          registry_format='yaml'),
        is_file=True)
    if not registry:
        registry = {}
    return registry


def yaml_dump_local_registry(registry):
    content = __salt__['mc_utils.yaml_dump'](registry,
                                             nonewline=False)
    return content


def pack_load_local_registry(name, registryf=None):
    value = {}
    regpath = get_registry_path(name,
                                registryf=registryf,
                                registry_format='pack')
    try:
        if os.path.exists(regpath):
            with open(regpath) as fic:
                rvalue = fic.read()
                value = __salt__['mc_utils.msgpack_load'](
                    rvalue)
    except msgpack.exceptions.UnpackValueError:
        log.error('decoding error, removing stale {0}'.format(regpath))
        os.unlink(registryf)
        value = {}
    return value


def pack_dump_local_registry(registry):
    '''
    encode in a file using msgpack backend
    '''
    return __salt__['mc_utils.msgpack_dump'](registry)


def encode_local_registry(name, registry, registry_format='yaml'):
    lockp = get_lock_name(name, registry_format)
    with mc_states.api.wait_lock(lockp):
        registryf = get_registry_path(
            name, registry_format=registry_format)
        dregistry = os.path.dirname(registryf)
        content = __salt__[
            'mc_macros.{0}_dump_local_registry'.format(
                registry_format)](registry)
        sync = False
        if os.path.exists(registryf):
            with open(registryf) as fic:
                old_content = fic.read()
                if old_content != content:
                    sync = True
        else:
            sync = True
        if sync:
            if not os.path.exists(dregistry):
                os.makedirs(dregistry)
            with open(registryf, 'w') as fic:
                fic.write(content)
        os.chmod(registryf, 0700)


def _get_local_registry(name,
                        cached=True,
                        cachetime=60,
                        registry_format='yaml'):
    '''
    Get local registry
    Masteralt & Salt share all the local registries
    unless for the main ones:

        - controllers
        - services
        - nodetypes
        - localsettings
        - cloud

    For backward compatibility, we take care to load and merge
    shared registries in mastersalt & salt prefix if any is found.
    '''
    # cache local registries one minute
    key = '{0}_{1}'.format('mcreg', name)
    if name not in NOT_SHARED:
        to_load = ['global', 'context']
    else:
        to_load = ['context']

    def _do(name, to_load, registry_format):
        registryfs = get_registry_paths(
            name, registry_format=registry_format)
        registry = OrderedDict()
        for prefix in to_load:
            registryf = registryfs[prefix]
            # dregistry = os.path.dirname(registryf)
            # if not os.path.exists(dregistry):
            #     os.makedirs(dregistry)
            if os.path.exists(registryf):
                data = __salt__[
                    'mc_macros.{0}_load_local_registry'.format(
                        registry_format)](name, registryf)
                registry = __salt__['mc_utils.dictupdate'](registry, data)
                _unprefix(registry, name)
        return registry
    cache_key = RKEY.format(key, registry_format)
    force_run = not cached
    lockp = get_lock_name(name, registry_format)
    with mc_states.api.wait_lock(lockp):
        return __salt__['mc_utils.memoize_cache'](
            _do, [name, to_load, registry_format], {},
            cache_key, cachetime, use_memcache=False,
            force_run=force_run)


def _unprefix(registry, name):
    # unprefix local simple registries
    loc_k = DEFAULT_LOCAL_REG_NAME.format(name)
    for k in [t for t in registry if t.startswith(loc_k)]:
        spl = loc_k + '.'
        nk = spl.join(k.split(spl)[1:])
        registry[nk] = registry[k]
        registry.pop(k)
    return registry


def get_local_registry(name,
                       cached=True,
                       cachetime=60,
                       registry_format='yaml'):
    local_registry = _get_local_registry(
        name,
        cached=cached,
        cachetime=cachetime,
        registry_format=registry_format)
    # try to find the localreg in another format
    if not local_registry:
        formats = [
            a
            for a in get_registry_formats()
            if not a == registry_format]
        for f in formats:
            local_registry = _get_local_registry(
                name,
                cached=cached,
                cachetime=cachetime,
                registry_format=f)
            if local_registry:
                break
    _unprefix(local_registry, name)
    return local_registry


def update_registry_params(registry_name, params, registry_format='yaml'):
    '''
    Update the desired local registry
    '''
    __salt__['mc_utils.invalidate_memoize_cache'](
        RKEY.format(registry_name, registry_format))
    registry = get_local_registry(registry_name,
                                  cached=False,
                                  registry_format=registry_format)
    changes = {}
    topreg_name = 'mc_{0}.registry'.format(registry_name)
    default = True
    if topreg_name in __salt__:
        registry_obj = __salt__[topreg_name]()
        pref = registry_obj['grains_pref']
        default = False
    else:
        pref = DEFAULT_LOCAL_REG_NAME.format(registry_name)
    for param, value in six.iteritems(params):
        gparam = param
        if (
            not param.startswith(pref) and
            not param.startswith('makina-states.')
        ):
            gparam = '{0}.{1}'.format(pref, param)
        reg_value = registry.get(gparam, _default)
        if reg_value != value:
            for data in changes, registry:
                data.update({gparam: value})
        if (
            default and
            (not param.startswith('makina-states.')) and
            (param in registry)
        ):
            del registry[param]
    if changes:
        encode_local_registry(
            registry_name, registry, registry_format=registry_format)
        __salt__['mc_utils.invalidate_memoize_cache'](
            RKEY.format(registry_name, registry_format))
    return changes


def update_local_registry(registry_name, params, registry_format='yaml'):
    '''
    Alias to update_local_registry
    '''
    ret = update_registry_params(registry_name,
                                 params,
                                 registry_format=registry_format)
    return ret


def get_registry(registry_configuration):
    '''
    Mangle a registry of activated/unactived states to be run
    as part of the automatic highstate inclusion.

    ::

        {
            'kind': 'foo',
            'bases': ['localsettings'],
            'defaults': {
               'mastersalt_minion': {'active': False},
               'mastersalt_master': {'active': False},
               'salt_minion': {'active': False},
               'salt_master': {'active': True}
              }
            }
        }

    Will activate the 'makina-states.controllers.salt_master' and
    deactivate all other states to be automaticly run

    EG, for automatic activation of firewalld,
    lookup in Configs for this key (pillar, grains, reg)::

        makina-states.services.is.firewall.firewalld: true
        makina-states.services.firewall.firewalld: true


    Idea why for the dict containing 'active', i did not choosed
    a simple boolean is to support other data in the near future.

    We return here a registry in the form::

        {
            'kind': 'foo',
            'bases': ['localsettings'],
            'states_pref': 'makina-states.foo',
            'grains_pref': 'makina-states.foo',
            'activated': {'salt_master': {'active': True}},
            'unactivated': {
               'mastersalt_minion': {'active': False},
               'mastersalt_master': {'active': False},
               'salt_minion': {'active': False},
            },
            'defaults': {
               'mastersalt_minion': {'active': False},
               'mastersalt_master': {'active': False},
               'salt_minion': {'active': False},
               'salt_master': {'active': True}
              }
            }
        }

    '''
    registry = registry_configuration.copy()
    registry.setdefault('is', {})
    registry['grains_pref'] = 'makina-states.{0}'.format(registry['kind'])
    registry['states_pref'] = 'makina-states.{0}'.format(registry['kind'])
    registry.setdefault('actives', {})
    registry.setdefault('unactivated', {})
    registry.setdefault('availables', {})
    for item, data in registry['defaults'].items():
        activation_status = _default_activation_status
        if isinstance(data, dict):
            activation_status = __salt__[
                'mc_macros.is_item_active'](
                    registry['kind'],
                    item,
                    default_status=data.get('active',
                                            activation_status),
                    force=data.get('force', False))
            if activation_status is not _default_activation_status:
                if activation_status:
                    registry['actives'][item] = data
                    registry['is'][item] = True
                else:
                    registry['unactivated'][item] = data
                    registry['is'][item] = False
            else:
                registry['availables'][item] = data
    # synonym has for is
    registry['has'] = registry['is']
    return registry


def construct_registry_configuration(name, defaults=None):
    '''
    Helper to factorise registry mappings
    '''
    metadata_reg = __salt__['mc_{0}.metadata'.format(name)]()
    if not defaults:
        defaults = {}
    return __salt__['mc_macros.get_registry']({
        'kind': metadata_reg['kind'],
        'bases': metadata_reg['bases'],
        'defaults': defaults})


def unregister(kind, slss, data=None, suf=''):
    '''
    Unregister a/some service(s) in the local registry
    '''
    state = '\n'
    if isinstance(slss, basestring):
        slss = [slss]
    if slss is None:
        slss = []
    data = locals()
    if slss:
        data['name'] = '-'.join(slss)
        state += (
            'makina-states-unregister.{kind}'
            '.{name}{suf}:\n').format(**data)
        state += '  mc_registry.absent:\n'
        state += '    - name: {kind}\n'.format(**data)
        state += '    - slss:\n'
        for sls in slss:
            state += '      - {0}\n'.format(sls)
        state += '    - order: 9999\n'
        state += '\n'
    return state


def register(kind, slss, data=None, suf=''):
    '''
    Register a/some service(s) in the local registry
    '''
    state = '\n'
    if isinstance(slss, basestring):
        slss = [slss]
    if slss is None:
        slss = []
    data = locals()
    if slss:
        data['name'] = '-'.join(slss)
        state += 'makina-states-register.{kind}.{name}{suf}:\n'.format(**data)
        state += '  mc_registry.present:\n'
        state += '    - name: {kind}\n'.format(**data)
        state += '    - slss:\n'
        for sls in slss:
            state += '      - {0}\n'.format(sls)
        state += '    - order: 9999\n'
        state += '\n'
    return state


def autoinclude(reg, additional_includes=None):
    '''
    Helper to autoload & (un)register services in a top file
    '''
    sls = ''
    if not additional_includes:
        additional_includes = []
    bases = reg.get('bases', [])
    includes = []
    slses = []
    for base in bases:
        includes.append('  - makina-states.{base}\n'.format(base=base))
        slses.append('makina-states.{base}\n'.format(base=base))
    for state, data in reg.get('actives', {}).items():
        includes.append('  - {rstatesPref}.{state}\n'.format(
            rstatesPref=reg['states_pref'], state=state))
        slses.append('{rstatesPref}.{state}\n'.format(
            rstatesPref=reg['states_pref'], state=state))
    includes.extend(['  - {0}\n'.format(a)
                     for a in additional_includes])
    slses.extend(['{0}\n'.format(a) for a in additional_includes])
    if includes:
        includes.insert(0, 'include:\n')
        sls += ''.join(includes)

# more harm than good, cycle errors are too easilly triggered
# between kinds
#sls += '''
#{kind}-postinstall-hook:
#  mc_proxy.hook:
#    - watch:
#{requires}
#'''.format(kind=reg['kind'], requires='\n'.join(
#                    ['      - sls: {0}'.format(s) for s in slses]))
    slss = []
    for state, data in reg.get('actives', {}).items():
        slss.append(state)
    sls += '\n{0}\n'.format(
        __salt__['mc_macros.register'](reg['kind'], slss,  suf='auto'))
    slss = []
    for state, data in reg.get('unactivated', {}).items():
        slss.append(state)
    sls += '\n{0}\n'.format(
        __salt__['mc_macros.unregister'](reg['kind'], slss, suf='auto'))
    return sls


def get_local_cache_key(key):
    return mc_states.saltapi.get_cache_key(key, __opts__)


def _cache_entry(local_reg, key, ttl=1):
    data = local_reg.get(key, OrderedDict())
    if not isinstance(data, dict):
        data = OrderedDict()
    data.setdefault('ttl', ttl)
    data.setdefault('value', _default)
    data.setdefault('time', time.time())
    return data


def default_cache_value():
    return _default


def store_local_cache(registry, local_reg, ttl=1):
    now = time.time()
    # expire old entries
    for k in [a for a in local_reg]:
        data = _cache_entry(local_reg, k)
        if now > data['time'] + data['ttl']:
            local_reg.pop(k, None)
    __salt__['mc_macros.update_local_registry'](
        registry, local_reg, registry_format='pack')
    local_reg = __salt__['mc_macros.get_local_registry'](
        registry, registry_format='pack')
    return local_reg


def save_local_cached_entry(value,
                            key=None,
                            sha1_key=None,
                            ttl=1,
                            registry='disk_cache'):
    if not (key or sha1_key):
        raise ValueError('provide at least key or sha1_key')
    if not sha1_key:
        sha1_key = get_local_cache_key(key)
    local_reg = __salt__['mc_macros.get_local_registry'](
        registry, registry_format='pack')
    data = _cache_entry(local_reg, sha1_key, ttl=ttl)
    now = time.time()
    if (now > data['time'] + ttl) or (value is not _default):
        data['ttl'] = ttl
        data['time'] = now
        data['value'] = value
        local_reg[sha1_key] = data
        local_reg = store_local_cache(registry,
                                      local_reg,
                                      ttl=ttl)
    return local_reg


def get_local_cached_entry(key,
                           default=_default,
                           ttl=1,
                           soft=False,
                           registry='disk_cache'):
    local_reg = __salt__['mc_macros.get_local_registry'](
        registry, registry_format='pack')
    sha1_key = get_local_cache_key(key)
    data = _cache_entry(local_reg, sha1_key, ttl=ttl)
    now = time.time()
    value = _default
    if ttl and (now <= data['time'] + ttl):
        value = data['value']
    data['value'] = value
    if value is _default and not soft:
        raise KeyError(key)
    return data


def filecache_fun(func,
                  args=None,
                  kwargs=None,
                  registry='disk_cache',
                  prefix=None,
                  ttl=1):
    '''
    Execute a function and store the result in a filebased cache

    func
        func to execute
    args
        positional args to func
    kwargs
        kwargs to func
    registry
        name of the file inside /etc/makina-states
    prefix
        cache key
    ttl
        if 0: do not use cache
    '''

    if isinstance(kwargs, dict):
        kwargs = copy.deepcopy(kwargs)
        for k in [a for a in kwargs]:
            if k.startswith('__pub_'):
                kwargs.pop(k, None)
    if not prefix:
        prefix = '{0}'.format(func)
    key = '{0}_'.format(prefix)
    try:
        key += json.dumps(args)
    except TypeError:
        try:
            key += '{0}'.format(repr(args))
        except Exception:
            key += ''
    try:
        key += json.dumps(kwargs)
    except TypeError:
        try:
            key += '{1}'.format(repr(kwargs))
        except Exception:
            key += ''
    data = get_local_cached_entry(key, ttl=ttl, soft=True)
    value = data['value']
    # if value is default, we have either no value
    # or the cache entry was expired
    if value is _default:
        if args is not None and kwargs is not None:
            value = func(*args, **kwargs)
        elif args is not None and (kwargs is None):
            value = func(*args)
        elif (args is None) and kwargs is not None:
            value = func(**kwargs)
        else:
            value = func()
        try:
            save_local_cached_entry(value,
                                    key,
                                    registry=registry,
                                    ttl=ttl)
        except Exception:
            log.error(traceback.format_exc())
            # dont fail for a failed cache set
    else:
        log.garbage('Using filecache !')
    return value


def glob_dump():
    try:
        return copy.deepcopy(_GLOBAL_KINDS)
    except (TypeError, ValueError):
        return _GLOBAL_KINDS


def sub_dump():
    try:
        return copy.deepcopy(_SUB_REGISTRIES)
    except (TypeError, ValueError):
        return _SUB_REGISTRIES


def dump():
    try:
        return copy.deepcopy(_REGISTRY)
    except (TypeError, ValueError):
        return _REGISTRY
# vim:set ai:
