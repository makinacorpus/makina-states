#!/usr/bin/env python
'''

.. _runner_mc_cloud_lxc:

mc_cloud_lxc runner
==========================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import python libs
import os
import logging
import traceback

# Import salt libs
import salt.client
import salt.payload
import salt.utils
import salt.output
import salt.minion
from salt.utils import check_state_result
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states.saltapi import (
    result,
    check_point,
    green, red, yellow,
    client,
    FailedStepError,
    MessageError,
)

log = logging.getLogger(__name__)


def cli(*args, **kwargs):
    if not kwargs:
        kwargs = {}
    kwargs.update({
        'salt_cfgdir': __opts__.get('config_dir', None),
        'salt_cfg': __opts__.get('conf_file', None),
    })
    return client(*args, **kwargs)


def post_configure_controller(output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    ret = result()
    try:
        id_ = cli('config.get', 'id')
        cret = cli('state.sls',
                   'makina-states.cloud.lxc.controller.pre-deploy')
        ret['result'] = check_state_result(cret)
        soutput = salt.output.get_printout(
            'highstate', __opts__)({id_: cret})
        ret['output'] = soutput
        if ret['result']:
            ret['comment'] += green(
                'LXC cloud controller configuration '
                'is applied')
        else:
            ret['comment'] += red(
                'LXC cloud controller configuration '
                'failed to configure:\n')
        check_point(ret)
    except FailedStepError:
        if output:
            salt.output.display_output(ret, '', __opts__)
        raise
    if output:
        salt.output.display_output(ret, '', __opts__)
    return ret


def post_deploy_controller(output=False):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    ret = result()
    try:
        id_ = cli('config.get', 'id')
        cret = cli('state.sls',
                   'makina-states.cloud.lxc.controller.post-deploy')
        ret['result'] = check_state_result(cret)
        soutput = salt.output.get_printout(
            'highstate', __opts__)({id_: cret})
        ret['output'] = soutput
        if ret['result']:
            ret['comment'] += green(
                'LXC cloud controller '
                'post-configuration is applied')
        else:
            ret['comment'] += red(
                'LXC cloud controller '
                'post-configuration failed to configure:\n')
        check_point(ret)
    except FailedStepError:
        if output:
            salt.output.display_output(ret, '', __opts__)
        raise
    if output:
        salt.output.display_output(ret, '', __opts__)
    return ret


def deploy_pre(target, vm, rets=None):
    ret = __salt__['mc_cloud_vm.spawn'](vm)
    checkpoint(rets, ret)


def postdeploy_pre(target, vm, rets=None):
    ret = __salt__['mc_cloud_vm.install_grains'](vm)
    checkpoint(rets, ret)
    ret = __salt__['mc_cloud_vm.install_hosts'](vm)
    checkpoint(rets, ret)
    ret = __salt__['mc_cloud_vm.install_sshkeys'](vm)
    checkpoint(rets, ret)
    ret = __salt__['mc_cloud_vm.install_deploy'](vm)
    checkpoint(rets, ret)
    ret = __salt__['mc_cloud_vm.install_deploy'](vm)
    checkpoint(rets, ret)

# vim:set et sts=4 ts=4 tw=80:
