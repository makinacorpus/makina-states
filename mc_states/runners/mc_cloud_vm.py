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
    merge_results,
    client,
    VMProvisionError,
    FailedStepError,
    MessageError,
)

log = logging.getLogger(__name__)


def vm_sls_pillar(compute_node, vm):
    cloudSettings = cli('mc_cloud.settings')
    cloudSettingsData = {}
    vmSettingsData = {}
    cnSettingsData = {}
    cloudSettingsData['all_sls_dir'] = cloudSettings['all_sls_dir']
    cloudSettingsData[
        'compute_node_sls_dir'] = cloudSettings['compute_node_sls_dir']
    cloudSettingsData['prefix'] = cloudSettings['prefix']
    cnsettings = cli('mc_cloud_compute_node.settings')
    targets = cnsettings.get('targets', {})
    cnSettingsData['virt_types'] = targets.get(
        compute_node, {}).get('virt_types', [])
    vmSettingsData['vm_name'] = vm
    vmSettingsData = api.json_dump(vmSettingsData)
    cloudSettingsData = api.json_dump(cloudSettingsData)
    cnSettingsData = api.json_dump(cnSettingsData)
    pillar = {'scloudSettings': cloudSettingsData,
              'mccloud_vmname': vm,
              'mccloud_targetname': compute_node,
              'svmSettings': vmSettingsData,
              'sisdevhost': api.json_dump(
                  cli('mc_nodetypes.registry')['is']['devhost']),
              'scnSettings': cnSettingsData}
    return pillar


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def _vm_configure(what, target, compute_node, vm, ret, output):
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'VM: Installing {2} on compute '
        '{0}/{1}\n'.format(compute_node, vm, what))
    pref = 'makina-states.cloud.generic.vm'
    ret = __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(pref, what), **{
            'salt_target': target,
            'ret': ret,
            'sls_kw': {'pillar': vm_sls_pillar(compute_node, vm)}})
    salt_output(ret, __opts__, output=output)
    return ret


def vm_grains(compute_node, vm, ret=None, output=True):
    return _vm_configure('grains', vm, compute_node, vm, ret, output)


def vm_initial_highstate(compute_node, vm, ret=None, output=True):
    return _vm_configure('initial_highstate', vm, compute_node, vm, ret, output)


def vm_initial_setup(compute_node, vm, ret=None, output=True):
    return _vm_configure('initial_setup', vm, compute_node, vm, ret, output)


def vm_sshkeys(compute_node, vm, ret=None, output=True):
    return _vm_configure('sshkeys', compute_node, vm, ret, output)


def provision(compute_node, vt, vm, ret=None, output=True):
    if ret is None:
        ret = result()
    for step in ['spawn',
                 'hostsfile',
                 'sshkeys',
                 'grains',
                 'initial_setup',
                 'initial_highstate']:
        pre_vid_ = 'mc_cloud_{0}.pre_vm_{1}'.format(vt, step)
        id_ = 'mc_cloud_vm.vm_{1}'.format(vt, step)
        post_vid_ = 'mc_cloud_{0}.vm_{1}'.format(vt, step)
        for cid_ in [pre_vid_, id_, post_vid_]:
            if (not ret['result']) or (cid_ not in __salt__):
                continue
            try:
                cret = __salt__[cid_](compute_node, vm, ret=ret, output=False)
                check_point(cret)
            except FailedStepError:
                trace = traceback.format_exc()
                cret['trace'] += trace
                cret['result'] = False
            if cret['result']:
                cret['trace'] = ''
                cret['output'] = ''
            merge_results(ret, cret)
    if ret['result']:
        ret['comment'] += red(
            '{0}/{1}/{2} deployed\n').format(compute_node, vt, vm)
    else:
        ret['comment'] += green(
            '{0}/{1}/{2} failed to deploy\n').format(compute_node, vt, vm)
    salt_output(ret, __opts__, output=output)
    return ret


def filter_vms(compute_node, vms, skip, only):
    todo = {}
    for vm, data in vms.items():
        if vm in skip.get(compute_node, []):
            continue
        if only:
            if vm not in only:
                continue
        todo[vm] = data
    return data


def provision_vms(compute_node,
                  skip=None, only=None, ret=None,
                  output=True, refresh=False):
    if ret is None:
        ret = result()
    if only is None:
        only = {}
    if skip is None:
        skip = {}
    if refresh:
        cli('saltutil.refresh_pillar')
    settings = cli('mc_cloud_compute_node.settings')
    gerror = ret['changes'].setdefault('vm_provisionned', {})
    gprov = ret['changes'].setdefault('vm_in_error', {})
    provision = gprov.setdefault(compute_node, [])
    provision_error = gerror.setdefault(compute_node, [])
    vms = settings['targets'].get(compute_node, {'virt_types': [], 'vms': {}})
    vms = filter_vms(compute_node, vms['vms'], only, skip)
    vms.sort()
    for vm, vt in vms.items():
        cret = result()
        try:
            cret = provision(compute_node, vt, vm, ret=cret, output=False, refresh=False)
            #if idx == 1:
            #    raise FailedStepError('foo')
            #elif idx > 0:
            #    raise Exception('bar')
        except FailedStepError:
            cret['result'] = False
        except Exception, exc:
            trace = traceback.format_exc()
            cret = {'result': False,
                    'output': 'unknown error on {0}/{2}\n{1}'.format(
                        compute_node, exc, vm),
                    'comment': 'unknown error on {0}/{1}\n'.format(
                        compute_node, vm),
                    'trace': trace}
        if cret['result']:
            provision[vm] = True
            if vm not in provision:
                provision.append(vm)
            # if everything is well, wipe the unseful output
            cret['output'] = ''
            cret['trace'] = ''
        else:
            ret['result'] = False
            if vm not in provision_error:
                provision_error.append(vm)
        cret.pop('result', False)
        merge_results(ret, cret)
    if len(provision_error):
        ret['comment'] += red('There were errors while provisionning '
                              'vms nodes {0}\n'.format(provision_error))
    else:
        del ret['trace']
        ret['comment'] += green('All vms were provisionned\n')
    salt_output(ret, __opts__, output=output)
    return ret


def orchestrate(compute_node,
                skip=None,
                only=None,
                output=True,
                refresh=False,
                ret=None):
    if skip is None:
        skip = []
    if only is None:
        only = []
    if ret is None:
        ret = result()
    provision_vms(compute_node, skip=skip, only=only,
                  output=output, refresh=refresh, ret=ret)
    salt_output(ret, __opts__, output=output)
    return ret


 # vim:set et sts=4 ts=4 tw=80:
