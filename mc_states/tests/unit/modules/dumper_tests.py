# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
import unittest
import os
import tempfile
from .. import base
from mc_states.modules import (
    mc_dumper,
    mc_utils,
    mc_locations,
    mc_macros
)
from mock import patch, Mock


class TestCase(base.ModuleCase):
    _mods = (mc_macros,
             mc_dumper,
             mc_locations,
             mc_utils)

    def test_msgpack(self):
        value = 'test'
        ret = mc_dumper.msgpack_dump(value)
        ret2 = mc_dumper.msgpack_load(ret)
        self.assertEqual(value, ret2)

    def test_json(self):
        value = 'test'
        ret = mc_dumper.json_dump(value)
        ret2 = mc_dumper.json_load(ret)
        self.assertEqual(value, ret2)
        self.assertEqual(ret, '"test"')
        self.assertEqual(ret2, value)

    def test_yaml(self):
        self.assertEqual(
            mc_dumper.yaml_dump({2: 1}),
            '2: 1\n')
        self.assertEqual(
            mc_dumper.yaml_dump({2: "1\nh"}),
            "2: '1\n\n  h'\n")
        self.assertEqual(
            mc_dumper.yaml_dump({2: "1\nh"}, flow=True),
            "{2: '1\n\n    h'}\n")
        self.assertEqual(
            mc_dumper.yaml_dump({2: "1\nh"}, nonewline=True),
            "2: '1    h' ")
        self.assertEqual(
            mc_dumper.old_yaml_dump({2: "1\nh"}, flow=True),
            "{2: '1      h'} ")
        self.assertEqual(
            mc_dumper.iyaml_dump({2: "1\nh"}),
            "{2: '1\n\n    h'}\n")
        self.assertEqual(
            mc_dumper.cyaml_load("{2: '1\n\n    h'}\n"),
            {2: "1\nh"})
        self.assertEqual(
            mc_dumper.yaml_load("{2: '1\n\n    h'}\n"),
            {2: "1\nh"})

    def test_sanitize_kw(self):
        self.assertEqual(
            mc_dumper.sanitize_kw({'is_file': 1, 1: 1}), {1: 1})
        self.assertEqual(
            mc_dumper.sanitize_kw({'__pub__foo': 1, 1: 1}), {1: 1})
        self.assertEqual(
            mc_dumper.sanitize_kw({'e__pub__foo': 1, 1: 1}),
            {'e__pub__foo': 1, 1: 1})

    def test_first_arg_is_file(self):
        self.assertTrue(
            mc_dumper.first_arg_is_file(**{'is_file': True}))
        self.assertTrue(
            not mc_dumper.first_arg_is_file(**{'is_file': False}))
        t = tempfile.mkstemp()[1]
        self.assertFalse(
            mc_dumper.first_arg_is_file(t, **{'is_file': False}))
        self.assertTrue(mc_dumper.first_arg_is_file(t))
        os.remove(t)
        self.assertFalse(mc_dumper.first_arg_is_file(t))

if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
