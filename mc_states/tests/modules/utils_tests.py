#!/usr/bin/env python
from __future__ import (absolute_import,
                        division,
                        print_function,)
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import unittest

from . import base
from mc_states.modules import mc_utils
from mock import patch, Mock


class TestCase(base.ModuleCase):
    _mods = (mc_utils,)

    def test_defaults(self):
        with patch.dict(mc_utils.__salt__,
                        {'mc_utils.get': Mock(
                            side_effect={
                                'prefix.1': "e",
                                'prefix.2': "{1}",
                            }.get)}):
            self.assertEquals(
                mc_utils.defaults('prefix', {
                    "1": 'a',
                    "2": '{3}',
                    "3": 'b',
                }
                ), {
                    '1': 'e',  # 1 take the pillar value
                    '2': 'e',  # 2 is overriden by the pillar value and get
                               # resolved {1} > data['1'] > e
                    '3': 'b'   # there is not 'prefix3' in pillar, default to b
                }
            )

    def test_defaults_rec(self):
        with patch.dict(mc_utils.__salt__,
                        {'mc_utils.get': Mock(
                            side_effect={
                                'prefix.2.aa': "foo",
                                'prefix.2.dd': {1: 2},
                                'prefix.2.cc.ff.gg': "ee",
                                'prefix.4': 3,
                                'prefix.5': {1: 2},
                            }.get)}):
            self.assertEquals(
                mc_utils.defaults('prefix', {
                    "1": 'a',
                    "2": {"aa": "bb",
                          "dd": {"dd": "ee",
                                 "ff": {"gg": "hh"}},
                          "cc": {"dd": "ee",
                                 "ff": {"gg": "hh"}}},
                    "4": {"aaa": "bbb", "ccc": {"ddd": "eee"}},
                    "5": {"aaaa": "bbbb", "cccc": {"dddd": "eeee"}},
                    "3": 'b',
                }
                ), {
                    '1': 'a',
                    '2': {'aa': 'foo', 'cc': {'dd': 'ee', 'ff': {'gg': 'ee'}},
                          'dd': {1: 2}},
                    '3': 'b',
                    '4': 3,
                    '5': {1: 2},
                }
            )

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


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
