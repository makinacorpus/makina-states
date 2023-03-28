#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import unittest
from .. import base
from mock import patch, Mock


class TestCase(base.ModuleCase):
    def test_defaults(self):
        with patch.dict(self.salt, {
            'mc_utils.get': Mock(
                side_effect={'prefix.1': "e",
                             'prefix.2': "{1}"}.get)
        }):
            self.assertEquals(
                self._('mc_utils.defaults')('prefix', {
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

    def test_defaults_mutable(self):
        # Test that the passed dictionnary is well updated
        # and not copied over
        data = {'1': 'foo',
                '2': {'aa': 2}}
        with patch.dict(self.salt, {
            'mc_utils.get': Mock(side_effect={'prefix.2.aa': 'foo'}.get)
        }):
            self._('mc_utils.defaults')('prefix', data)
            data['1'] = 'bar'
            self.assertEquals(data, {'1': 'bar', '2': {'aa': 'foo'}})

    def test_defaults_rec(self):
        with patch.dict(self.salt, {
            'mc_utils.get': Mock(
                side_effect={
                    'prefix.2.aa': 'foo',
                    'prefix.2.dd': {1: 2},
                    'prefix.2.cc.ff.gg': 'ee',
                    'prefix.2.kk.ll.mmm.nn': 1,
                    'prefix.2.kk.ll.mmu.nn.oou.pp.qqu.rr.ssu': 1,
                    'prefix.2.cc.ff': {'o': 'p'},
                    'prefix.4': 3,
                    'prefix.5': {1: 2},
                }.get)
        }):
            self.assertEquals(
                self._('mc_utils.defaults')('prefix', {
                    '1': 'a',
                    '2': {
                        'aa': 'bb',
                        'kk.ll': {
                            'mmm.nn': {
                                'oo.pp': {
                                    'qq.rr': {'ss': 'tt'},
                                    'qqq.rrr': {'sss': 'ttt'},
                                }
                            },
                            'mmu.nn': {
                                'oou.pp': {
                                    'qqw.rr': {'ssu': 'tt'},
                                    'qqu.rr': {'ssu': 'tt'},
                                }
                            }
                        },
                        'dd': {'dd': 'ee',
                               'ff': {'gg': 'hh'}},
                        'cc': {'dd': 'ee',
                               'ff': {'gg': 'hh',
                                      'o': 'p'}}},
                    '4': {'aaa': 'bbb', 'ccc': {'ddd': 'eee'}},
                    '3': 'b',
                    '5': {'aaaa': 'bbbb', 'cccc': {'dddd': 'eeee'}},
                }
                ), {
                    '1': 'a',
                    '2': {'aa': 'foo',
                          'kk.ll': {
                              'mmm.nn': 1,
                              'mmu.nn': {
                                  'oou.pp': {
                                      'qqw.rr': {'ssu': 'tt'},
                                      'qqu.rr': {'ssu': 1},
                                  }
                              }
                          },
                          'cc': {'dd': 'ee', 'ff': {'gg': 'hh',
                                                    'o': 'p'}},
                          'dd': {1: 2, 'dd': 'ee', 'ff': {'gg': 'hh'}}},
                    '3': 'b',
                    '4': 3,
                    '5': {1: 2, 'aaaa': 'bbbb', 'cccc': {'dddd': 'eeee'}}
                }
            )

    def test_defaults_rec_over(self):
        with patch.dict(self.salt, {
            'mc_utils.get': Mock(
                side_effect={
                    'prefix.11': ['foo'],
                    'prefix.22-overrides': ['foo'],
                    'prefix.2.aa': 'foo',
                    'prefix.2.dd': {1: 2},
                    'prefix.2.cc.ff.gg': 'ee',
                    'prefix.2.cc.ff-overrides': {'o': 'p'},
                    'prefix.2.kk.ll.mmm.nn.oo.pp': {1: 2},
                    'prefix.2.kk.ll.mmu.nn.oou.pp-overrides': {1: 2},
                    'prefix.6.a.bb-overrides': {1: 2},
                    'prefix.6.b.bb': {1: 2},
                    'prefix.4': 3,
                    'prefix.5': {1: 2},
                }.get)
        }):
            self.assertEquals(
                self._('mc_utils.defaults')('prefix', {
                    '11': ['a', 'b', 'c'],
                    '22': ['a', 'b', 'c'],
                    '1': 'a',
                    '6': {
                        'a': {
                            'bb': {'ccc': 'ddd',
                                   'eee': 'fff'}},
                        'b': {
                            'bb': {'ccc': 'ddd',
                                   'eee': 'fff'}}
                    },
                    '2': {
                        'aa': 'bb',
                        'kk.ll': {
                            'mmm.nn': {
                                'oo.pp': {
                                    'qq.rr': {'ss': 'tt'},
                                    'qqq.rrr': {'sss': 'ttt'},
                                }
                            },
                            'mmu.nn': {
                                'oou.pp': {
                                    'qqu.rr': {'ssu': 'tt'},
                                    'qqu.rr': {'ssu': 'tt'},
                                }
                            }
                        },
                        'dd': {'dd': 'ee',
                               'ff': {'gg': 'hh'}},
                        'cc': {'dd': 'ee',
                               'ff': {'o': 'p'}}},
                    '4': {'aaa': 'bbb', 'ccc': {'ddd': 'eee'}},
                    '5': {'aaaa': 'bbbb', 'cccc': {'dddd': 'eeee'}},
                    '3': 'b',
                }
                ), {
                    '11': ['a', 'b', 'c', 'foo'],
                    '22': ['foo'],
                    '1': 'a',
                    '6': {
                        'a': {'bb': {1: 2}},
                        'b': {
                            'bb': {1: 2,
                                   'ccc': 'ddd',
                                   'eee': 'fff'}}
                    },
                    '2': {
                        'aa': 'foo',
                        'kk.ll': {
                            'mmm.nn': {
                                'oo.pp': {
                                    1: 2,
                                    'qq.rr': {'ss': 'tt'},
                                    'qqq.rrr': {'sss': 'ttt'},
                                }
                            },
                            'mmu.nn': {
                                'oou.pp': {
                                    1: 2,
                                }
                            }
                        },
                        'cc': {'dd': 'ee', 'ff': {'o': 'p'}},
                        'dd': {1: 2, 'dd': 'ee', 'ff': {'gg': 'hh'}}},
                    '3': 'b',
                    '4': 3,
                    '5': {1: 2, 'aaaa': 'bbbb', 'cccc': {'dddd': 'eeee'}}
                }
            )

    def test_format_resolve2(self):
        fun = self._('mc_utils.unresolved')
        self.assertFalse(fun(None))
        self.assertFalse(fun(1))
        self.assertFalse(fun(1.1))
        self.assertFalse(fun([1]))
        self.assertFalse(fun({1: 1}))
        self.assertFalse(fun([{1: 1}]))
        self.assertFalse(fun([{'1': 1}]))
        self.assertFalse(fun([{'1': '1'}]))
        self.assertTrue(fun([{'1': '{1}'}]))
        self.assertTrue(fun(['{1}']))
        self.assertTrue(fun([{'{1}': 1}]))
        self.assertTrue(fun([{'1': {'1': {2: '{1}'}}}]))
        self.assertTrue(fun([{'1': {'1': {'{2}': '1'}}}]))
        self.assertTrue(fun([{'1': {'1': {2: ['{1}']}}}]))

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
                    "o": "p",
                    "m": "{l}",
                    "l": "{n}",
                    "n": "{o}",
                    "k": "{n}",
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
                    'i': 'p',
                    'j': 'p',
                    'k': 'p',
                    'l': 'p',
                    'm': 'p',
                    'n': 'p',
                    'o': 'p',
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
                data = self._('mc_utils.format_resolve')(test, args)
                self.assertEquals(data, res)
            else:
                data = self._('mc_utils.format_resolve')(test)
                self.assertEquals(data, res)


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
