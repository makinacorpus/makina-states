# -*- coding: utf-8 -*-
import unittest
import copy
import os
import tempfile
from .. import base
import yaml
import mc_states.api
from mc_states.modules import (
    mc_remote,
    mc_dumper,
    mc_ntp,
    mc_utils,
    mc_locations,
    mc_macros
)
from mock import patch, Mock

from mc_states.renderers import lyaml

from salt.utils.odict import OrderedDict


class TestCase(base.ModuleCase):
    _mods = (mc_macros,
             mc_ntp,
             mc_dumper,
             mc_remote,
             mc_locations,
             lyaml,
             mc_utils)

    def test_sls(self):

        def _do(*args, **kw):
            return {'retcode': 0, 'result': {'foo': {'changes': {}}}}

        with patch(
            'mc_states.modules.mc_remote.salt_call', Mock(side_effect=_do)
        ):
            ret1 = mc_remote.sls_('foo', 'a', strip_out=True)
            self.assertEqual(ret1, {'foo': {'changes': {}}})
            ret2 = mc_remote.sls_('foo', 'a', strip_out=False)
            self.assertEqual(
                ret2, {'retcode': 0, 'result': {'foo': {'changes': {}}}})

    def test_highstate(self):

        def _do(*args, **kw):
            return {'retcode': 0, 'result': {'foo': {'changes': {}}}}

        with patch(
            'mc_states.modules.mc_remote.salt_call', Mock(side_effect=_do)
        ):
            ret1 = mc_remote.highstate('foo', strip_out=True)
            self.assertEqual(ret1, {'foo': {'changes': {}}})
            ret2 = mc_remote.highstate('foo', strip_out=False)
            self.assertEqual(
                ret2, {'retcode': 0, 'result': {'foo': {'changes': {}}}})

    def test_get_saltcall_result(self):
        self.assertEqual(
            'foo\n',
            mc_remote.get_saltcall_result(
                "abc\n" +
                mc_remote.SIMPLE_RESULT_SEP +
                "\nfoo"))
        self.assertEqual(
            'foo\n',
            mc_remote.get_saltcall_result(
                "abc\n" +
                mc_remote.SIMPLE_RESULT_SEP +
                "\n+ rm 123\nfoo", sh_wrapper_debug=True))

    def test__unparse_ret(self):
        self._grains['foo'] = 'test'

        def _do(*args, **kw):
            return {'retcode': 0, 'result': {'foo': {'changes': {}}}}

        jvalid_ret = {'outputter': 'json',
                      'transformer': None,
                      'retcode': 0,
                      'stdout':
                      mc_remote.SIMPLE_RESULT_SEP +
                      '\n'
                      '{"2": "3"}\n',
                      'stderr': ''}
        ijvalid_ret = copy.deepcopy(jvalid_ret)
        ijvalid_ret['outputter'] = 'json'
        ijvalid_ret['stdout'] = (
            mc_remote.SIMPLE_RESULT_SEP +
            '\n'
            '{12'
        )
        yvalid_ret = copy.deepcopy(jvalid_ret)
        yvalid_ret['outputter'] = 'yaml'
        yvalid_ret['stdout'] = (
            mc_remote.SIMPLE_RESULT_SEP +
            '\n'
            'a: 1\nb: 2\n'
        )
        iyvalid_ret = copy.deepcopy(jvalid_ret)
        iyvalid_ret['outputter'] = 'yaml'
        iyvalid_ret['stdout'] = (
            mc_remote.SIMPLE_RESULT_SEP +
            '\n'
            'a: 1\nb: {2\n'
        )
        for valid_ret in [jvalid_ret, ijvalid_ret,
                          yvalid_ret, iyvalid_ret]:
            valid_ret['result'] = valid_ret['raw_result'] = (
                mc_remote.get_saltcall_result(valid_ret['stdout']))
        with patch.dict(
            self._opts, {'grains': {}}
        ):
            ret1 = mc_remote._unparse_ret(jvalid_ret)
            self.assertEqual(ret1['result'], {u'2': u'3'})
            self.assertRaises(mc_remote.ResultProcessError,
                              mc_remote._unparse_ret, ijvalid_ret)

        def render(*args, **kwargs):
            return {'lyaml': lyaml.render}

        def outputters(*args, **kwargs):
            return {}

        with patch.dict(self._opts, {'grains': {}}):
            with patch('salt.loader.render', render):
                with patch('salt.loader.outputters', outputters):
                    ret2 = mc_remote._unparse_ret(yvalid_ret)
                    self.assertEqual(ret2['result'],
                                     OrderedDict([('a', 1), ('b', 2)]))
                    self.assertRaises(mc_remote.ResultProcessError,
                                      mc_remote._unparse_ret, iyvalid_ret)

    def test_consolidate_failure(self):
        ret = {'result': {'local': True}}
        self.assertEqual(mc_remote._consolidate_failure(ret),
                         {'result': True, 'retcode': 0})
        ret = {'result': {'local': True}, 'retcode': 1, 'raw_result': 666}
        self.assertEqual(mc_remote._consolidate_failure(ret),
                         {'raw_result': 666,
                          'result': mc_remote._EXECUTION_FAILED,
                          'retcode': 1})

    def test_mark_failed(self):
        self.assertEqual(
            mc_remote._mark_failed({'result': True,
                                    "log_trace": "è",
                                    "log_trace": u"è",
                                    "éa": "aè",
                                    u"éa": "aè"}),
            ({u'\xe9a': 'a\xc3\xa8',
              '\xc3\xa9a': 'a\xc3\xa8',
              'result': None,
              'log_trace': u'\xe8'},
             "Salt call failed:\n{u'\\xe9a': 'a\\xc3\\xa8',"
             " '\\xc3\\xa9a': 'a\\xc3\\xa8',"
             " 'result': None, 'log_trace': u'\\xe8'}"))

    def test_get_localhost(self):
        with patch.dict(self._grains, {'id': 'foo'}):
            self.assertEqual(
                mc_remote.get_localhost(),
                (None, 'foo', '127.0.0.1', 'localhost'))

    def test_process_ret(self):
        with patch.dict(self._grains, {'id': 'foo'}):
            self.assertRaises(mc_remote._SaltCallFailure,
                              mc_remote._process_ret,
                              {'result': 'foo',
                               'raw_result': 'foo',
                               'retcode': 1},
                              hard_failure=True)
            self.assertEqual(
                mc_remote._process_ret(
                    {'result': 'foo',
                     'raw_result': 'foo',
                     'stdout': 'e', 'stderr': 'f',
                     'retcode': 0},
                    unparse=False,
                    strip_out=False,
                    hard_failure=False),
                {'log_trace': '',
                 'result': 'foo',
                 'raw_result': 'foo',
                 'stdout': 'e', 'stderr': 'f',
                 'retcode': 0})
            self.assertEqual(
                mc_remote._process_ret(
                    {'log_trace': 'foo'},
                    unparse=False,
                    strip_out=False,
                    hard_failure=False),
                {'result': None,
                 'log_trace': 'foo',
                 'retcode': 0})
            self.assertEqual(
                mc_remote._process_ret(
                    {'result': mc_remote._EXECUTION_FAILED, 'retcode': 0},
                    unparse=False,
                    strip_out=False,
                    hard_failure=False),
                {'log_trace': '',
                 'result': None,
                 'raw_result': mc_remote._EXECUTION_FAILED,
                 'retcode': 1})
            self.assertEqual(
                mc_remote._process_ret(
                    {'result': 'foo',
                     'raw_result': 'foo',
                     'retcode': 1},
                    unparse=False,
                    strip_out=False,
                    hard_failure=False),
                {'log_trace': '',
                 'result': None,
                 'raw_result': 'foo',
                 'retcode': 1})
            self.assertEqual(
                mc_remote._process_ret(
                    {'result': 'foo',
                     'raw_result': 'foo',
                     'stdout': 'e', 'stderr': 'f',
                     'retcode': 0},
                    unparse=False,
                    strip_out=True,
                    hard_failure=False),
                {'log_trace': '',
                 'result': 'foo',
                 'raw_result': 'foo',
                 'stdout': '', 'stderr': '',
                 'retcode': 0})

    def test_consolidate_transformer_and_outputter(self):
        self.assertEqual(
            mc_remote._consolidate_transformer_and_outputter(
                {}), {'outputter': 'noop', 'transformer': 'noop'})
        self.assertEqual(
            mc_remote._consolidate_transformer_and_outputter(
                {'outputter': 'json'}),
            {'outputter': 'json', 'transformer': 'json'})
        self.assertEqual(
            mc_remote._consolidate_transformer_and_outputter(
                {'outputter': 'json', 'transformer': 'yaml'}),
            {'outputter': 'json', 'transformer': 'lyaml'})


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
