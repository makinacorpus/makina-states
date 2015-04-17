# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base
from mc_states.modules import (
    mc_dumper,
    mc_utils,
    mc_locations,
    mc_autoupgrade,
    mc_macros
)
from mock import patch, Mock
import mc_states.api


class TestCase(base.ModuleCase):
    _mods = (mc_macros,
             mc_dumper,
             mc_autoupgrade,
             mc_locations,
             mc_utils)

    def test_autoupgrade(self):
        with patch.dict(self._grains, {'os': 'Ubuntu'}):
            ret = mc_autoupgrade.settings()
            self.assertTrue(
                'Debian' not in ret['unattended']['origins'][0])
        mc_states.api.invalidate_memoize_cache('localreg_autoupgrade_settings')
        with patch.dict(self._grains, {'os': 'Debian'}):
            ret = mc_autoupgrade.settings()
            self.assertTrue(
                'Debian' in ret['unattended']['origins'][0])


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
