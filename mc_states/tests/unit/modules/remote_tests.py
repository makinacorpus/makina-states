# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
import unittest
import copy
from .. import base
from mock import patch, Mock


from mc_states import saltapi
from salt.utils.odict import OrderedDict


class TestCase(base.ModuleCase):
    def test_sls(self):

        def _do(*args, **kw):
            return {'retcode': 0, 'result': {'foo': {'changes': {}}}}

        with self.patch(funcs={
            'modules': {'mc_remote.salt_call': Mock(side_effect=_do)}},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret1 = self._('mc_remote.sls')('foo', 'a', strip_out=True)
            self.assertEqual(ret1, {'foo': {'changes': {}}})
            ret2 = self._('mc_remote.sls')('foo', 'a', strip_out=False)
            self.assertEqual(
                ret2, {'retcode': 0, 'result': {'foo': {'changes': {}}}})

    def test_highstate(self):
        def _do(*args, **kw):
            return {'retcode': 0, 'result': {'foo': {'changes': {}}}}

        with self.patch(funcs={
            'modules': {'mc_remote.salt_call': Mock(side_effect=_do)}},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret1 = self._('mc_remote.highstate')('foo', strip_out=True)
            self.assertEqual(ret1, {'foo': {'changes': {}}})
            ret2 = self._('mc_remote.highstate')('foo', strip_out=False)
            self.assertEqual(
                ret2, {'retcode': 0, 'result': {'foo': {'changes': {}}}})

    def test_get_saltcall_result(self):
        SIMPLE_RESULT_SEP = self.get_private('mc_remote.SIMPLE_RESULT_SEP')
        self.assertEqual(
            'foo\n',
            self._('mc_remote.get_saltcall_result')(
                "abc\n" +
                SIMPLE_RESULT_SEP +
                "\nfoo"))
        self.assertEqual(
            'foo\n',
            self._('mc_remote.get_saltcall_result')(
                "abc\n" +
                SIMPLE_RESULT_SEP +
                "\n+ rm 123\nfoo", sh_wrapper_debug=True))

    def test__unparse_ret(self):
        self.grains_['foo'] = 'test'
        SIMPLE_RESULT_SEP = self.get_private('mc_remote.SIMPLE_RESULT_SEP')
        fun_ = self.get_private('mc_remote._unparse_ret')

        def _do(*args, **kw):
            return {'retcode': 0, 'result': {'foo': {'changes': {}}}}

        jvalid_ret = {'outputter': 'json',
                      'transformer': None,
                      'retcode': 0,
                      'stdout':
                      SIMPLE_RESULT_SEP +
                      '\n'
                      '{"2": "3"}\n',
                      'stderr': ''}
        ijvalid_ret = copy.deepcopy(jvalid_ret)
        ijvalid_ret['outputter'] = 'json'
        ijvalid_ret['stdout'] = (
            SIMPLE_RESULT_SEP +
            '\n'
            '{12'
        )
        yvalid_ret = copy.deepcopy(jvalid_ret)
        yvalid_ret['outputter'] = 'yaml'
        yvalid_ret['stdout'] = (
            SIMPLE_RESULT_SEP +
            '\n'
            'a: 1\nb: 2\n'
        )
        iyvalid_ret = copy.deepcopy(jvalid_ret)
        iyvalid_ret['outputter'] = 'yaml'
        iyvalid_ret['stdout'] = (
            SIMPLE_RESULT_SEP +
            '\n'
            'a: 1\nb: {2\n'
        )
        for valid_ret in [jvalid_ret, ijvalid_ret,
                          yvalid_ret, iyvalid_ret]:
            valid_ret['result'] = valid_ret['raw_result'] = (
                self._('mc_remote.get_saltcall_result')(valid_ret['stdout']))
        with self.patch(
            grains={},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret1 = fun_(jvalid_ret)
            self.assertEqual(ret1['result'], {u'2': u'3'})
            self.assertRaises(saltapi.RemoteResultProcessError,
                              fun_, ijvalid_ret)

        with self.patch(
            grains={},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret2 = fun_(yvalid_ret)
            self.assertEqual(ret2['result'],
                             OrderedDict([('a', 1), ('b', 2)]))
            self.assertRaises(
                saltapi.RemoteResultProcessError,
                fun_, iyvalid_ret)

    def test_consolidate_failure(self):
        _EXECUTION_FAILED = self.get_private('mc_remote._EXECUTION_FAILED')
        fun_ = self.get_private('mc_remote._consolidate_failure')
        ret = {'result': {'local': True}}
        self.assertEqual(fun_(ret), {'result': True, 'retcode': 0})
        ret = {'result': {'local': True}, 'retcode': 1, 'raw_result': 666}

        self.assertEqual(fun_(ret), {'raw_result': 666,
                                     'result': _EXECUTION_FAILED,
                                     'retcode': 1})

    def test_mark_failed(self):
        mf = self.get_private('mc_remote._mark_failed')
        self.assertEqual(
            mf({'result': True,
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
        with patch.dict(self.grains_, {'id': 'foo'}):
            self.assertEqual(
                self._('mc_remote.get_localhost')(),
                (None, 'foo', '127.0.0.1', 'localhost'))

    def test_process_ret(self):
        process_ret = self.get_private('mc_remote._process_ret')
        _process_ret = self.get_private('mc_remote._process_ret',
                                        'mc_remote.highstate')
        self.assertTrue(process_ret is _process_ret)
        _EXECUTION_FAILED = self.get_private('mc_remote._EXECUTION_FAILED')
        with patch.dict(self.grains_, {'id': 'foo'}):
            self.assertRaises(saltapi._SaltCallFailure,
                              process_ret,
                              {'result': 'foo',
                               'raw_result': 'foo',
                               'retcode': 1},
                              hard_failure=True)
            self.assertEqual(
                process_ret(
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
                process_ret(
                    {'log_trace': 'foo'},
                    unparse=False,
                    strip_out=False,
                    hard_failure=False),
                {'result': None,
                 'log_trace': 'foo',
                 'retcode': 0})
            self.assertEqual(
                process_ret(
                    {'result': _EXECUTION_FAILED, 'retcode': 0},
                    unparse=False,
                    strip_out=False,
                    hard_failure=False),
                {'log_trace': '',
                 'result': None,
                 'raw_result': _EXECUTION_FAILED,
                 'retcode': 1})
            self.assertEqual(
                process_ret(
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
                process_ret(
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
        fun_ = self.get_private(
            'mc_remote._consolidate_transformer_and_outputter')
        self.assertEqual(
            fun_({}), {'outputter': 'noop', 'transformer': 'noop'})
        self.assertEqual(
            fun_({'outputter': 'json'}),
            {'outputter': 'json', 'transformer': 'json'})
        self.assertEqual(
            fun_({'outputter': 'json', 'transformer': 'yaml'}),
            {'outputter': 'json', 'transformer': 'lyaml'})


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
