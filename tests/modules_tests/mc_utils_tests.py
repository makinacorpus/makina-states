#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import unittest

from modules_tests import base

from modules import mc_utils


class DefaulstTestCase(base.ModuleCase):

    def test_defaults(self):
        self.assertTrue(True)


class TestCase(base.ModuleCase):
    def test_format_resolve(self):
        self.maxDiff = None
        tests = [
            [
                # You may notice here that we have introduced the test
                # of a cycle between i j and k
                {
                    "a": ["{b}/{d}/{f}", "{c}", "{eee}"],
                    "aa": ["{b}/{d}/{f}", "{c}/{b}", "{eee}"],
                    "b": 1,
                    "c": ["{d}", "b"],
                    "d": "{b}",
                    "eee": "{f}",
                    "f": "{g}",
                    "g": "3",
                    "i": "{j}",
                    "j": "{k}",
                    "k": "{i}",
                }, None,
                {
                    'a': ['1/1/3', ['1', 'b'], '3'],
                    'aa': ['1/1/3', "['1', 'b']/1", '3'],
                    'b': 1,
                    'c': ['1', 'b'],
                    'd': '1',
                    'eee': '3',
                    'f': '3',
                    'g': '3',
                    'i': '{k}',
                    'j': '{i}',
                    'k': '{k}'
                },
            ],
            [
                '{prefix}/{name}/openstack',
                {
                    'prefix': 'foo',
                    'name': 'bar',
                    'openstack': 'fuu',
                },
                'foo/bar/openstack',
            ],
        ]
        for test, args, res in tests:
            if args:
                self.assertEquals(mc_utils.format_resolve(test, args), res)
            else:
                self.assertEquals(mc_utils.format_resolve(test), res)


if (
    __name__ == '__main__'
):
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
