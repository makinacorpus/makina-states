#!/usr/bin/env python
'''
.. _runner_mc_cloud_compute_node:

mc_cloud_compute_node runner
============================
'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import python libs
import os
import traceback
import logging

# Import salt libs
import salt.client
import salt.payload
import salt.utils
from salt.utils import check_state_result
import salt.output
import salt.minion
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states.saltapi import (
    salt_output,
    result,
    green, red, yellow,
    check_point,
    client,
    FailedStepError,
    MessageError,
)


log = logging.getLogger(__name__)


def _checkpoint(ret):
    if not ret['result']:
        raise FailedStepError('stop')


def pre_deploy(output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    ret = result()
    try:
        run_vt_hook(ret, 'pre_configure_controller')
        id_ = cli('config.get', 'id')
        cret = cli('state.sls',
                   'makina-states.cloud.generic.controller.pre-deploy')
        ret['result'] = check_state_result(cret)
        ret['output'] = salt.output.get_printout(
            'highstate', __opts__)({id_: cret})
        if ret['result']:
            ret['comment'] += green(
                'Global cloud controller configuration is applied')
        else:
            ret['comment'] += red(
                'Cloud controller failed to configure:\n')
        check_point(ret)
        run_vt_hook(ret, 'post_configure_controller')
    except FailedStepError:
        if output:
            salt.output.display_output(ret, '', __opts__)
        raise
    if output:
        salt.output.display_output(ret, '', __opts__)
    return ret


def configure():
    ret = result()
    return ret


def postconfigure():
    ret = result()
    return ret


def configure_firewall(target):
    ret = result()
    return ret


def configure(target, vm):
    ret = result()
    return ret
    try:
        pass
    except:
        pass


def orchestrate(target, rets=None):
    if rets is None:
        rets = []
    return rets
    settings = cli('mc_cloud_compute_node.settings')
    t_settings = cli('mc_cloud_compute_node.get_settings_for_target', target)

    ret = result()
    rets = []
    ret = configure_cloud()
    return ret
    checkpoint(rets, ret)
    vms = {}
    configure()
    for vm in vms:
        try:
            ret = __salt__[
                'mc_cloud_{0}.orchestrate'.format(
                    vt)]()
            configure_vm(target, vm)
            ret = __salt__['mc_cloud_controller.post_configure'](compute_nodes)
        except:
            continue
    post_configure()
    checkpoint(rets, ret)
    return rets

#
