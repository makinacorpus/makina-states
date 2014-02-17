# -*- coding: utf-8 -*-
'''
mc_macros / macros helpers
============================================

'''

# Import salt libs
import traceback
from salt.exceptions import SaltException

_default_activation_status = object()

# cache variable
_REGISTRY = {}
_GLOBAL_KINDS = [
    'localsettings',
    'services',
    'controllers',
    'nodetypes',
]
_SUB_REGISTRIES = [
    'metadata',
    'settings',
    'registry',
]


class NoRegistryLoaderFound(SaltException):
    """."""


def registry_kind_get(kind):
    if not kind in _REGISTRY:
        _REGISTRY[kind] = {}
    return _REGISTRY[kind]


def registry_kind_set(kind, value):
    _REGISTRY[kind] = value


def is_item_active(config_entry, default_status=False):
    return __salt__['mc_utils.get'](config_entry, default_status)


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
                registry['grains_pref'] + "." + item,
                data.get('active', activation_status))
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


def construct_registry_configuration(__name, defaults=None):
    '''Helper to factorise registry mappings'''
    settings_reg = __salt__['mc_{0}.settings'.format(__name)]()
    metadata_reg = __salt__['mc_{0}.metadata'.format(__name)]()
    if not defaults:
        defaults = {}
    return __salt__['mc_macros.get_registry']({
                'kind': metadata_reg['kind'],
        'bases': metadata_reg['bases'],
        'defaults': defaults,
    })



def unregister(kind, name, data=None, suf=''):
    '''Unregister a service via a grain'''
    state = '\n'
    data = locals()
    state += 'makina-states-register.{kind}.{name}{suf}:\n'.format(**data)
    state += '  grains.present:\n'
    state += '    - name: makina-states.{kind}.{name}\n'.format(**data)
    state += '    - value: False\n'.format(**data)
    state += '    - order: 9999\n'
    state += '\n'
    return state


def register(kind, name, data=None, suf=''):
    '''Register a service via a grain'''
    state = '\n'
    data = locals()
    state += 'makina-states-register.{kind}.{name}{suf}:\n'.format(**data)
    state += '  grains.present:\n'
    state += '    - name: makina-states.{kind}.{name}\n'.format(**data)
    state += '    - value: True\n'.format(**data)
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
    for state, data in reg.get('actives', {}).items():
        sls += '\n{0}\n'.format(
            __salt__['mc_macros.register'](
                reg['kind'], state, data, suf='auto'))
    for state, data in reg.get('unactivated', {}).items():
        sls += '\n{0}\n'.format(
            __salt__['mc_macros.unregister'](
                reg['kind'], state, data, suf='auto'))
    return sls


def dump():
    return _REGISTRY

# vim:set ai:
