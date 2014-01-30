#!/usr/bin/env python
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
            'mc_.*.registry is unavailable',
            mc_macros.load_registries,
        )
        with patch.dict(self._salt, {
            'mc_localsettings.registry': {},
            'mc_services.registry': {},
            'mc_controllers.registry': {},
            'mc_localsettings.registry': {},
        }):
            pass
        self.assertEquals(mc_macros._REGISTRY, {})

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
