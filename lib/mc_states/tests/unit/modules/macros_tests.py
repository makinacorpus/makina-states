# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
import unittest
from .. import base
import contextlib
from mock import patch, Mock

from mc_states import saltapi
import mc_states.api


class TestCase(base.ModuleCase):

    def test_get_regitry_paths(self):
        with self.patch(
            opts={'config_dir': 'salt'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            mc_states.api.invalidate_memoize_cache(
                'localreg_locations_settings')
            locs = self._('mc_locations.settings')()
            ret = self._('mc_macros.get_registry_paths')('myreg')
            self.assertEqual(
                ret['context'],
                'salt/makina-states/myreg.pack'.format(**locs)
            )
            self.assertEqual(
                ret['global'],
                '{root_dir}etc/makina-states/myreg.pack'.format(**locs)
            )
            self.assertEqual(
                ret['salt'],
                '{root_dir}etc/salt/'
                'makina-states/myreg.pack'.format(**locs))

    def test_load_registries(self):
        self.assertEquals(self._('mc_macros.dump')(), {})
        with self.patch(
            globs={'_GLOBAL_KINDS': ['foo']},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            self.assertRaisesRegexp(
                saltapi.NoRegistryLoaderFound,
                'mc_.* is unavailable',
                self._('mc_macros.load_registries'))
            with contextlib.nested(
                self.patch(
                    globs={'_GLOBAL_KINDS': ['foo']},
                    filtered=['mc.*'],
                    kinds=['modules']),
                patch.dict(self.salt, {
                    'mc_foo.settings': Mock(side_effect=lambda: {66: 666}),
                    'mc_foo.metadata': Mock(side_effect=lambda: {66: 666}),
                    'mc_foo.registry': Mock(side_effect=lambda: {66: 666}),
                })
            ):
                ret = self._('mc_macros.load_registries')()
                self.assertEqual(ret, ['foo'])

    def test_get_regitry(self):
        def _get(regname, item, default_status=None, *ar, **kw):
            return {'poo': True,
                    'qoo': False}.get(item, default_status)

        with patch.dict(self.salt, {
            'mc_macros.is_item_active': Mock(side_effect=_get)
        }):
            ret = self._('mc_macros.get_registry')({
                'kind': 'foo',
                'bases': 'bar',
                'defaults': {
                    'moo': {'active': True},
                    'noo': {'active': False},
                    'poo': {'active': False},
                    'qoo': {'active': True},
                }})
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
        gkinds = self.__('mc_macros.glob_dump')
        for i, reg in enumerate(gkinds):
            for j, sreg in enumerate(self.__('mc_macros.sub_dump')):
                patched['mc_{0}.{1}'.format(reg, sreg)] = Mock(
                    return_value={i: (1 + int(i)) * (1 + int(j))})
        with patch.dict(self.salt, patched):
            results = {}
            for i in sorted(gkinds):
                results[i] = self._('mc_macros.load_kind_registries')(i)
            ta = self._('mc_macros.kinds')()
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
        with patch.dict(self.salt, {'mc_utils.get': _get}):
            self._('mc_macros.is_item_active')('foo', 'prefix.1')
            self.assertTrue(
                self._('mc_macros.is_item_active')('foo', 'prefix.1'))
            self.assertFalse(
                self._('mc_macros.is_item_active')('foo', 'prefix.2'))
        with patch.dict(self.salt, {'mc_utils.get': _get}):
            self.assertTrue(
                self._('mc_macros.is_item_active')('foo', 'prefix.a',
                                                   default_status=True))
            self.assertFalse(
                self._('mc_macros.is_item_active')('foo', 'prefix.b',
                                                   default_status=False))

if __name__ == '__main__':
    unittest.main()

# vim:set et sts=4 ts=4 tw=80:
