# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
from .. import base
import mc_states.api
from mc_states.modules import (
    mc_dumper,
    mc_ntp,
    mc_utils,
    mc_locations,
    mc_macros
)
from mock import patch, Mock


class TestCase(base.ModuleCase):
    _mods = (mc_macros,
             mc_ntp,
             mc_dumper,
             mc_locations,
             mc_utils)

    def test_ntp(self):
        data = mc_ntp.settings()
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(
            data['default_flags'],
            ' kod notrap nomodify nopeer noquery')
        with patch.dict(self._grains, {
            'makina.lxc': False,
            'makina.docker': False
        }):
            mc_states.api.invalidate_memoize_cache('localreg_ntp_settings')
            data = mc_ntp.settings()
            self.assertTrue(data['activated'])
            self.assertTrue(data['defaults']['NTPSYNC'] != '"no"')
        with patch.dict(self._grains, {
            'makina.lxc': True,
            'makina.docker': False
        }):
            mc_states.api.invalidate_memoize_cache('localreg_ntp_settings')
            data = mc_ntp.settings()
            self.assertFalse(data['activated'])
            self.assertTrue(data['defaults']['NTPSYNC'] == '"no"')
        with patch.dict(self._grains, {
            'makina.lxc': False,
            'makina.docker': True
        }):
            mc_states.api.invalidate_memoize_cache('localreg_ntp_settings')
            data = mc_ntp.settings()
            self.assertFalse(data['activated'])
            self.assertTrue(data['defaults']['NTPSYNC'] == '"no"')

if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
