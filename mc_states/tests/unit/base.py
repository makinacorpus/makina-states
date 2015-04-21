#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import copy
try:
    import unittest2 as unittest
except ImportError:
    import unittest


from salt.modules import grains as sgrains
from mc_states.modules import mc_localsettings as mmc_localsettings
from mc_states.modules import mc_pillar as mmc_pillar
from mc_states.modules import mc_utils as mmc_utils
from mc_states.modules import mc_dumper as mmc_dumper
from mc_states.modules import mc_locations as mmc_locations
from mc_states.modules import mc_macros as mmc_macros
from mc_states.modules import mc_ntp as mmc_ntp
from mc_states.modules import mc_remote as mmc_remote

from mc_states.renderers import lyaml as mmc_lyaml

import mc_states.tests.utils

J = os.path.join
D = os.path.dirname
STATES_DIR = J(D(D(D(__file__))), '_modules')
_NO_ATTR = object()
DUNDERS = {
    'default': {
        'opts': {
            'config_dir': '/etc/mastersalt',
            'extension_modules': '/var/cache/salt/salt-minion/extmods',
            'renderer': 'yaml_jinja',
        },
        'salt': {},
        'pillar': {},
        'grains': {},
        'context': {}}}
DUNDERS['modules'] = copy.deepcopy(DUNDERS['default'])
DUNDERS['modules']['salt'] = {
    'lyaml.render': mmc_lyaml.render,
    'mc_remote.sls': mmc_remote.sls_,
    'mc_remote.highstate': mmc_remote.highstate,
    'mc_remote.salt_call': mmc_remote.salt_call,
    'mc_remote.mastersalt_call': mmc_remote.mastersalt_call,
    'mc_remote.ssh': mmc_remote.ssh,
    'mc_remote.ssh_transfer_file': mmc_remote.ssh_transfer_file,
    'mc_remote.ssh_transfer_dir': mmc_remote.ssh_transfer_dir,
    'grains.filter_by': sgrains.filter_by,
    'mc_ntp.settings': mmc_ntp.settings,
    'mc_locations.settings': mmc_locations.settings,
    'mc_dumper.sanitize_kw': mmc_dumper.sanitize_kw,
    'mc_dumper.yencode': mmc_dumper.yencode,
    'mc_dumper.cyaml_load': mmc_dumper.cyaml_load,
    'mc_dumper.yaml_load': mmc_dumper.yaml_load,
    'mc_dumper.yaml_dump': mmc_dumper.yaml_dump,
    'mc_dumper.cyaml_dump': mmc_dumper.cyaml_dump,
    'mc_dumper.old_yaml_dump': mmc_dumper.old_yaml_dump,
    'mc_dumper.iyaml_dump': mmc_dumper.iyaml_dump,
    'mc_dumper.msgpack_load': mmc_dumper.msgpack_load,
    'mc_dumper.msgpack_dump': mmc_dumper.msgpack_dump,
    'mc_dumper.json_load': mmc_dumper.json_load,
    'mc_dumper.json_dump': mmc_dumper.json_dump,
    'mc_localsettings.get_pillar_sw_ip':
    mmc_localsettings.get_pillar_sw_ip,
    'mc_pillar.get_sysadmins_keys':
    mmc_pillar.get_sysadmins_keys,
    'mc_pillar.ip_for': mmc_pillar.ip_for,
    'mc_pillar.ips_for': mmc_pillar.ips_for,
    'mc_utils.yaml_dump':
    mmc_utils.yaml_dump,
    'mc_utils.yaml_load':
    mmc_utils.yaml_load,
    'mc_utils.msgpack_dump':
    mmc_utils.msgpack_dump,
    'mc_utils.msgpack_load':
    mmc_utils.msgpack_load,
    'mc_macros.yaml_load_local_registry':
    mmc_macros.yaml_load_local_registry,
    'mc_macros.yaml_load_local_registry':
    mmc_macros.yaml_load_local_registry,
    'mc_macros.yaml_dump_local_registry':
    mmc_macros.yaml_dump_local_registry,
    'mc_macros.pack_load_local_registry':
    mmc_macros.pack_load_local_registry,
    'mc_macros.pack_dump_local_registry':
    mmc_macros.pack_dump_local_registry,
    'mc_macros.get_local_registry':
    mmc_macros.get_local_registry,
    'mc_macros.update_local_registry':
    mmc_macros.update_local_registry,
    'mc_pillar.load_db': mmc_pillar.load_db,
    'mc_pillar.query': mmc_pillar.query,
    'mc_pillar.whitelisted': mmc_pillar.whitelisted,
    'mc_utils.local_minion_id': mmc_utils.local_minion_id,
    'mc_utils.format_resolve': mmc_utils.format_resolve,
    'mc_utils.defaults': mmc_utils.defaults,
    'mc_utils.magicstring': mmc_utils.magicstring,
    'mc_utils.get': mmc_utils.get,
    'mc_utils.dictupdate': mmc_utils.dictupdate,
    'mc_utils.uniquify': mmc_utils.uniquify,
    'mc_utils.unix_crypt': mmc_utils.unix_crypt,
    'mc_utils.invalidate_memoize_cache': mmc_utils.invalidate_memoize_cache,
    'mc_utils.generate_password': mmc_utils.generate_password,
    'mc_utils.memoize_cache': mmc_utils.memoize_cache}


class ModuleCase(unittest.TestCase):
    '''Base test class
    Its main function is to be used in salt modules
    and to mock the __salt__, __pillar__ and __grains__ attributes
    all in one place

    '''
    _mods = tuple()
    maxDiff = None
    _to_patch = ('salt', 'pillar', 'grains', 'opts', 'context')
    kind = 'modules'

    def reset_dunders(self):
        self.dunders = copy.deepcopy(DUNDERS)

    def setUp(self):
        '''
        1. Monkey patch the dunders (__salt__, __grains__ & __pillar__; etc)
        in the objects (certainly python modules) given in self.mods

            - This search in self._{grains, pillar, salt} for a dict containing
              the monkey patch replacement and defaults to {}
            - We will then have on the test class _salt, _grains & _pillar
              dicts to be used and mocked in tests, this ensure that the mock
              has to be done only at one place, on the class attribute.

        '''
        mc_states.tests.utils.test_setup()
        self.reset_dunders()
        for patched in self._to_patch:
            patch = self.dunders[self.kind].setdefault(patched, {})
            setattr(self, '_{0}'.format(patched), patch)
            for mod in self._mods:
                sav_attribute = '___mc_patch_{0}'.format(patched)
                attribute = '__{0}__'.format(patched)
                if hasattr(mod, sav_attribute):
                    raise ValueError('test conflict')
                if not hasattr(mod, sav_attribute):
                    setattr(mod, sav_attribute,
                            getattr(mod, attribute, _NO_ATTR))
                    setattr(mod, attribute, patch)

    def tearDown(self):
        '''
        1. Ungister any Monkey patch on  __salt__, __grains__ & __pillar__ in
        objects (certainly python modules) given in self.mods
        '''
        for mod in self._mods:
            for patched in self._to_patch:
                attribute = '__{0}__'.format(patched)
                sav_attribute = '___mc_patch_{0}'.format(patched)
                _patch = getattr(mod, sav_attribute, None)
                if _patch is not None:
                    if _patch is not _NO_ATTR:
                        setattr(mod, attribute, _patch)
                    else:
                        delattr(mod, attribute)
                    delattr(mod, sav_attribute)
                shortcut = '_{0}'.format(patched)
                if hasattr(self, shortcut):
                    delattr(self, shortcut)
        self.reset_dunders()
        mc_states.tests.utils.test_teardown()
# vim:set et sts=4 ts=4 tw=80:
