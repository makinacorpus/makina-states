#!/usr/bin/env python
from __future__ import absolute_import, print_function
'''

.. _runner_mc_cloud_kvm:

mc_cloud_kvm runner
==========================



'''
# -*- coding: utf-8 -*-

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
from mc_states.api import memoize_cache
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
VT = 'kvm'


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def post_deploy_controller(output=True):
    '''
    Prepare cloud controller KVM configuration
    '''
    fname = 'mc_cloud_kvm.post_deploy_controller'
    _s = __salt__
    _s['mc_api.time_log']('start', fname)
    ret = result()
    ret['comment'] = yellow('Installing controller kvm configuration\n')
    p = 'makina-states.cloud.kvm.controller'
    ret = _s['mc_api.apply_sls'](['{0}.postdeploy'.format(p)], **{'ret': ret})
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def cn_configure(what, target, ret, output):
    _s = __salt__
    fname = 'mc_cloud_kvm.cn_configure'
    _s['mc_api.time_log']('start', fname, what, target)
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'KVM: Installing {1} on compute node {0}\n'.format(target, what))
    p = 'makina-states.cloud.kvm.compute_node'
    ret = _s['mc_api.apply_sls']('{0}.{1}'.format(p, what),
                                 **{'salt_target': target, 'ret': ret})
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def configure_install_vt(target, ret=None, output=True):
    '''
    install kvm
    '''
    return cn_configure('install_kvm', target, ret, output)


def upgrade_vt(target, ret=None, output=True):
    '''
    Upgrade KVM hosts
    NOT IMPLEMENTED
    '''
    fname = 'mc_cloud_kvm.upgrade_vt'
    __salt__['mc_api.time_log']('start', fname, target)
    if not ret:
        ret = result()
    __salt__['mc_api.time_log']('end', fname)
    return ret


def sync_images(target, output=True, ret=None):
    '''
    sync images on target
    NOT IMPLEMENTED
    '''
    fname = 'mc_cloud_kvm.sync_images'
    __salt__['mc_api.time_log']('start', fname, target)
    if ret is None:
        ret = result()
    __salt__['mc_api.time_log']('end', fname)
    return ret


def install_vt(target, output=True):
    '''
    install & configure kvm
    '''
    fname = 'mc_cloud_kvm.install_vt'
    __salt__['mc_api.time_log']('start', fname, target)
    ret = result()
    ret['comment'] += yellow('Installing kvm on {0}\n'.format(target))
    for step in [configure_install_vt]:
        try:
            step(target, ret=ret, output=False)
        except FailedStepError:
            pass
    __salt__['mc_cloud_kvm.sync_images'](target, output=False, ret=ret)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', fname)
    return ret


def post_post_deploy_compute_node(target, output=True):
    '''
    post deployment hook for controller
    '''
    fname = 'mc_cloud_kvm.post_post_deploy_compute_node'
    __salt__['mc_api.time_log']('start', fname, target)
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
        status = 'success'
    else:
        clr = red
        status = 'failure'
    ret['comment'] += clr(msg.format(status))
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', fname)
    return ret


def vm_configure(what, vm, ret=None, output=True):
    fname = 'mc_cloud_kvm.vm_configure'
    __salt__['mc_api.time_log']('start', fname, what, vm)
    vm_data = _s['mc_api.get_vm'](vm)
    cn = vm_data['target']
    if ret is None:
        ret = result()
    ret['comment'] += yellow('KVM: Installing {2} on vm'
                             ' {0}/{1}\n'.format(cn, vm, what))
    pref = 'makina-states.cloud.kvm.vm'
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(pref, what), **{'salt_target': vm, 'ret': ret})
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', fname)
    return ret
# vim:set et sts=4 ts=4 tw=80:
