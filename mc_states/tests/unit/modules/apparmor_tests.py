#!/usr/bin/env python
from __future__ import division
from __future__ import absolute_import
from __future__ import division
import unittest
import mc_states.api
from .. import base


class TestCase(base.ModuleCase):

    def test_apparmor(self):
        mc_states.api.invalidate_memoize_cache('localreg_apparmor_settings')
        with self.patch(
            pillar={},
            grains={'os': 'foo'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret1 = self._('mc_apparmor.settings')()
            self.assertFalse(len(ret1['confs']) > 10)
        mc_states.api.invalidate_memoize_cache('localreg_apparmor_settings')
        with self.patch(
            pillar={},
            grains={'os': 'Ubuntu', 'osrelease': '15.04'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret1 = self._('mc_apparmor.settings')()
            self.assertFalse(len(ret1['confs']) > 10)
        mc_states.api.invalidate_memoize_cache('localreg_apparmor_settings')
        with self.patch(
            pillar={},
            grains={'os': 'Ubuntu', 'osrelease': '14.04'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret1 = self._('mc_apparmor.settings')()
            # we disabled for now backport on ubuntu trusty
            self.assertFalse(len(ret1['confs']) > 10)
        mc_states.api.invalidate_memoize_cache('localreg_apparmor_settings')


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
