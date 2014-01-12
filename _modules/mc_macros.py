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


def is_item_active(config_entry, default_status=False):
    return __salt__['mc_utils.get'](
        config_entry, default_status)


def get_registries(registries_configurations):
    """
    Mangle a registry of activated/unactived states to be run
    as part of the automatic highstate inclusion.

    controllers_kind: {
        'states_pref': states_pref, 'grains_pref': grains_pref,
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

    controllers_kind: {
        'states_pref': states_pref, 'grains_pref': grains_pref,
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
    registries = registries_configurations.copy()
    for kind in registries.copy():
        registry = registries[kind]
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
                    registry['grains_pref'] + item,
                    data.get('active', activation_status))
                if activation_status is not _default_activation_status:
                    if activation_status:
                        registry['actives'][item] = data
                    else:
                        registry['unactivated'][item] = data
                else:
                    registry['availables'][item] = data
    return registries


def is_active(registry, kind, name):
    try:
        return name in registry[kind]['actives']
    except:
        return False
