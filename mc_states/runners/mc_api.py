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
EVENT_TAG = 'makina_cloud'


def out(ret, __opts__, output=True, onlyret=False):
    return salt_output(ret,
                       __opts__,
                       output=output,
                       onlyret=onlyret,
                       __jid_event__=__jid_event__)


def cloud_event(msg='', *args, **kw):
    tag = kw.pop('event_tag', EVENT_TAG)
    category = kw.pop('event_category', None)
    kw['event_datetime'] = datetime.datetime.now().isoformat()
    payload = {'args': args, 'kw': kw,
               'message': msg, 'category': category}
    __jid_event__.fire_event(payload, tag)


def time_log(lifecycle_id='start', fun=None, *args, **extra_data):
    msg = extra_data.pop('msg', '')
    if not msg and (lifecycle_id in ['start', 'end']):
        msg = 'timer_{0}: {1}'.format(lifecycle_id, fun)
        lifecycle_id = 'timer_' + lifecycle_id
    return cloud_event(
        msg, event_category=lifecycle_id, fun=fun, *args, **extra_data)


def cli(*args, **kwargs):
    '''
    Correctly forward salt globals to a regular python module
    '''
    def _do(args, kwargs):
        if not kwargs:
            kwargs = {}
        kwargs.update({'salt_cfgdir': __opts__.get('config_dir', None),
                       'salt_cfg': __opts__.get('conf_file', None),
                       'salt___opts__': __opts__})
        return client(*args, **kwargs)
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


def get_cloud_images_settings(ttl=60):
    def _do():
        fname = 'mc_api.get_cloud_images_settings'
        __salt__['mc_api.time_log']('start', fname, __opts__['id'])
        settings = cli('mc_cloud_images.ext_pillar',
                       __opts__['id'], prefixed=False)
        __salt__['mc_api.time_log']('end', fname, settings=settings)
        return settings
    cache_key = 'rmc_api.get_cloud_images_settings'
    return memoize_cache(_do, [], {}, cache_key, ttl)


def get_cloud_controller_settings(ttl=60):
    def _do():
        fname = 'mc_api.get_cloud_controller_settings'
        __salt__['mc_api.time_log']('start', fname, __opts__['id'])
        settings = cli('mc_cloud_controller.ext_pillar',
                       __opts__['id'], prefixed=False)
        __salt__['mc_api.time_log']('end', fname, settings=settings)
        return settings
    cache_key = 'rmc_api.get_cloud_controller_settings'
    return memoize_cache(_do, [], {}, cache_key, ttl)


def get_cloud_settings(id_=None, ttl=60):
    def _do(id_):
        if not id_:
            id_ = __opts__['id']
        fname = 'mc_api.get_cloud_settings'
        __salt__['mc_api.time_log']('start', fname, id_)
        settings = cli('mc_cloud.ext_pillar', id_, prefixed=False)
        __salt__['mc_api.time_log']('end', fname, settings=settings)
        return settings
    cache_key = 'rmc_api.get_cloud_settings'
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_vm(vm, ttl=60):
    def _do(vm):
        fname = 'mc_api.get_vm'
        __salt__['mc_api.time_log']('start', fname, vm)
        vmdata = cli('mc_cloud_vm.vm_extpillar', vm)
        if not vmdata.get('vt', None):
            raise KeyError('vm is empty for {0}'.format(vm))
        __salt__['mc_api.time_log']('end', fname, vm=vm, vmdata=vmdata)
        return vmdata
    cache_key = 'rmc_api.get_vm{0}'.format(vm)
    return memoize_cache(_do, [vm], {}, cache_key, ttl)


def get_vt(vm, ttl=60):
    def _do(vm):
        fname = 'mc_api.get_vt'
        __salt__['mc_api.time_log']('start', fname, vm)
        vt = cli('mc_cloud_compute_node.vt_for_vm', vm)
        if not vt:
            raise KeyError('vt is empty for {0}'.format(vm))
        __salt__['mc_api.time_log']('end', fname, vm=vm, vt=vt)
        return vt
    cache_key = 'rmc_api.get_vt{0}'.format(vm)
    return memoize_cache(_do, [vm], {}, cache_key, ttl)


def get_compute_node_settings(compute_node=None, vm=None, ttl=60):
    def _do(compute_node, vm):
        fname = 'mc_api.get_compute_node_settings'
        __salt__['mc_api.time_log']('start', fname, compute_node, vm)
        if not compute_node and vm:
            compute_node = get_compute_node(vm)
        if not compute_node and not vm:
            raise Exception('Choose at least one cn or one vm')
        data = cli('mc_cloud_compute_node.ext_pillar',
                   compute_node, prefixed=False)
        __salt__['mc_api.time_log']('end', fname, data=data)
        return data
    cache_key = 'rmc_api.get_compute_node_settings{0}{1}'.format(
        compute_node, vm)
    return memoize_cache(_do, [compute_node, vm], {}, cache_key, ttl)


def get_compute_node(vm, ttl=60):
    def _do(vm):
        fname = 'mc_api.get_compute_node'
        __salt__['mc_api.time_log']('start', fname, vm)
        compute_node = cli('mc_cloud_compute_node.target_for_vm', vm)
        if not compute_node:
            raise KeyError('compute node is empty for {0}'.format(vm))
        __salt__['mc_api.time_log'](
            'end', fname, compute_node=compute_node)
        return compute_node
    cache_key = 'rmc_api.get_cn{0}'.format(vm)
    return memoize_cache(_do, [vm], {}, cache_key, ttl)


def ping():
    import time
    time.sleep(2)
    print ('foo')
    return 'bar'

# vim:set et sts=4 ts=4 tw=80:
