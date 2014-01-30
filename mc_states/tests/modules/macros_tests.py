# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import unittest

from . import base
from mc_states.modules import (
    mc_utils,
    mc_macros
)
from mock import patch, Mock


class TestCase(base.ModuleCase):
    _mods = (mc_macros, mc_utils)

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
                   ]):
            ret = mc_macros.load_registries()
            self.assertEqual(ret, ['localsettings'])
            self.assertTrue('localsettings' in mc_macros._REGISTRY)

    def test_get_regitry(self):
        with patch.dict(self._salt, {
            'mc_utils.get': Mock(
                side_effect={
                    'makina-states.foo.poo': True,
                    'makina-states.foo.qoo': False
                }.get
            )}
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
                self.assertEqual(mc_macros.kinds(),
                                 ['controllers', 'localsettings',
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
        with patch.dict(self._salt,
                        {'mc_utils.get': Mock(
                            side_effect={
                                'prefix.1': True,
                                'prefix.2': False,
                            }.get)}):
            self.assertTrue(mc_macros.is_item_active('prefix.1'))
            self.assertFalse(mc_macros.is_item_active('prefix.2'))
            self.assertTrue(
                mc_macros.is_item_active('prefix.a', default_status=True))
            self.assertFalse(
                mc_macros.is_item_active('prefix.b', default_status=False))

    def test_registry_kind_get(self):
        foo = mc_macros.registry_kind_get('foo')
        self.assertEqual(foo, {})
        self.assertTrue(foo is mc_macros._REGISTRY['foo'])


if __name__ == '__main__':
    unittest.main()

# vim:set et sts=4 ts=4 tw=80:
