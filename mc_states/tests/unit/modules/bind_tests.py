#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
__docformat__ = 'restructuredtext en'
import unittest
from .. import base
from mc_states.modules import (
    mc_dumper,
    mc_utils,
    mc_locations,
    mc_bind,
    mc_macros
)
from mock import patch, Mock
import mc_states.api


class TestCase(base.ModuleCase):
    _mods = (mc_macros,
             mc_dumper,
             mc_bind,
             mc_locations,
             mc_utils)

    def test_settings(self):
        locs = mc_locations.settings()
        with patch.dict(self._grains, {'os': 'Ubuntu',
                                       'os_family': 'Debian'}):
            data = mc_bind.settings()
            self.assertTrue(isinstance(data, dict))
            self.assertEqual(
                data['views_config'],
                locs['conf_dir'] + '/bind/named.conf.views')


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
