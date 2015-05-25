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
        func = self._('mc_cloud_images.guess_template_env')
        with self.patch(
            grains={'os': 'Ubuntu', 'os_family': 'Debian'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            self.assertEqual(func('precise'), {'os': 'ubuntu',
                                               'release': 'precise'})
            self.assertEqual(func('foo', 'precise'), {'os': 'ubuntu',
                                                      'release': 'precise'})


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
