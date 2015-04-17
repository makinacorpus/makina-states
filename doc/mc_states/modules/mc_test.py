#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import os
import traceback
import salt.exceptions
import salt.output
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states import saltapi
from mc_states.tests import utils


class TestError(salt.exceptions.SaltException):
    """."""


def _error(msg, ret=None):
    return saltapi.rich_error(TestError, msg, ret)


def froot():
    return __opts__['file_roots']['base'][0]


def mroot():
    return os.path.join(froot(), 'makina-states')


def lint_tests(use_vt=True):
    try:
        result = __salt__['cmd.run_all'](
            '_scripts/pylint.sh -f colorized mc_states',
            use_vt=use_vt, cwd=mroot())
        if result['retcode']:
            raise _error('Pylint tests failed', result)
    except salt.exceptions.CommandExecutionError:
        trace = traceback.format_exc()
        raise _error('Problem with pylint install:\n {0}'.format(
            api.magicstring(trace)))


def unit_tests(tests=None,
               coverage=True,
               doctests=True,
               use_vt=True):
    in_args = '--exe -e mc_test -v -s'
    if isinstance(tests, basestring):
        tests = tests.split(',')
    if not tests:
        tests = ['mc_states']
    if coverage:
        in_args += (' --with-xcoverage'
                    ' --xcoverage-file=.coverage.xml')
    if doctests:
        in_args += ' --with-doctest'
    failed = OrderedDict()
    success = OrderedDict()
    for test in tests:
        try:
            result = __salt__['cmd.run_all'](
                'bin/nosetests {0} {1}'.format(
                    in_args, test),
                output_loglevel='debug',
                use_vt=use_vt, cwd=mroot())
            if result['retcode']:
                failed[test] = result
            else:
                success[test] = result
        except salt.exceptions.CommandExecutionError:
            trace = traceback.format_exc()
            raise _error('Problem with nose install:\n {0}'.format(
                api.magicstring(trace)))
    if failed:
        fail = failed.pop([a for a in failed][0])
        for ffail in failed:
            fail = saltapi.concat_res_or_rets(fail, ffail)
        raise _error('Doctest tests failed', fail)
    return success


def run_tests(flavors=None, use_vt=True):
    if not flavors:
        flavors = []
    if isinstance(flavors, basestring):
        flavors = flavors.split(',')
    success = OrderedDict()
    failures = OrderedDict()
    for step in ['lint', 'unit']:
        try:
            utils.test_setup()
            success[step] = __salt__['mc_test.{0}_tests'.format(step)](use_vt=use_vt)
        except (TestError,) as exc:
            failures[step] = exc
        except (Exception,):
            failures[step] = traceback.format_exc()
            break
        finally:
            utils.test_teardown()
    # for now, lint is not a failure
    acceptables = ['lint']
    for i in acceptables:
        failures.pop(i, None)
    if failures:
        _failures = dict([(a, "{0}".format(failures[a])) for a in failures])
        salt.output.display_output(_failures, opts=__opts__)
        raise TestError('test failure => non 0 exit code')
    # if no failure, be sure not to mark retcode as a failure
    __context__['retcode'] = 0
    return success


def run_travis_tests(use_vt=False):
    return run_tests('travis', use_vt=use_vt)
# vim:set et sts=4 ts=4 tw=80:
