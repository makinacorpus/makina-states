# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
import unittest
from .. import base
from mc_states.modules import (
    mc_utils,
    mc_locations,
    mc_macros
)
from mock import patch, Mock


class TestCase(base.ModuleCase):
    _mods = (mc_macros, mc_locations, mc_utils)

    def test_get_regitry_paths(self):
        locs = mc_locations.settings()
        with patch.dict(
            mc_macros.__opts__, {'config_dir': 'salt'}
        ):
            ret = mc_macros.get_registry_paths('myreg')
            self.assertEqual(
                ret,
                {'context':
                 '{root_dir}etc/salt/makina-states/myreg.pack'.format(**locs),
                 'global':
                 '{root_dir}etc/makina-states/myreg.pack'.format(**locs),
                 'mastersalt':
                 '{root_dir}etc/mastersalt/'
                 'makina-states/myreg.pack'.format(**locs),
                 'salt':
                 '{root_dir}etc/salt/'
                 'makina-states/myreg.pack'.format(**locs)})
        with patch.dict(
            mc_macros.__opts__, {'config_dir': 'mastersalt'}
        ):
            ret = mc_macros.get_registry_paths('myreg')
            self.assertEqual(
                ret,
                {'context':
                 '{root_dir}etc/mastersalt/'
                 'makina-states/myreg.pack'.format(**locs),
                 'global':
                 '{root_dir}etc/makina-states/'
                 'myreg.pack'.format(**locs),
                 'mastersalt':
                 '{root_dir}etc/mastersalt/'
                 'makina-states/myreg.pack'.format(**locs),
                 'salt':
                 '{root_dir}etc/salt/makina-states/'
                 'myreg.pack'.format(**locs)})

    def test_load_registries(self):
        self.assertEquals(mc_macros._REGISTRY, {})
        self.assertRaisesRegexp(
            mc_macros.NoRegistryLoaderFound,
            'mc_.* is unavailable',
            mc_macros.load_registries)
        with patch('mc_states.modules.mc_macros.load_kind_registries',
                   side_effect=[
                       {5: 2},
                       {1: 2},
                       {3: 2},
                       {4: 2},
                       {4: 2},
                       {4: 2},
                       {4: 2},
                       {4: 2},
                   ]):
            ret = mc_macros.load_registries()
            self.assertEqual(ret, ['localsettings'])
            self.assertTrue('localsettings' in mc_macros._REGISTRY)

    def test_get_regitry(self):
        def _get(regname, item, default_status=None, *ar, **kw):
            return {
                'poo': True,
                'qoo': False
            }.get(item, default_status)
        with patch.dict(self._salt, {
            'mc_macros.is_item_active': Mock(side_effect=_get)}
        ):
            ret = mc_macros.get_registry({
                'kind': 'foo',
                'bases': 'bar',
                'defaults': {
                    'moo': {'active': True},
                    'noo': {'active': False},
                    'poo': {'active': False},
                    'qoo': {'active': True},
                }
            })
            self.assertEqual(ret['unactivated'],
                             {'noo': {'active': False},
                              'qoo': {'active': True}})
            self.assertEqual(ret['actives'],
                             {'moo': {'active': True},
                              'poo': {'active': False}})
            self.assertTrue(ret['is']['poo'])
            self.assertTrue(ret['is']['moo'])
            self.assertFalse(ret['is']['noo'])
            self.assertFalse(ret['is']['qoo'])

    def test_load_kind_registries(self):
        patched = {}
        for i, reg in enumerate(mc_macros._GLOBAL_KINDS):
            for j, sreg in enumerate(mc_macros._SUB_REGISTRIES):
                patched['mc_{0}.{1}'.format(reg, sreg)] = Mock(
                    return_value={i: (1 + int(i)) * (1 + int(j))})
        results = {}
        patched['mc_macros.load_registries'] = mc_macros.load_registries
        with patch.dict('mc_states.modules.mc_macros._REGISTRY', {}):
            with patch.dict(self._salt, patched):
                for i in sorted(mc_macros._GLOBAL_KINDS):
                    results[i] = mc_macros.load_kind_registries(i)
                ta = mc_macros.kinds()
                ta.sort()
                self.assertEqual(ta,
                                 ['cloud', 'controllers', 'localsettings',
                                  'nodetypes', 'services'])
                self.assertEqual(
                    results['controllers'],
                    {'metadata': {2: 3},
                     'registry': {2: 9},
                     'settings': {2: 6}})
                self.assertEqual(
                    results['localsettings'],
                    {'metadata': {0: 1},
                     'registry': {0: 3},
                     'settings': {0: 2}})
                self.assertEqual(
                    results['nodetypes'],
                    {'metadata': {3: 4},
                     'registry': {3: 12},
                     'settings': {3: 8}})

                self.assertEqual(
                    results['services'],
                    {'metadata': {1: 2},
                     'registry': {1: 6},
                     'settings': {1: 4}})

    def test_is_item_active(self):
        def _get(a, default=None, *ar, **kw):
            return {
                'makina-states.foo.prefix.1': True,
                'makina-states.foo.prefix.2': False,
            }.get(a, default)
        with patch.dict(self._salt, {
            'mc_utils.get': _get,
        }):
            mc_macros.is_item_active('foo', 'prefix.1')
            self.assertTrue(mc_macros.is_item_active('foo', 'prefix.1'))
            self.assertFalse(mc_macros.is_item_active('foo', 'prefix.2'))
        with patch.dict(self._salt, {
            'mc_utils.get': _get,
        }):
            self.assertTrue(
                mc_macros.is_item_active('foo', 'prefix.a',
                                         default_status=True))
            self.assertFalse(
                mc_macros.is_item_active('foo', 'prefix.b',
                                         default_status=False))

if __name__ == '__main__':
    unittest.main()

# vim:set et sts=4 ts=4 tw=80:
