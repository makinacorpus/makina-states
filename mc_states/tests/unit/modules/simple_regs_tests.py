# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base
import mc_states.api


class TestCase(base.ModuleCase):
    def test_autoupgrade(self):
        with self.patch(
            grains={'os': 'Ubuntu'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret = self.__('mc_autoupgrade.settings')
            self.assertTrue(
                'Debian' not in ret['unattended']['origins'][0])
        mc_states.api.invalidate_memoize_cache('localreg_autoupgrade_settings')
        with self.patch(
            grains={'os': 'Debian'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret = self.__('mc_autoupgrade.settings')
            self.assertTrue(
                'Debian' in ret['unattended']['origins'][0])


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
