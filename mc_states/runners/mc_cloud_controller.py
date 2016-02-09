#!/usr/bin/env python
from __future__ import absolute_import, print_function
'''

.. _runner_mc_cloud_controller:

mc_cloud_controller runner
==========================



'''
# -*- coding: utf-8 -*-

# Import python libs
import os
import logging
import traceback

from pprint import pformat
from mc_states.api import memoize_cache

# Import salt libs
from salt.utils import check_state_result
import salt.client
import salt.payload
import salt.utils
import salt.output
import salt.minion
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states.saltapi import (
    ComputeNodeProvisionError,
    merge_results,
    salt_output,
    result,
    green, red, yellow, blue,
    check_point,
    client,
    FailedStepError,
    MessageError,
)

import salt.output

log = logging.getLogger(__name__)


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def post_configure(output=True):
    '''post configuration'''
    return result()


def run_vt_hook(hook_name,
                ret=None,
                target=None,
                vts=None,
                output=True,
                *args, **kwargs):
    '''
    Run an hook for a special vt
    on a controller, or a compute node or a vm
    '''
    fname = 'mc_cloud_controller.run_vt_hook'
    _s = __salt__
    _s['mc_api.time_log']('start', fname, hook_name, target)
    if target:
        kwargs['target'] = target
    if ret is None:
        ret = result()
    if not vts:
        if not target:
            settings = _s['mc_api.get_cloud_controller_settings']()
            vts = [vt for vt in settings['vts']
                   if settings['vts'][vt] and vt not in ['generic', 'saltify']]
        else:
            settings = _s['mc_api.get_compute_node_settings'](target)
            vts = settings['vts']
    if isinstance(vts, basestring):
        vts = [vts]
    for vt in vts:
        vid_ = 'mc_cloud_{0}.{1}'.format(vt, hook_name)
        if vid_ in _s:
            ret['comment'] += green('\n --> ') + blue(vid_) + green(' hook\n')
            kwargs['output'] = False
            cret = _s[vid_](*args, **kwargs)
            merge_results(ret, cret)
            check_point(ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def dns_conf(output=True, ret=None):
    '''
    Prepare cloud controller dns (BIND) server
    '''
    fname = 'mc_cloud_controller.dns_conf'
    __salt__['mc_api.time_log']('start', fname)
    if ret is None:
        ret = result()
    kw = {'ret': ret, 'output': output}
    kw['ret']['comment'] += green(
        'Installing cloud controller DNS configuration\n')
    run_vt_hook('pre_dns_conf_on_controller', ret=kw['ret'], output=output)
    __salt__['mc_api.apply_sls'](
        ['makina-states.cloud.generic.controller.dnsconf'], **kw)
    check_point(kw['ret'], __opts__, output=output)
    run_vt_hook('post_dns_conf_on_controller', ret=kw['ret'], output=output)
    __salt__['mc_api.out'](kw['ret'], __opts__, output=output)
    __salt__['mc_api.time_log']('end', fname)
    return kw['ret']


def deploy(output=True, ret=None):
    '''
    Prepare cloud controller configuration
    can also apply per virtualization type configuration
    '''
    fname = 'mc_cloud_controller.deploy'
    __salt__['mc_api.time_log']('start', fname)
    if ret is None:
        ret = result()
    kw = {'ret': ret, 'output': output}
    kw['ret']['comment'] += green(
        'Installing cloud controller configuration files\n')
    run_vt_hook('pre_deploy_controller', ret=kw['ret'], output=output)
    __salt__['mc_api.apply_sls'](
        ['makina-states.cloud.generic.controller',
         'makina-states.cloud.saltify.controller'], **kw)
    check_point(kw['ret'], __opts__, output=output)
    run_vt_hook('post_deploy_controller', ret=kw['ret'], output=output)
    __salt__['mc_api.out'](kw['ret'], __opts__, output=output)
    __salt__['mc_api.time_log']('end', fname)
    return kw['ret']


def exists(name):
    '''
    return true if the 'target' is already provisionned
    '''
    cloudSettings = __salt__['mc_api.get_cloud_settings']()
    key = '{prefix}/pki/master/minions/{name}'.format(
        prefix=cloudSettings['prefix'], name=name)
    already_exists = os.path.exists(key)
    return already_exists


def gather_only_skip(only=None,
                     skip=None,
                     skip_vms=None,
                     only_vms=None):
    if only is None:
        only = []
    if skip is None:
        skip = []
    if only_vms is None:
        only_vms = []
    if skip_vms is None:
        skip_vms = []
    if isinstance(only, basestring):
        only = only.split(',')
    if isinstance(skip, basestring):
        skip = skip.split(',')
    if isinstance(only_vms, basestring):
        only_vms = only_vms.split(',')
    if isinstance(skip_vms, basestring):
        skip_vms = skip_vms.split(',')
    if only_vms and not only:
        # fiter compute nodes here
        for vm in only_vms:
            target = __salt__['mc_api.get_vm'](vm)['target']
            if target not in only:
                only.append(target)
    return (only,
            only_vms,
            skip,
            skip_vms)


def orchestrate(only=None,
                only_vms=None,
                skip=None,
                skip_vms=None,
                no_controller=False,
                no_dns_conf=False,
                no_configure=False,
                no_saltify=False,
                no_provision=False,
                no_vms=False,
                no_compute_nodes=False,
                no_post_provision=False,
                no_vms_post_provision=False,
                output=True,
                refresh=True,
                ret=None):
    '''
    install controller, compute node, vms & run postdeploy

        no_configure
            skip configuring the cloud controller
        skip
            list of compute nodes to skip
        skip_vms
            list of vm to skip
        only
            explicit list of compute nodes to deploy
        only_vms
            explicit list of vm to deploy
        no_provision
            skip compute node & vm provision
        no_compute_nodes
            skip configuration of compute nodes
        no_vms
            do not provision vms
        no_post_provision
            do not post provision compute nodes
        no_vms_post_provision
            do not post provision vms


    '''
    fname = 'mc_cloud_controller.orchestrate'
    __salt__['mc_api.time_log']('start', fname,
                                skip=skip,
                                skip_vms=skip_vms,
                                only=only,
                                only_vms=only_vms,
                                no_dns_conf=no_dns_conf,
                                no_controller=no_controller,
                                no_configure=no_configure,
                                no_saltify=no_saltify,
                                no_provision=no_provision,
                                no_vms=no_vms,
                                no_compute_nodes=no_compute_nodes,
                                no_post_provision=no_post_provision,
                                no_vms_post_provision=no_vms_post_provision,
                                refresh=refresh)
    only, only_vms, skip, skip_vms = (
        __salt__['mc_cloud_controller.gather_only_skip'](
            only=only,
            only_vms=only_vms,
            skip=skip,
            skip_vms=skip_vms))
    if ret is None:
        ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    cret = result()
    gret = True
    try:
        # only deploy base configuration if we did not set
        # a specific saltify/computenode/vm switch
        if not no_controller:
            if not no_dns_conf:
                dns_conf(output=False, ret=cret)
                check_point(cret, __opts__, output=output)
                del cret['result']
                merge_results(ret, cret)
            if not no_configure:
                cret = result()
                # test that all hosts resolve else
                # for the dns migration
                deploy(output=False, ret=cret)
                check_point(cret, __opts__, output=output)
                del cret['result']
                merge_results(ret, cret)
        if not no_saltify:
            cret = result()
            __salt__['mc_cloud_saltify.orchestrate'](
                only=only, skip=skip, ret=cret,
                output=False, refresh=False)
            check_point(cret, __opts__, output=output)
            del cret['result']
            merge_results(ret, cret)
        cn_in_error = cret['changes'].get('saltified_errors', [])
        if not no_provision:
            if not skip:
                skip = []
            skip += cn_in_error
            cret = result()
            cret['result'] = False
            __salt__['mc_cloud_compute_node.orchestrate'](
                skip=skip,
                skip_vms=skip_vms,
                only=only,
                only_vms=only_vms,
                no_provision=no_provision,
                no_compute_nodes=no_compute_nodes,
                no_post_provision=no_post_provision,
                no_vms_post_provision=no_vms_post_provision,
                no_vms=no_vms,
                refresh=False,
                output=False,
                ret=cret)
            # make the global exec continue if the provision of a CN failed
            if not cret['result']:
                gret = cret['result']
            del cret['result']
            merge_results(ret, cret)
            cn_in_error = cret['changes'].get('provision_error', [])
    except FailedStepError:
        merge_results(ret, cret)
        trace = traceback.format_exc()
        ret['output'] += '\n{0}'.format(trace)
        __salt__['mc_api.out'](ret, __opts__, output=output)
        ret['result'] = False
    # make the exec fail if the provision of at least one CN failed
    ret['result'] = gret and ret['result']
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', fname)
    return ret


def prepare_controller(no_saltify=True,
                       no_compute_nodes=True,
                       no_vms=True,
                       *a, **kw):
    '''
    Shortcut to prepare the controller

    (DNS; VT orchestration)
    '''
    return orchestrate(no_saltify=no_saltify,
                       no_compute_nodes=no_compute_nodes,
                       no_vms=no_vms,
                       *a, **kw)


def saltify_node(target,
                 no_controller=True,
                 no_compute_nodes=True,
                 no_vms=True,
                 *a, **kw):
    '''
    Shortcut to only saltify something
    '''
    return orchestrate(no_controller=no_controller,
                       no_compute_nodes=no_compute_nodes,
                       no_vms=no_vms,
                       only=target,
                       *a, **kw)


def configure_vm(target,
                 no_controller=True,
                 no_compute_nodes=True,
                 no_saltify=True,
                 *a, **kw):
    '''
    Shortcut to only configure vm
    '''
    return orchestrate(no_controller=no_controller,
                       no_saltify=no_saltify,
                       no_compute_nodes=no_compute_nodes,
                       only_vms=target,
                       *a, **kw)


def configure_node(target,
                   no_saltify=True,
                   no_vms=True,
                   no_controller=True,
                   *a, **kw):
    '''
    Shortcut to only configure a compute node
    '''
    return orchestrate(no_controller=no_controller,
                       no_saltify=no_saltify,
                       no_vms=no_vms,
                       only=target,
                       *a, **kw)


def report(*a, **kw):
    '''
    Alias to mc_cloud_compute_node.report
    '''
    return __salt__['mc_cloud_compute_node.report'](*a, **kw)


def remove(node_name,
           destroy=False,
           remove_key=True,
           only_stop=False,
           **kwargs):
    '''
    Remove a node
    NOTE: only lxc vms are supported for now
    Actually this consists in:

        - disabling crons
        - disabling services
        - unlinking the key from salt

    '''
    _s = __salt__
    settings = _s['mc_api.get_cloud_controller_settings']()
    if node_name not in settings['vms']:
        return False
    vm = settings['vms'][node_name]
    fun = 'mc_cloud_{0[vt]}.remove'.format(vm)
    if fun not in _s:
        return False
    kwargs['remove_key'] = remove_key
    kwargs['destroy'] = destroy
    kwargs['only_stop'] = only_stop
    ret = _s[fun](node_name, **kwargs)
    return ret


def test(*a, **kw):
    import time
    print('bar')
    time.sleep(2)
    raise FailedStepError('foo')
#
