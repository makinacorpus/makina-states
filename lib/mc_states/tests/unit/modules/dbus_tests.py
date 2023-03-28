# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
import unittest
from .. import base
import mc_states.api
from salt.utils.odict import OrderedDict
import mock

six = mc_states.api.six


class TestCase(base.ModuleCase):

    def test_settings(self):
        data = self._('mc_dbus.settings')()
        self.assertEquals(data['packages'],  ['dbus'])


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
