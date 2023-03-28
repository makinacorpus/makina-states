#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import absolute_import
from __future__ import division
import unittest
import mc_states.api
from .. import base

import mock
import os
import copy
import sys
import contextlib


class TestCase(base.ModuleCase):

    def test_is_nt(self):
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_registry')
        fun = self.salt['mc_nodetypes.is_nt']
        self.assertTrue(fun('server'))
        wopen = mock.mock_open(read_data='foo')
        gopen = mock.mock_open(read_data='laptop')

        def ex(fic):
            if fic.endswith('etc/salt/makina-states'):
                return True
            return False

        with mock.patch('os.path.exists', side_effect=ex):
            with mock.patch.dict(os.environ, {'TRAVIS': 'false'}):
                self.assertFalse(fun('travis'))
            with mock.patch.dict(os.environ, {'TRAVIS': 'true'}):
                self.assertTrue(fun('server'))
        with mock.patch.dict(os.environ, {'TRAVIS': 'false'}):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch('__builtin__.open', wopen):
                    self.assertFalse(fun('laptop'))
                with mock.patch('__builtin__.open', gopen):
                    self.assertTrue(fun('laptop'))

    def test_is_vm(self):
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_registry')
        fun = self.salt['mc_nodetypes.is_vm']
        mod = sys.modules[fun.__module__]
        with mock.patch.object(mod, 'is_container', return_value=True):
            self.assertTrue(fun())
        with mock.patch.object(mod, 'is_container', return_value=False):
            with mock.patch.object(mod, 'registry', return_value={
                'is': {}}
            ):
                self.assertFalse(fun())
            with mock.patch.object(mod, 'registry', return_value={
                'is': {'kvm': True}}
            ):
                self.assertTrue(fun())
            with mock.patch.object(mod, 'registry', return_value={
                'is': {'travis': True}}
            ):
                self.assertTrue(fun())

    def test_settings(self):
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_settings')
        ret = self._('mc_nodetypes.settings')()
        self.assertEqual(ret, {
            'metadata': {'bases': ['localsettings', 'services'],
                         'kind': 'nodetypes'}})

    def test_reg(self):
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_registry')
        ret = self._('mc_nodetypes.registry')()
        self.assertTrue('has' in ret)
        self.assertTrue('is' in ret)
        self.assertTrue(ret['actives']['server'])

    def test_metadata(self):
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_metadata')
        ret = self._('mc_nodetypes.metadata')()
        self.assertEqual(ret, {'bases': ['localsettings', 'services'],
                               'kind': 'nodetypes'})

    def test_forward(self):
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_registry')
        mc_states.api.invalidate_memoize_cache('mc_localsettings.registry')
        with mock.patch(
            'mc_states.grains.makina_grains.get_makina_grains', return_value={}
        ):
            ret = self._('mc_nodetypes.get_makina_grains')()
            self.assertEqual(ret, {})
        with mock.patch(
            'mc_states.grains.makina_grains._is_devhost', return_value=1
        ):
            ret = self._('mc_nodetypes.is_devhost')()
            self.assertEqual(ret, 1)
        with mock.patch(
            'mc_states.grains.makina_grains._is_container', return_value=1
        ):
            ret = self._('mc_nodetypes.is_container')()
            self.assertEqual(ret, 1)
        with mock.patch(
            'mc_states.grains.makina_grains._is_upstart', return_value=1
        ):
            ret = self._('mc_nodetypes.is_upstart')()
            self.assertEqual(ret, 1)
        with mock.patch(
            'mc_states.grains.makina_grains._is_systemd', return_value=1
        ):
            ret = self._('mc_nodetypes.is_systemd')()
            self.assertEqual(ret, 1)


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
