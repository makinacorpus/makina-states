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
    apply_sls,
    result,
    salt_output,
    check_point,
    SaltExit,
    green, red, yellow,
    SaltCopyError,
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


def install_vt(target, output=False):
    ret = result()
    pre_slss = [
        'pre-deploy/grains.sls',
        'pre-deploy/install-lxc.sls',
        'pre-deploy/images.sls',
    ]
    cdir = '/srv/cloud-controller'
    imgSettings = cli('mc_cloud_images.settings')
    lxcSettings = cli('mc_cloud_lxc.settings')
    imgSettingsData = {}
    lxcSettingsData = {}
    for name, imageData in imgSettings['lxc']['images'].items():
        imgSettingsData[name] = {
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
    slsfs = []
    try:
        for sls in pre_slss:
            dst = '{0}/lxc/{1}'.format(cdir, sls)
            ret = cli('cp.get_template',
                      'salt://makina-states/cloud/lxc/compute_node/{0}'.format(sls),
                      dst,
                      simgSettings=imgSettingsData,
                      slxcSettings=lxcSettingsData,
                      makedirs=True, salt_target=target)
            if ret != dst:
                raise SaltCopyError('Cant copy {0} to {1}'.format(dst, target))
            ret = cli('cmd.run', 'chmod 700 "{0}"'.format(dst))
            slsfs.append(dst)
            apply_sls(cli, slsfs, target=target)
    except FailedStepError:
        salt_output(ret, __opts__, output=output)
        raise
    except SaltCopyError, ex:
        ret['comment'] += '{0}'.format(ex)
        ret['result'] = False
        salt_output(ret, __opts__, output=output)
        raise
    salt_output(ret, __opts__, output=output)
    return ret




# vim:set et sts=4 ts=4 tw=80:
