# -*- coding: utf-8 -*-
'''
.. _module_mc_macros:

mc_macros / macros helpers
============================================

'''

# Import salt libs
import os
import traceback
from salt.exceptions import SaltException
from salt.utils.odict import OrderedDict

_default_activation_status = object()

# cache variable
_REGISTRY = {}
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
import yaml
from salt.utils import yamldumper
from salt.renderers.yaml import get_yaml_loader


class NoRegistryLoaderFound(SaltException):
    """."""


def registry_kind_get(kind):
    if not kind in _REGISTRY:
        _REGISTRY[kind] = {}
    return _REGISTRY[kind]


def registry_kind_set(kind, value):
    _REGISTRY[kind] = value


def is_item_active(registry_name,
                   item,
                   default_status=False,
                   grains_pref=None):
    '''Look in pillar/grains/localconfig for registry
    activation status
    '''
    if not grains_pref:
        grains_pref = 'makina-states.{0}'.format(registry_name)
    local_reg = get_local_registry(registry_name)
    config_entry = grains_pref + "." + item
    return __salt__['mc_utils.get'](config_entry,
                                    default_status,
                                    local_registry=local_reg)


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
    return [a
            for a in __salt__['mc_macros.load_registries']()
            if a in _GLOBAL_KINDS]


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


def encode_local_registry(name, registry):
    registryf = os.path.join(
        __opts__['config_dir'], 'makina-states/{0}.yaml'.format(name))
    dregistry = os.path.dirname(registryf)
    if not os.path.exists(dregistry):
        os.makedirs(dregistry)
    content = yaml.dump(
        registry,
        default_flow_style=False,
        Dumper=yamldumper.SafeOrderedDumper)
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


def get_local_registry(name):
    registryf = os.path.join(
        __opts__['config_dir'], 'makina-states/{0}.yaml'.format(name))
    dregistry = os.path.dirname(registryf)
    if not os.path.exists(dregistry):
        os.makedirs(dregistry)
    registry = OrderedDict()
    if os.path.exists(registryf):
        with open(registryf, 'r') as fic:
            registry = yaml.load(fic, Loader=get_yaml_loader(''))
    return registry


_default = object()


def update_registry_params(registry_name, params):
    registry = get_local_registry(registry_name)
    changes = {}
    registry_obj = __salt__['mc_{0}.registry'.format(registry_name)]()
    for param, value in params.items():
        gparam = '{0}.{1}'.format(registry_obj['grains_pref'],
                                  param)
        if registry.get(gparam, _default) != value:
            for data in changes, registry:
                data.update({gparam: value})
    if changes:
        encode_local_registry(registry_name, registry)
    return changes


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
            activation_status = is_item_active(
                registry['kind'], item,
                default_status=data.get('active', activation_status))
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
        __salt__['mc_macros.register'](
            reg['kind'], slss, data=data, suf='auto'))
    slss = []
    for state, data in reg.get('unactivated', {}).items():
        slss.append(state)
    sls += '\n{0}\n'.format(
        __salt__['mc_macros.unregister'](
            reg['kind'], slss, data=data, suf='auto'))
    return sls


def dump():
    return _REGISTRY

# vim:set ai:
