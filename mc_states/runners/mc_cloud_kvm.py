#!/usr/bin/env python
from __future__ import absolute_import, print_function
'''

.. _runner_mc_cloud_kvm:

mc_cloud_kvm runner
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
from mc_states.utils import memoize_cache
import salt.minion
from salt.utils import check_state_result
from salt.cloud.exceptions import SaltCloudSystemExit
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


def post_deploy_controller(output=True):
    '''
    Prepare cloud controller KVM configuration
    '''
    func_name = 'mc_cloud_kvm.post_deploy_controller'
    __salt__['mc_api.time_log']('start', func_name)
    ret = result()
    ret['comment'] = yellow('Installing controller kvm configuration\n')
    pref = 'makina-states.cloud.kvm.controller'
    ret = __salt__['mc_api.apply_sls'](
        ['{0}.postdeploy'.format(pref)],
        **{'ret': ret})
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def _cn_configure(what, target, ret, output):
    func_name = 'mc_cloud_kvm._cn_configure'
    __salt__['mc_api.time_log']('start', func_name, what, target)
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'KVM: Installing {1} on compute node {0}\n'.format(target, what))
    pref = 'makina-states.cloud.kvm.compute_node'
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(pref, what), **{'salt_target': target, 'ret': ret})
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def configure_install_kvm(target, ret=None, output=True):
    '''
    install kvm
    '''
    return _cn_configure('install_kvm', target, ret, output)


def upgrade_vt(target, ret=None, output=True):
    '''
    Upgrade KVM hosts
    This will reboot all containers upon kvm upgrade
    Containers are marked as being rebooted, and unmarked
    as soon as this script unmark explicitly them to be
    done.
    '''
    func_name = 'mc_cloud_kvm.upgrade_vt'
    __salt__['mc_api.time_log']('start', func_name, target)
    if not ret:
        ret = result()
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def sync_images(target, output=True, ret=None):
    '''
    sync images on target
    '''
    func_name = 'mc_cloud_kvm.sync_images'
    __salt__['mc_api.time_log']('start', func_name, target)
    if ret is None:
        ret = result()
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def install_vt(target, output=True):
    '''
    install & configure kvm
    '''
    func_name = 'mc_cloud_kvm.install_vt'
    __salt__['mc_api.time_log']('start', func_name, target)
    ret = result()
    ret['comment'] += yellow('Installing kvm on {0}\n'.format(target))
    for step in [
        configure_install_kvm
    ]:
        try:
            step(target, ret=ret, output=False)
        except FailedStepError:
            pass
    __salt__['mc_cloud_kvm.sync_images'](target, output=False, ret=ret)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name)
    return ret


def post_post_deploy_compute_node(target, output=True):
    '''
    post deployment hook for controller
    '''
    func_name = 'mc_cloud_kvm.post_post_deploy_compute_node {0}'.format(
        target)
    __salt__['mc_api.time_log']('start', func_name)
    ret = result()
    nodetypes_reg = cli('mc_nodetypes.registry')
    slss, pref = [], 'makina-states.cloud.kvm.compute_node'
    if nodetypes_reg['is']['devhost']:
        slss.append('{0}.devhost'.format(pref))
    if slss:
        ret =  __salt__['mc_api.apply_sls'](
            slss, **{'salt_target': target, 'ret': ret})
    msg = 'Post installation: {0}\n'
    if ret['result']:
        clr = green
        status = 'sucess'
    else:
        clr = red
        status = 'failure'
    ret['comment'] += clr(msg.format(status))
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def _vm_configure(what, target, compute_node, vm, ret, output):
    func_name = 'mc_cloud_kvm._vm_configure'
    __salt__['mc_api.time_log'](
        'start', func_name, what, target, compute_node, vm)
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'KVM: Installing {2} on vm '
        '{0}/{1}\n'.format(compute_node, vm, what))
    pref = 'makina-states.cloud.kvm.vm'
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(pref, what), **{'salt_target': target, 'ret': ret})
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret
# vim:set et sts=4 ts=4 tw=80:
