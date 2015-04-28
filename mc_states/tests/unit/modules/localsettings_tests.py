#a!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import absolute_import
from __future__ import division
import unittest
import mc_states.api
from .. import base
import copy


class TestCase(base.ModuleCase):

    def test_localreg(self):
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_registry')
        mc_states.api.invalidate_memoize_cache('mc_localsettings.registry')
        with self.patch(
            pillar={'makina-states.nodetypes.laptop': True},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret1 = copy.deepcopy(self._('mc_localsettings.registry')())
            self.assertTrue(ret1['is']['jdk'])
            self.assertTrue(ret1['is']['npm'])
            self.assertTrue(ret1['is']['nodejs'])
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_registry')
        mc_states.api.invalidate_memoize_cache('mc_localsettings.registry')
        with self.patch(
            pillar={'makina-states.nodetypes.laptop': False},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret2 = copy.deepcopy(self._('mc_localsettings.registry')())
            self.assertFalse(ret2['is']['jdk'])
            self.assertFalse(ret2['is']['npm'])
            self.assertFalse(ret2['is']['nodejs'])

    def test_apparmor(self):
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_registry')
        mc_states.api.invalidate_memoize_cache('mc_localsettings.registry')
        with self.patch(
            grains={'os': 'foo'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            self.assertFalse(self._('mc_localsettings.apparmor_en')())
        mc_states.api.invalidate_memoize_cache('localreg_nodetypes_registry')
        mc_states.api.invalidate_memoize_cache('mc_localsettings.registry')
        with self.patch(
            grains={'os': 'Ubuntu'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            self.assertTrue(self._('mc_localsettings.apparmor_en')())


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
