# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
import unittest
from .. import base
import mc_states.api


class TestCase(base.ModuleCase):

    def test_ntp(self):
        data = self.__('mc_ntp.settings')
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(
            data['default_flags'],
            ' kod notrap nomodify nopeer noquery')
        with self.patch(
            grains={'makina.lxc': False, 'makina.docker': False},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            mc_states.api.invalidate_memoize_cache('localreg_ntp_settings')
            data = self.__('mc_ntp.settings')
            self.assertTrue(data['activated'])
            self.assertTrue(data['defaults']['NTPSYNC'] != '"no"')
        with self.patch(
            grains={'makina.lxc': True, 'makina.docker': False},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            mc_states.api.invalidate_memoize_cache('localreg_ntp_settings')
            data = self.__('mc_ntp.settings')
            self.assertFalse(data['activated'])
            self.assertTrue(data['defaults']['NTPSYNC'] == '"no"')
        with self.patch(
            grains={'makina.lxc': True, 'makina.docker': True},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            mc_states.api.invalidate_memoize_cache('localreg_ntp_settings')
            data = self.__('mc_ntp.settings')
            self.assertFalse(data['activated'])
            self.assertTrue(data['defaults']['NTPSYNC'] == '"no"')

if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
