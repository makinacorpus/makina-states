#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base
import mock
from mc_states.api import six


class TestCase(base.ModuleCase):

    def test_appendnet(self):
        func = self._('mc_network.append_netmask')
        with self.patch(
            funcs={
                'modules': {
                }
            },
            grains={
                'ip4_interfaces': {'eth0': ['192.168.168.8']}
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):

            self.assertEqual(func('10.5.1.0'), '10.5.1.0/24')
            self.assertEqual(func('10.5.0.0'), '10.5.0.0/16')
            self.assertEqual(func('192.168.0.0'), '192.168.0.0/16')
            self.assertEqual(func('172.16.0.0'), '172.16.0.0/12')
            self.assertEqual(func('8.8.8.0'), '8.8.8.0/24')
            self.assertEqual(func('10.5.1.1'), '10.5.1.1/32')
            self.assertEqual(func('10.5.0.1'), '10.5.0.1/32')
            self.assertEqual(func('192.168.1.0'), '192.168.1.0/24')
            self.assertEqual(func('192.168.1.2'), '192.168.1.2/32')
            self.assertEqual(func('192.168.0.1'), '192.168.0.1/32')
            self.assertEqual(func('172.16.0.1'), '172.16.0.1/32')
            self.assertEqual(func('8.8.8.8'), '8.8.8.8/32')
            self.assertEqual(func('8.8.0.0'), '8.8.0.0/16')
            self.assertEqual(func('8.0.0.0'), '8.0.0.0/8')
            self.assertEqual(func('0.0.0.0'), '0.0.0.0/0')
# vim:set et sts=4 ts=4 tw=80:
