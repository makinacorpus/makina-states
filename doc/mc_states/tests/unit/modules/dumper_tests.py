# -*- coding: utf-8 -*-
import unittest
from .. import base
from mc_states.modules import (
    mc_dumper,
    mc_utils,
    mc_macros
)
from mock import patch, Mock


class TestCase(base.ModuleCase):
    _mods = (mc_macros,
             mc_dumper,
             mc_utils)

    #def test_load_registries(self):
    #    self.assertEquals(mc_macros._REGISTRY, {})
    #    self.assertRaisesRegexp(
    #        mc_macros.NoRegistryLoaderFound,
    #        'mc_.* is unavailable',
    #        mc_macros.load_registries)
    #    with patch('mc_states.modules.mc_macros.load_kind_registries',
    #               side_effect=[
    #                   {5: 2},
    #                   {1: 2},
    #                   {3: 2},
    #                   {4: 2},
    #                   {4: 2},
    #                   {4: 2},
    #                   {4: 2},
    #                   {4: 2},
    #               ]):

    #    with patch.dict(self._salt, {
    #        'mc_utils.get': _get,
    #    }):
    #        ret = mc_macros.load_registries()
    #        self.assertEqual(ret, ['localsettings'])
    #        self.assertTrue('localsettings' in mc_macros._REGISTRY)

    def test_get_regitry(self):
        def _get(regname, item, default_status=None, *ar, **kw):
            return {
                'poo': True,
                'qoo': False
            }.get(item, default_status)
        with patch.dict(self._salt, {
            'mc_macros.is_item_active': Mock(side_effect=_get)}
        ):


if __name__ == '__main__':
    unittest.main()

# vim:set et sts=4 ts=4 tw=80:
