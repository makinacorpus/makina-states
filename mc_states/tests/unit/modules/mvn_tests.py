#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base
import mc_states.api

six = mc_states.api.six


class TestCase(base.ModuleCase):

    def test_settings(self):
        func = self._('mc_mvn.settings')
        with self.patch(
            grains={'os': 'Ubuntu', 'os_family': 'Debian'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            mc_states.api.invalidate_memoize_cache('localreg_mvn_registry')
            data = func()
            self.assertTrue(isinstance(data['url'], six.string_types))


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
