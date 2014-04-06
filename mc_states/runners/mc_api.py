#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
'''

.. _mc_runners_api:

Convenient functions to use a salt infra as an api
===================================================
Internal module used as api.
'''
import salt.output
from pprint import pformat
import traceback

from mc_states.saltapi import (
    result,
    client,
    check_state_result,
    green,
    FailedStepError,
    yellow,
    SaltExit,
    red,
    merge_results,
    salt_output,
)


def cli(*args, **kwargs):
    '''Correctly forward salt globals to a regular
    python module
    '''
    if not kwargs:
        kwargs = {}
    kwargs.update({
        'salt_cfgdir': __opts__.get('config_dir', None),
        'salt_cfg': __opts__.get('conf_file', None),
        'salt___opts__': __opts__,
    })
    return client(*args, **kwargs)


def apply_sls_(func, slss,
               salt_output_t='highstate',
               status_msg=None,
               sls_status_msg=None,
               ret=None,
               output=False,
               *a, **kwargs):
    target = kwargs.get('salt_target',
                        __grains__.get('id',
                                       __opts__.get('id', 'local')))
    if ret is None:
        ret = result()
    if isinstance(slss, basestring):
        slss = [slss]
    sls_kw = kwargs.pop('sls_kw', {})
    statuses = []
    salt_ok, salt_ko = 'success', 'failed'
    for sls in slss:
        cret = None
        try:
            cret = cli(func, sls, *a, **sls_kw)
            if not isinstance(cret, dict):
                raise SaltExit(
                    'Execution failed(return) for sls: {0}: '
                    '\n{1}'.format(sls, cret))
            if not check_state_result(cret):
                raise SaltExit('Execution failed for sls: {0}'.format(sls))
            ret['output'] += '{0}\n'.format(
                salt.output.get_printout(
                    salt_output_t, __opts__)({target: cret}).rstrip())
            statuses.append((salt_ok, sls))
        except SaltExit, exc:
            trace = traceback.format_exc()
            ret['result'] = False
            ret['output'] += '- {0}\n{1}\n'.format(yellow(sls), exc)
            ret['trace'] += '{0}\n'.format(trace)
            statuses.append((salt_ko, sls))
            if cret:
                ret['trace'] += '\n{0}'.format(pformat(cret))
    clr = ret['result'] and green or red
    status = ret['result'] and salt_ok or salt_ko
    if not status_msg:
        status_msg = yellow('  Installation on {0}: ') + red('{1}\n')
    if not sls_status_msg:
        sls_status_msg = yellow('   - {0}: ') + red('{2}\n')
    ret['comment'] += clr(status_msg.format(target, red(status)))
    if len(statuses) > 1:
        for status, sls in statuses:
            if status == salt_ko:
                clr = red
            else:
                clr = yellow
            ret['comment'] += clr(
                sls_status_msg.format(sls, target, status))
    return ret


def apply_sls_template(slss, *a, **kwargs):
    return apply_sls_('state.template', slss, *a, **kwargs)


def apply_sls(slss, *a, **kwargs):
    '''
    args:

        slss
            one or list of sls
        output
            output to stdout
        ret
            mc_state results dict
        salt_target
            target
        sls_kw
            useful to give pillar.
            (**{sls_kw: {pillar: {1:2}}})


    '''
    return apply_sls_('state.sls', slss, *a, **kwargs)


# vim:set et sts=4 ts=4 tw=80:
