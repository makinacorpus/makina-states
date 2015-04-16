#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
__docformat__ = 'restructuredtext en'
import os
import traceback
import salt.exceptions
import salt.output

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


def lint_tests():
    try:
        result = __salt__['cmd.run_all'](
            '_scripts/pylint.sh -f colorized mc_states',
            use_vt=True, cwd=mroot())
        if result['retcode']:
            raise _error('Pylint tests failed', result)
    except salt.exceptions.CommandExecutionError:
        trace = traceback.format_exc()
        raise _error('Problem with pylint install:\n {0}'.format(
            api.magicstring(trace)))


def unit_tests():
    try:
        result = __salt__['cmd.run_all'](
            'bin/nosetests -s -v --exe -w mc_states/tests/unit',
            use_vt=True, cwd=mroot())
        if result['retcode']:
            raise _error('Unit tests failed', result)
    except salt.exceptions.CommandExecutionError:
        trace = traceback.format_exc()
        raise _error('Problem with nose install:\n {0}'.format(
            api.magicstring(trace)))


def run_tests(flavors=None):
    if not flavors:
        flavors = []
    if isinstance(flavors, basestring):
        flavors = flavors.split(',')
    failures = {}
    for step in ['lint', 'unit']:
        try:
            utils.test_setup()
            __salt__['mc_test.{0}_tests'.format(step)]()
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


def run_travis_tests():
    return run_tests('travis')
# vim:set et sts=4 ts=4 tw=80:
