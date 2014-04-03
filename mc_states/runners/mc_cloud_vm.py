#!/usr/bin/env python
'''

.. _runner_mc_cloud_vm:

mc_cloud_vm runner
==========================

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
import salt.output
from salt.utils import check_state_result
import salt.minion
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states.saltapi import (
    salt_output,
    result,
    check_point,
    green, red, yellow,
    client,
    VMProvisionError,
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


def postdeploy(target, vm):
    ret = __salt__['mc_cloud_vm.install_highstate'](vm)
    checkpoint(rets, ret)


def provision(compute_node, vt, vm, output=True):
    ret = result()
    settings = cli('mc_cloud_{0}.settings'.format(vt))
    vm_settings = cli(
        'mc_cloud_compute_{0}.get_settings_for_vm'.format(vt),
        target, vm)
    try:
        for step in [
            'configure',
            'deploy',
            'postdeploy',
        ]:
            cret = __salt__['mc_cloud_{1}.{0}'.format](compute_node, vm)
            cret = __salt__['mc_cloud_{1}.{0}'.format](compute_node, vm)
            cret = __salt__['mc_cloud_{1}.{0}'.format](compute_node, vm)
    except Exception, exc:
        trace = traceback.format_exc()
        comment += yellow(
            '\nSaltificatioon failed for {0}: {1}'.format(compute_node,
                                                          exc))
        if not isinstance(exc, VMProvisionError):
            ret['trace'] += '\n'.format(trace)
        log.error(trace)
        salt_output(ret, __opts__, output=output)
    checkpoint(rets, ret)
    ret = __salt__['mc_cloud_vm.spawn'](vm)
    checkpoint(rets, ret)
    ret = __salt__['mc_cloud_vm.post_configure'](vm, salt_target=vm)
    checkpoint(rets, ret)
    return rets


def orchestrate(compute_node, vt, skip=None, output=True, refresh=False):
    if skip is None:
        skip = []
    ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    comment = ''
    settings = cli('mc_cloud_compute_node.settings')
    provision = ret['changes'].setdefault('provisionned', [])
    provision_error = ret['changes'].setdefault('in_error', [])
    vms = [a for a in settings['vms'] if a not in skip]
    vms.sort()
    for vm in vms:
        try:
            cret = provision(compute_node, vt, vm, output=False, refresh=False)
            if cret['result']:
                provision.append((compute_node, vt, vm))
            else:
                raise VMProvisionError(
                    'Target {0} failed to provision:\n{1}'.format(
                        compute_node, cret['comment']))
        except Exception, exc:
            trace = traceback.format_exc()
            comment += yellow(
                '\nProvision failed for {0}: {1}'.format(compute_node,
                                                         exc))
            if not isinstance(exc, VMProvisionError):
                ret['trace'] += '\n'.format(trace)
            log.error(trace)
            provision_error.append((compute_node, vt, vm))
    salt_output(ret, __opts__, output=output)
    return ret



# vim:set et sts=4 ts=4 tw=80:
