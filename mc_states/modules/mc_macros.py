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
import logging
import time
import traceback
from mc_states.utils import memoize_cache, invalidate_memoize_cache
from salt.exceptions import SaltException
from salt.utils.odict import OrderedDict
from mc_states.api import(
    _GLOBAL_KINDS,
    _SUB_REGISTRIES,
)

_default_activation_status = object()

# cache variable
_REGISTRY = {}
_LOCAL_REG_CACHE = {}
import yaml
from salt.utils import yamldumper
from salt.renderers.yaml import get_yaml_loader

log = logging.getLogger(__name__)
DEFAULT_SUF = 'makina-states.local'
DEFAULT_LOCAL_REG_NAME = '{0}.{{0}}'.format(DEFAULT_SUF)
RKEY = 'mcreg_{0}_{1}'
REGISTRY_FORMATS = ['pack', 'yaml']
_default = object()


def get_registry_formats():
    return copy.deepcopy(REGISTRY_FORMATS)


class NoRegistryLoaderFound(SaltException):
    """."""


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
    '''Look in pillar/grains/localconfig for registry
    activation status
    '''
    if not grains_pref:
        grains_pref = 'makina-states.{0}'.format(registry_name)
    local_reg = get_local_registry(registry_name)
    config_entry = grains_pref + "." + item
    if force:
        val = default_status
    else:
        val =  __salt__['mc_utils.get'](config_entry,
                                        default_status,
                                        local_registry=local_reg)
    return val


def load_kind_registries(kind):
    # load all registries
    if not kind in _REGISTRY:
        _REGISTRY[kind] = {}
    for registry in _SUB_REGISTRIES:
        if registry in _REGISTRY[kind]:
            continue
        try:
            _REGISTRY[kind][registry] = __salt__[
                'mc_{0}.{1}'.format(kind, registry)]()
        except KeyError:
            trace = traceback.format_exc()
            raise NoRegistryLoaderFound(
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
    return {
        'kind': kind,
        'bases': bases
    }


def is_active(registry, name):
    '''Is the queried service active in the registry'''
    try:
        return name in registry['actives']
    except:
        return False


def yaml_load_local_registry(name, registryf):
    with open(registryf, 'r') as fic:
        registry = yaml.load(fic, Loader=get_yaml_loader(''))
        if not registry:
            registry = {}
        return registry


def yaml_dump_local_registry(registry):
    content = yaml.dump(
        registry,
        default_flow_style=False,
        Dumper=yamldumper.SafeOrderedDumper)
    return content


def pack_load_local_registry(name, registryf):
    value = {}
    try:
        if os.path.exists(registryf):
            with open(registryf) as fic:
                rvalue = fic.read()
                value = msgpack.unpackb(rvalue)['value']
    except msgpack.exceptions.UnpackValueError:
        log.error('decoding error, removing stale {0}'.format(registryf))
        os.unlink(registryf)
        value = {}
    return value


def pack_dump_local_registry(registry):
    '''encode in a file using msgpack backend'''
    content = msgpack.packb({'value': registry})
    return content


def encode_local_registry(name, registry, registry_format='yaml'):
    locs = __salt__['mc_locations.settings']()
    not_shared = ['controllers', 'services', 'nodetypes',
                  'localsettings', 'cloud']

    if name not in not_shared:
        registryf = os.path.join(
            locs['conf_dir'], 'makina-states/{0}.{1}'.format(
                name, registry_format))
    else:
        registryf = os.path.join(
            __opts__['config_dir'], 'makina-states/{0}.{1}'.format(
                name, registry_format))
    dregistry = os.path.dirname(registryf)
    if not os.path.exists(dregistry):
        os.makedirs(dregistry)
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
        with open(registryf, 'w') as fic:
            fic.write(content)
    os.chmod(registryf, 0700)


def _get_local_registry(name,
                       cached=True,
                       cachetime=60,
                       registry_format='yaml'):
    '''Get local registry
    Masteralt & Salt share the local registries
    unless for the main ones:

        - controllers
        - services
        - nodetypes
        - localsettings
        - cloud

    For backward compatibility, we take care to load and merge
    shared registries in mastersalt & salt prefix if any is found.
    '''
    not_shared = ['controllers', 'services', 'nodetypes',
                  'localsettings', 'cloud']
    mastersalt_registryf = '{0}/makina-states/{1}.{2}'.format(
        '/etc/mastersalt',  name, registry_format)
    salt_registryf = '{0}/makina-states/{1}.{2}'.format(
        '/etc/salt',  name, registry_format)
    shared_registryf = os.path.join(
        '/etc/makina-states/{0}.{1}'.format(name, registry_format))
    # cache local registries one minute
    key = '{0}_{1}'.format('mcreg', name)
    if name not in not_shared:
        to_load = [mastersalt_registryf,
                   salt_registryf,
                   shared_registryf]
    else:
        to_load = [
            '{0}/makina-states/{1}.{2}'.format(
                __opts__['config_dir'], name, registry_format)
        ]
    def _do(name, to_load, registry_format):
        registry = OrderedDict()
        for registryf in to_load:
            dregistry = os.path.dirname(registryf)
            if not os.path.exists(dregistry):
                os.makedirs(dregistry)
            if os.path.exists(registryf):
                registry = __salt__[
                    'mc_utils.dictupdate'](
                        registry,
                        __salt__[
                            'mc_macros.{0}_load_local_registry'.format(
                                registry_format)](name, registryf))
                # unprefix local simple registries
                loc_k = DEFAULT_LOCAL_REG_NAME.format(name)
                for k in [t for t in registry if t.startswith(loc_k)]:
                    spl = loc_k + '.'
                    nk = spl.join(k.split(spl)[1:])
                    registry[nk] = registry[k]
                    registry.pop(k)
        return registry
    cache_key = RKEY.format(key, registry_format)
    force_run = not cached
    return memoize_cache(
        _do, [name, to_load, registry_format], {},
        cache_key, cachetime, force_run=force_run)


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
    return local_registry


def update_registry_params(registry_name, params, registry_format='yaml'):
    '''Update the desired local registry'''
    invalidate_memoize_cache(RKEY.format(registry_name, registry_format))
    registry = get_local_registry(
        registry_name, registry_format=registry_format)
    changes = {}
    topreg_name = 'mc_{0}.registry'.format(registry_name)
    default = True
    if topreg_name in __salt__:
        registry_obj = __salt__[topreg_name]()
        pref = registry_obj['grains_pref']
        default = False
    else:
        pref = DEFAULT_LOCAL_REG_NAME.format(registry_name)
    for param, value in params.items():
        gparam = param
        if (
            not param.startswith(pref)
            and not param.startswith('makina-states.')
        ):
            gparam = '{0}.{1}'.format(pref, param)
        if registry.get(gparam, _default) != value:
            for data in changes, registry:
                data.update({gparam: value})
        if (
            default
            and (not param.startswith('makina-states.'))
            and (param in registry)
        ):
            del registry[param]
    if changes:
        encode_local_registry(
            registry_name, registry, registry_format=registry_format)
        invalidate_memoize_cache(RKEY.format(registry_name, registry_format))
    return changes


def update_local_registry(registry_name, params, registry_format='yaml'):
    '''Alias to update_local_registry'''
    return update_registry_params(registry_name,
                                  params,
                                  registry_format=registry_format)


def get_registry(registry_configuration):
    """
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

    """
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
    '''Helper to factorise registry mappings'''
    metadata_reg = __salt__['mc_{0}.metadata'.format(name)]()
    if not defaults:
        defaults = {}
    return __salt__['mc_macros.get_registry']({
        'kind': metadata_reg['kind'],
        'bases': metadata_reg['bases'],
        'defaults': defaults,
    })


def unregister(kind, slss, data=None, suf=''):
    '''Unregister a/some service(s) in the local registry'''
    state = '\n'
    if isinstance(slss, basestring):
        slss = [slss]
    if slss is None:
        slss = []
    data = locals()
    if slss:
        data['name'] = '-'.join(slss)
        state += 'makina-states-unregister.{kind}.{name}{suf}:\n'.format(**data)
        state += '  mc_registry.absent:\n'
        state += '    - name: {kind}\n'.format(**data)
        state += '    - slss:\n'
        for sls in slss:
            state += '      - {0}\n'.format(sls)
        state += '    - order: 9999\n'
        state += '\n'
    return state


def register(kind, slss, data=None, suf=''):
    '''Register a/some service(s) in the local registry'''
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
    '''Helper to autoload & (un)register services in a top file'''
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


def dump():
    return _REGISTRY

# vim:set ai:
