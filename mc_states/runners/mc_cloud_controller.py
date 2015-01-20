#!/usr/bin/env python
from __future__ import absolute_import, print_function
'''

.. _runner_mc_cloud_controller:

mc_cloud_controller runner
==========================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import python libs
import os
import logging
import traceback

from pprint import pformat
from mc_states.utils import memoize_cache

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
    '''Run an hook for a special vt
    on a controller, or a compute node or a vm'''
    func_name = 'mc_cloud_controller.run_vt_hook'
    __salt__['mc_api.time_log']('start', func_name, hook_name, target)
    if target:
        kwargs['target'] = target
    if ret is None:
        ret = result()
    if not vts:
        if not target:
            settings = cli('mc_cloud_controller.settings')
            vts = settings['vts']
        else:
            settings = cli('mc_cloud_compute_node.settings')
            vts = settings['targets'][target]['vts']
    if isinstance(vts, basestring):
        vts = [vts]
    for vt in vts:
        vid_ = 'mc_cloud_{0}.{1}'.format(vt, hook_name)
        if vid_ in __salt__:
            ret['comment'] += (
                green('\n --> ') + blue(vid_) + green(' hook\n')
            )
            kwargs['output'] = False
            cret = __salt__[vid_](*args, **kwargs)
            merge_results(ret, cret)
            check_point(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def dns_conf(output=True, ret=None):
    '''
    Prepare cloud controller dns (BIND) server
    '''
    func_name = 'mc_cloud_controller.dns_conf'
    __salt__['mc_api.time_log']('start', func_name)
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
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return kw['ret']


def deploy(output=True, ret=None):
    '''
    Prepare cloud controller configuration
    can also apply per virtualization type configuration
    '''
    func_name = 'mc_cloud_controller.deploy'
    __salt__['mc_api.time_log']('start', func_name)
    if ret is None:
        ret = result()
    kw = {'ret': ret, 'output': output}
    kw['ret']['comment'] += green(
        'Installing cloud controller configuration files\n')
    run_vt_hook('pre_deploy_controller', ret=kw['ret'], output=output)
    __salt__['mc_api.apply_sls'](
        ['makina-states.cloud.generic.controller',
         'makina-states.cloud.saltify'], **kw)
    check_point(kw['ret'], __opts__, output=output)
    run_vt_hook('post_deploy_controller', ret=kw['ret'], output=output)
    __salt__['mc_api.out'](kw['ret'], __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
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
            target = __salt__[
                'mc_cloud_vm.get_compute_node'](
                    vm)
            if target not in only:
                only.append(target)
    return (only,
            only_vms,
            skip,
            skip_vms)


def orchestrate(skip=None,
                skip_vms=None,
                only=None,
                only_vms=None,
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
    '''install controller, compute node, vms & run postdeploy

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
    func_name = 'mc_cloud_controller.orchestrate'
    __salt__['mc_api.time_log']('start', func_name,
                                skip=skip,
                                skip_vms=skip_vms,
                                only=only,
                                only_vms=only_vms,
                                no_dns_conf=no_dns_conf,
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
    try:
        # only deploy base configuration if we did not set
        # a specific saltify/computenode/vm switch
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
            del cret['result']
            merge_results(ret, cret)
        cn_in_error = cret['changes'].get('saltified_errors', [])
        if not no_provision:
            if not skip:
                skip = []
            skip += cn_in_error
            cret = result()
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
            del cret['result']
            merge_results(ret, cret)
            cn_in_error = cret['changes'].get('provision_error', [])
    except FailedStepError:
        merge_results(ret, cret)
        trace = traceback.format_exc()
        ret['output'] += '\n{0}'.format(trace)
        __salt__['mc_api.out'](ret, __opts__, output=output)
        raise
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def report(*a, **kw):
    '''
    Alias to mc_cloud_compute_node.report
    '''
    return __salt__['mc_cloud_compute_node.report'](*a, **kw)
#
