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
from pprint import pformat
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
    merge_results,
    result,
    salt_output,
    check_point,
    SaltExit,
    green, red, yellow,
    SaltCopyError,
    FailedStepError,
    MessageError,
)

log = logging.getLogger(__name__)


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def compute_node_pillar(target):
    cloudSettings = cli('mc_cloud.settings')
    imgSettings = cli('mc_cloud_images.settings')
    lxcSettings = cli('mc_cloud_lxc.settings')
    imgSettingsData = {}
    lxcSettingsData = {}
    for name, imageData in imgSettings['lxc']['images'].items():
        imgSettingsData[name] = {
            'lxc_tarball': imageData['lxc_tarball'],
            'lxc_tarball_md5': imageData['lxc_tarball_md5'],
            'lxc_tarball_name': imageData['lxc_tarball_name'],
            'lxc_tarball_ver': imageData['lxc_tarball_ver']}
    for name, imageData in lxcSettings['defaults'].items():
        data = lxcSettingsData.setdefault(name, {})
        for v in ['use_bridge', 'bridge',
                  'gateway', 'netmask_full',
                  'network', 'netmask']:
            data[v] = lxcSettings['defaults'][v]
    imgSettingsData = api.json_dump(imgSettingsData)
    lxcSettingsData = api.json_dump(lxcSettingsData)
    pillar = {'slxcSettings': lxcSettingsData,
              'simgSettings': imgSettingsData,
              'sprefix': cloudSettings['prefix']}
    return pillar


def post_configure_controller(output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    ret = result()
    try:
        id_ = cli('config.get', 'id')
        cret = __salt__['mc_api.apply_sls'](
            'makina-states.cloud.lxc.controller.pre-deploy')
        merge_results(ret, cret)
        if ret['result']:
            ret['comment'] += green(
                'LXC cloud controller configuration '
                'is applied\n')
        else:
            ret['comment'] += red(
                'LXC cloud controller configuration '
                'failed to configure:\n')
        check_point(ret, __opts__)
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
        cret = __salt__['mc_salt.apply_sls'](
            'makina-states.cloud.lxc.controller.post-deploy')
        merge_results(ret, cret)
        if ret['result']:
            ret['comment'] += green(
                'LXC cloud controller '
                'post-configuration is applied\n')
        else:
            ret['comment'] += red(
                'LXC cloud controller '
                'post-configuration failed to configure:\n')
        check_point(ret, __opts__)
    except FailedStepError:
        if output:
            salt.output.display_output(ret, '', __opts__)
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


def install_vt(target, output=True):
    ret = result()
    ret['comment'] = yellow('Installing lxc on {0}\n'.format(target))
    pref = 'makina-states.cloud.lxc.compute_node'
    ret =  __salt__['mc_api.apply_sls'](
        ['{0}.pre-deploy.grains'.format(pref),
         '{0}.pre-deploy.install-lxc'.format(pref),
         '{0}.pre-deploy.images'.format(pref)],
        **{'salt_target': target,
           'ret': ret,
           'sls_kw': {'pillar': compute_node_pillar(target)}})
    salt_output(ret, __opts__, output=output)
    return ret
# vim:set et sts=4 ts=4 tw=80:
