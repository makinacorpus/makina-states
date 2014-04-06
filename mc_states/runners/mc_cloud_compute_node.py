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
    ComputeNodeProvisionError,
    salt_output,
    result,
    green, red, yellow,
    check_point,
    client,
    FailedStepError,
    merge_results,
    MessageError,
)


log = logging.getLogger(__name__)


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def _checkpoint(ret):
    if not ret['result']:
        raise FailedStepError('stop')


def pre_deploy(target, output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    ret, opt = result(), __opts__
    try:
        run_vt_hook('pre_configure_compute_node', ret=ret, target=target)
        check_point(ret)
        for step in [configure_ssh,
                     configure_grains,
                     configure_hosts,
                     install_vts,
                     configure_firewall,
                     configure_reverse_proxy,]:
            cret = step(target)
            check_point(ret)
            ret['result'] = check_state_result(cret)
            ret['output'] = salt.output.get_printout(
                'highstate', opt)({target: cret})
            if ret['result']:
                ret['comment'] += green(
                    'Global cloud controller configuration is applied\n')
            else:
                ret['comment'] += red(
                    'Cloud controller failed to configure:\n')
            check_point(ret)
        run_vt_hook('post_configure_compute_node', ret=ret, target=target)
    except FailedStepError:
        if output:
            salt.output.display_output(ret, '', __opts__)
        raise
    if output:
        salt.output.display_output(ret, '', __opts__)
    return ret


def configure_grains(target):
    ret = result()
    ret['comment'] = 'Grains installed for {0}\n'.format(target)
    return ret


def configure_ssh(target):
    ret = result()
    ret['comment'] = 'SSH key installed for {0}\n'.format(target)
    return ret


def run_vt_hook(hook_name, target, ret=None, vts=None, *args, **kwargs):
    return  __salt__['mc_cloud_controller.run_vt_hook'](hook_name,
                                                        ret=ret,
                                                        target=target,
                                                        vts=vts,
                                                        *args, **kwargs)


def install_vts(target, output=False):
    ret = run_vt_hook('install_vt', target=target)
    if ret['result']:
        ret['comment'] += yellow('{0} can now host {1} vms\n'.format(target))
    salt_output(ret, __opts__, output=output)
    return ret


def configure_firewall(target):
    ret = result()
    ret['comment'] = 'Firewall configured for {0}\n'.format(target)
    return ret


def configure_reverse_proxy(target):
    ret = result()
    ret['comment'] = 'Reverse proxy configured for {0}\n'.format(target)
    return ret


def configure_hosts(target):
    ret = result()
    ret['comment'] = '/etc/hosts configured for {0}\n'.format(target)
    return ret


def postconfigure():
    ret = result()
    return ret


def provision_targets(skip=None, output=True, refresh=False):
    if skip is None:
        skip = []
    ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    comment = ''
    settings = cli('mc_cloud_compute_node.settings')
    provision = ret['changes'].setdefault('provisionned', [])
    provision_error = ret['changes'].setdefault('in_error', [])
    targets = []
    for a in settings['targets']:
        if a not in skip and a not in targets:
            targets.append(a)
        else:
            ret['comment'] += yellow(
                'compute node {0} provision skipped\n'.format(a))
    targets.sort()
    for compute_node in targets:
        try:
            cret = __salt__['mc_cloud_compute_node.provision'](
                compute_node, output=False)
            if cret['result']:
                provision.append(compute_node)
            else:
                raise ComputeNodeProvisionError(
                    'Target {0} failed to provision:\n{1}'.format(
                        compute_node, cret['comment']))
        except Exception, exc:
            trace = traceback.format_exc()
            comment += yellow(
                'Compute node prvision failed for '
                '{0}: {1}\n'.format(compute_node, exc))
            if not isinstance(exc, ComputeNodeProvisionError):
                ret['trace'] += '\n'.format(trace)
            log.error(trace)
            provision_error.append(compute_node)
    salt_output(ret, __opts__, output=output)
    return ret


def provision_vms(skip=None, skip_vms=None, output=True, refresh=False):
    if skip is None:
        skip = []
    if skip_vms is None:
        skip_vms = {}
    ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    comment = ''
    settings = cli('mc_cloud_compute_node.settings')
    provision = ret['changes'].setdefault('provisionned', [])
    provision_error = ret['changes'].setdefault('in_error', [])
    targets = []
    for a in settings['targets']:
        if a not in skip and a not in targets:
            targets.append(a)
        else:
            ret['comment'] += yellow(
                'compute node {0} provision skipped\n'.format(a))
    for compute_node in targets:
        for vm, vt in settings[compute_node]['vms'].items():
            if vm in skip_vms.get(compute_node, []):
                ret['comment'] += yellow(
                    'Compute node vms {0}/{2}/{1} '
                    'provision skipped\n'.format(a, vm, vt))
                continue
            try:
                ret = __salt__['mc_cloud_vm.orchestrate'](target, vt, vm)
            except Exception, exc:
                trace = traceback.format_exc()
                comment += yellow(
                    '\nCompute node vm prvision failed for '
                    '{0}/{1}: {2}\n'.format(compute_node, vm, exc))
                if not isinstance(exc, ComputeNodeProvisionError):
                    ret['trace'] += '\n'.format(trace)
                log.error(trace)
                provision_error.append((compute_node, vt, vm))
    salt_output(ret, __opts__, output=output)
    return ret


def post_configure_targets(skip=None, output=True, refresh=False):
    if skip is None:
        skip = []
    ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    comment = ''
    settings = cli('mc_cloud_compute_node.settings')
    provision = ret['changes'].setdefault('provisionned', [])
    provision_error = ret['changes'].setdefault('in_error', [])
    targets = []
    for a in settings['targets']:
        if a not in skip and a not in targets:
            targets.append(a)
        else:
            ret['comment'] += yellow(
                'compute node {0} provision skipped\n'.format(a))
    for compute_node in targets:
        try:
            ret = __salt__[
                'mc_cloud_{0}.orchestrate'.format(
                    vt)]()
            configure_vm(target, vm)
            ret = __salt__['mc_cloud_controller.post_configure'](compute_node)
        except Exception, exc:
            trace = traceback.format_exc()
            comment += yellow(
                '\nCompute node prvision failed for '
                '{0}: {1}'.format(compute_node, exc))
            if not isinstance(exc, ComputeNodeProvisionError):
                ret['trace'] += '\n'.format(trace)
            log.error(trace)
            provision_error.append(compute_node)
    salt_output(ret, __opts__, output=output)
    return ret


def orchestrate(skip=None, skip_vms=None, output=True, refresh=False):
    if skip is None:
        skip = []
    if skip_vms is None:
        skip_vms = {}
    ret = result()
    cret = provision_targets(skip=skip, output=output,
                             refresh=refresh, ret=ret)
    cn_in_error = ret['changes'].setdefault(
        'cn_in_errors', cret['changes'].get('in_error', []))
    if cret['result']:
        if len(cn_in_error):
            ret['comment'] += cret['comment']
            ret['trace'] += cret['trace']
        else:
            ret['comment'] += 'All computes nodes were provisionned\n'

    vcret = provision_vms(skip=skip, output=output, refresh=refresh, ret=ret)
    vms_in_errors = ret['changes'].setdefault(
        'vm_in_errors', vcret['changes'].get('in_error', {}))
    if cret['result']:
        if len(vms_in_errors):
            ret['comment'] += cret['comment']
            ret['trace'] += cret['trace']
        else:
            ret['comment'] += 'All vms were provisionned\n'
    skip_vms.update(vms_in_errors)
    pcret = post_configure_targets(skip=skip, skip_vms=skip_vms,
                                   output=output, refresh=refresh, ret=ret)
    pcn_in_error = ret['changes'].setdefault(
        'cn_in_post_provisionerrors',
        pcret['changes'].get('in_error', []))
    if cret['result']:
        if len(pcn_in_error):
            ret['comment'] += cret['comment']
            ret['trace'] += cret['trace']
        else:
            ret['comment'] += 'All post procedures controller/vm were done\n'
    return ret
#
