#!/usr/bin/env python
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
    green, red, yellow,
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
    return result()


def run_vt_hook(hook_name, ret=None, target=None, vts=None, *args, **kwargs):
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
            vts = settings['targets'][target]['virt_types']
    if isinstance(vts, basestring):
        vts = [vts]
    for vt in vts:
        vid_ = 'mc_cloud_{0}.{1}'.format(vt, hook_name)
        if vid_ in __salt__:
            ret['comment'] += green('Executing {0} hook\n'.format(vid_))
            kwargs['output'] = False
            import pdb;pdb.set_trace()  ## Breakpoint ##
            cret = __salt__[vid_](*args, **kwargs)
            merge_results(ret, cret)
            check_point(ret, __opts__)
    return ret


def pre_deploy(output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    kw = {'ret': result(), 'output': output}
    try:
        run_vt_hook('pre_configure_controller', ret=kw['ret'])
        __salt__['mc_api.apply_sls'](
            ['makina-states.cloud.generic.controller.pre-deploy',
             'makina-states.cloud.saltify'], **kw)
        check_point(ret, __opts__)
        run_vt_hook('post_configure_controller', ret=kw['ret'])
    except FailedStepError:
        salt_output(kw['ret'], __opts__, output=output)
        raise
    salt_output(kw['ret'], __opts__, output=output)
    return kw['ret']


def deploy():
    ret = result()
    run_vt_hook('pre_deploy_controller', ret=ret)
    run_vt_hook('post_deploy_controller', ret=ret)
    return ret


def post_deploy():
    ret = result()
    run_vt_hook('pre_post_deploy_controller', ret=ret)
    run_vt_hook('post_post_deploy_controller', ret=ret)
    return ret


def exists(name):
    cloudSettings = cli('mc_cloud.settings')
    key = '{prefix}/pki/master/minions/{name}'.format(
        prefix=cloudSettings['prefix'], name=name)
    already_exists = os.path.exists(key)
    if not already_exists:
        try:
            instance = __salt__['cloud.action'](
                fun='show_instance', names=[name])
            prov = str(instance.keys()[0])
            if instance and 'Not Actioned' not in prov:
                already_exists = True
        except:
            trace = traceback.format_exc()
            log.warn(trace)
    return already_exists


def orchestrate(output=True, refresh=True):
    ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    try:
        ret = pre_deploy()
        check_point(ret, __opts__)
        ret = deploy()
        check_point(ret, __opts__)
        cret = __salt__['mc_cloud_saltify.orchestrate'](
            output=False, refresh=False)
        if cret['result']:
            ret['comment'] += cret['comment']
            ret['trace'] += cret['trace']
        cn_in_error = cret['changes'].get('saltified_errors', [])
        c_ret = __salt__['mc_cloud_compute_node.orchestrate'](
            skip=cn_in_error, output=False)
        if cret['result']:
            ret['comment'] += cret['comment']
            ret['trace'] += cret['trace']
        cn_in_error = cret['changes'].get('provision_error', [])
    except FailedStepError:
        salt_output(ret, __opts__, output=output)
        raise
    salt_output(ret, __opts__, output=output)
    return ret

#
