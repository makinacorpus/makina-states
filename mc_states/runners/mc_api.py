#!/usr/bin/env python
from __future__ import absolute_import, print_function
'''

.. _mc_runners_mc_api:

mc_api
======
Convenient functions to use a salt infra as an api
Internal module used as api.
'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import salt.output
from pprint import pformat
from mc_states.utils import memoize_cache
import traceback
import datetime
import logging

from mc_states import api
from mc_states.saltapi import (
    result,
    client,
    SaltInvalidReturnError,
    check_state_result,
    green,
    FailedStepError,
    blue,
    SaltEmptyDictError,
    yellow,
    SaltExit,
    red,
    merge_results,
    salt_output,
)
log = logging.getLogger(__name__)


def out(ret, __opts__, output=True, onlyret=False):
    return salt_output(ret,
                       __opts__,
                       output=output,
                       onlyret=onlyret,
                       __jid_event__= __jid_event__)


def time_log(msg='Point', categ='CLOUD_TIMER'):
    __jid_event__.fire_event(
        {'data': msg, 'category': categ},
        'makina_cloud'
    )

def cli(*args, **kwargs):
    '''Correctly forward salt globals to a regular
    python module
    '''
    def _do(args, kwargs):
        if not kwargs:
            kwargs = {}
        kwargs.update({
            'salt_cfgdir': __opts__.get('config_dir', None),
            'salt_cfg': __opts__.get('conf_file', None),
            'salt___opts__': __opts__,
        })
        return client(*args, **kwargs)
    fun_ = args[0]

    defaults_ttls = {}
    #    'mc_cloud_compute_node.target_for_vm': 60,
    #    'mc_cloud_compute_node.vt_for_vm': 60,
    #    'mc_cloud_compute_node.get_reverse_proxies_for_target': 60,
    #    'mc_cloud_compute_node.get_settings_for_target': 60,
    #    'mc_cloud_saltify.settings_for_target': 60,
    #}
    ttl = kwargs.pop('cache_ttl',
                     defaults_ttls.get(fun_,
                                       api.RUNNER_CACHE_TIME))
    cache_key = ''
    if (
        fun_ in [
            'mc_cloud_compute_node.target_for_vm',
            'mc_cloud_compute_node.vt_for_vm',
            'mc_cloud_compute_node.get_reverse_proxies_for_target',
            'mc_cloud_compute_node.get_settings_for_target',
            'mc_cloud_saltify.settings_for_target',
        ]
    ) or (
        fun_.endswith('.get_settings_for_vm')
    ):
        cache_key = ' '.join(['{0}'.format(a) for a in args])
    if (
        fun_ in [
            'mc_nodetypes.registry'
        ]
    ) or (
        fun_.endswith('.settings')
        and len(args) == 1
        and not kwargs
    ):
            cache_key = fun_
    if cache_key:
        __salt__['mc_api.time_log'](cache_key, categ='CLOUD_CACHE')
        return memoize_cache(_do, [args, kwargs], {}, cache_key, ttl)
    else:
        return _do(args, kwargs)


def valid_state_return(cret, sls=None):
    if not isinstance(cret, dict):
        msg = 'Execution failed(return is not a dict)'
        if sls:
            msg += 'for {0}:\n{{0}}'.format(sls)
        raise SaltEmptyDictError(msg.format(pformat(cret)))
    if not check_state_result(cret):
        msg = 'Execution failed(return is not valid)'
        if sls:
            msg += 'for {0}:\n{{0}}'.format(sls)
        raise SaltEmptyDictError(msg.format(pformat(cret)))
    return cret


def filter_state_return(cret, target='local', output='nested'):
    if not isinstance(cret, dict):
        # for list of strings, output the concatenation
        # for better error inspection
        if isinstance(cret, list):
            onlystrings = True
            for i in cret:
                if not isinstance(i, basestring):
                    onlystrings = False
                    break
            if onlystrings:
                cret = '\n'.join(cret)
    else:
        try:
            cret = salt.output.get_printout(
                output, __opts__)({target: cret}).rstrip()
        except:
            try:
                cret = salt.output.get_printout(
                    output, __opts__)(cret).rstrip()
            except:
                if output != 'nested':
                    cret = salt.output.get_printout(
                        'nested', __opts__)(cret).rstrip()
    return cret


def apply_sls_(func, slss,
               salt_output_t='highstate',
               status_msg=None,
               sls_status_msg=None,
               ret=None,
               output=False,
               *a, **kwargs):
    local_target = __grains__.get('id', __opts__.get('id', 'local'))
    target = salt_target = kwargs.pop('salt_target', None)
    if target is None:
        target = local_target
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
            cliret = cli(func, sls, salt_target=salt_target, *a, **sls_kw)
            cret = filter_state_return(cliret, target=target,
                                       output=salt_output_t)
            valid_state_return(cliret, sls=sls)
            ret['output'] += cret
            statuses.append((salt_ok, sls))
        except SaltExit, exc:
            trace = traceback.format_exc()
            ret['result'] = False
            ret['output'] += '- {0}\n{1}\n'.format(yellow(sls), exc)
            ret['trace'] += '{0}\n'.format(trace)
            statuses.append((salt_ko, sls))
            if cret:
                ret['trace'] += '{0}\n'.format(pformat(cret))
                ret['output'] += '{0}\n'.format(cret)
    clr = ret['result'] and green or red
    status = ret['result'] and salt_ok or salt_ko
    if not status_msg:
        if target:
            status_msg = yellow('  Installation on {0}: ') + clr('{1}\n')
        else:
            status_msg = yellow('  Installation: ') + clr('{1}\n')
    ret['comment'] += status_msg.format(target, status)
    sls_status_msg = yellow('   - {0}:') + ' {2}\n'
    if len(statuses) > 1:
        for status, sls in statuses:
            if status == salt_ko:
                sclr = red
            else:
                sclr = green
            status = sclr(status)
            ret['comment'] += sls_status_msg.format(sls, target, status)
    return ret


def apply_sls_template(slss, *a, **kwargs):
    return apply_sls_('state.template', slss, *a, **kwargs)


def apply_sls(slss, concurrent=True, *a, **kwargs):
    '''
    args

        slss
            one or list of sls
        output
            output to stdout
        ret
            mc_state results dict
        salt_target
            target
        sls_kw
            useful to give pillar::

                (**{sls_kw: {pillar: {1:2}}})

    '''
    sls_kw = kwargs.setdefault('sls_kw',  {})
    sls_kw.setdefault('concurrent', concurrent)
    return apply_sls_('state.sls', slss, *a, **kwargs)


def ping():
    import time
    time.sleep(2)
    print ('foo')
    return 'bar'

# vim:set et sts=4 ts=4 tw=80:
