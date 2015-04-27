#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base


class TestCase(base.ModuleCase):

    def test_tsig(self):
        ret1 = self._('mc_bind.tsig_for')('foo')
        self.assertTrue(len(ret1) > 64)
        ret2 = self._('mc_bind.tsig_for')('foo')
        ret3 = self._('mc_bind.tsig_for')('foo3')
        ret4 = self._('mc_bind.tsig_for')('foo3')
        self.assertTrue(ret3 == ret4)
        self.assertTrue(ret1 == ret2)
        self.assertTrue(ret1 != ret3)

    def test_gtsig(self):
        ret1 = self._('mc_bind.generate_tsig')(128)
        self.assertTrue(len(ret1.decode('base64')) == 128)

    def test_settings(self):
        locs = self._('mc_locations.settings')()
        with self.patch(
            grains={'os': 'Ubuntu', 'os_family': 'Debian'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            data = self._('mc_bind.settings')()
            self.assertTrue(isinstance(data, dict))
            self.assertEqual(
                data['views_config'],
                locs['conf_dir'] + '/bind/named.conf.views')


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
