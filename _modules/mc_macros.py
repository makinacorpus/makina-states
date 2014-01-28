# -*- coding: utf-8 -*-
'''
Some usefull small tools
============================================

'''

import unittest
# Import salt libs
import salt.utils
import os
import salt.utils.dictupdate
from salt.exceptions import SaltException

_default_activation_status = object()

# cache variable
_REGISTRY = {}


def registry_kind_get(kind):
    if not kind in _REGISTRY:
        _REGISTRY[kind] = {}
    return _REGISTRY[kind]

def registry_kind_set(kind, value):
    _REGISTRY[kind] = value


def is_item_active(config_entry, default_status=False):
    return __salt__['mc_utils.get'](
        config_entry, default_status)


def load_registries():
    # load all registries
    for reg in [
        'localsettings',
        'services',
        'controllers',
        'nodetypes',
    ]:
        # load the registry
        __salt__['mc_{0}.registry'.format(reg)]()
    return _REGISTRY


def kinds():
    # py3 compatible dict keys()
    return [a for a in __salt__['mc_macros.load_registries']()]


def metadata(kind, grain=None, state=None, bases=None):
    if bases is None:
        bases = []
    return {
        'kind': kind,
        'bases': bases
    }


def get_registry(registry_configuration):
    """
    Mangle a registry of activated/unactived states to be run
    as part of the automatic highstate inclusion.

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
    registry['grains_pref'] = 'makina-states.{0}'.format(registry['kind'])
    registry['states_pref'] = 'makina-states.{0}'.format(registry['kind'])
    if not 'actives' in registry:
        registry['actives'] = {}
    if not 'unactivated' in registry:
        registry['unactivated'] = {}
    if not 'availables' in registry:
        registry['availables'] = {}
    for item, data in registry['defaults'].items():
        activation_status = _default_activation_status
        if isinstance(data, dict):
            activation_status = is_item_active(
                registry['grains_pref'] + "." + item,
                data.get('active', activation_status))
            if activation_status is not _default_activation_status:
                if activation_status:
                    registry['actives'][item] = data
                else:
                    registry['unactivated'][item] = data
            else:
                registry['availables'][item] = data
    return registry


def construct_registry_configuration(settings, defaults=None):
    metadata = settings['metadata']
    if not defaults:
        defaults = {}
    return __salt__['mc_macros.get_registry']({
        'kind': metadata['kind'],
        'bases': metadata['bases'],
        'defaults': defaults,
    })


def is_active(registry, kind, name):
    try:
        return name in registry[kind]['actives']
    except:
        return False


def unregister(kind, name, data=None, suf=''):
    state = '\n'
    data = locals()
    state += 'makina-states-register.{kind}.{name}{suf}:\n'.format(**data)
    state += '  grains.present:\n'
    state += '    - name: makina-states.{kind}.{name}\n'.format(**data)
    state += '    - value: False\n'.format(**data)
    state += '\n'
    return state


def register(kind, name, data=None, suf=''):
    state = '\n'
    data = locals()
    state += 'makina-states-register.{kind}.{name}{suf}:\n'.format(**data)
    state += '  grains.present:\n'
    state += '    - name: makina-states.{kind}.{name}\n'.format(**data)
    state += '    - value: True\n'.format(**data)
    state += '\n'
    return state


def autoinclude(reg):
    sls = ''
    bases = reg.get('bases', [])
    includes= []
    for base in bases:
        includes.append('  - makina-states.{base}\n'.format(base=base))
    for state, data in reg.get('actives', {}).items():
        includes.append('  - {rstatesPref}.{state}\n'.format(
            rstatesPref=reg['states_pref'], state=state))
    if includes:
        includes.insert(0, 'include:\n')
        sls += ''.join(includes)
    for state, data in reg.get('actives', {}).items():
        sls += '\n{0}\n'.format(
            __salt__['mc_macros.register'](
                reg['kind'], state, data, suf='auto'))
    for state, data in reg.get('unactivated', {}).items():
        sls += '\n{0}\n'.format(
            __salt__['mc_macros.unregister'](
                reg['kind'], state, data, suf='auto'))
    return sls

# vim:set ai:
