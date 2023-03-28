#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base
import mock
from mc_states.api import six


class TestCase(base.ModuleCase):

    def test_haproxy(self):
        func = self._('mc_haproxy.settings')
        with self.patch(
            funcs={
                'modules': {
                }
            },
            grains={
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret = func()
            self.assertTrue('rotate' in ret)
            self.assertTrue('configs' in ret)


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
