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
    '''limited cloud pillar to expose to a vm

    compute_node
        compute node to gather pillar from
    vm
        vm to gather pillar from
    '''
    cloudSettings = cli('mc_cloud.settings')
    cloudSettingsData = {}
    vmSettingsData = {}
    cnSettingsData = {}
    cloudSettingsData['all_sls_dir'] = cloudSettings['all_sls_dir']
    cloudSettingsData[
        'compute_node_sls_dir'] = cloudSettings['compute_node_sls_dir']
    cloudSettingsData['root'] = cloudSettings['root']
    cloudSettingsData['prefix'] = cloudSettings['prefix']
    cnsettings = cli('mc_cloud_compute_node.settings')
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
              'mccloud_vm_ssh_port': cli(
                  'mc_cloud_compute_node.get_ssh_port', compute_node, vm),
              'mccloud_targetname': compute_node,
              'svmSettings': vmSettingsData,
              'sisdevhost': api.json_dump(
                  cli('mc_nodetypes.registry')['is']['devhost']),
              'scnSettings': cnSettingsData}
    return pillar


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def get_vt(vm, vt=None):
    if vt is None:
        vt = cli('mc_cloud_compute_node.vt_for_vm', vm)
    if not vt:
        raise KeyError('vt is empty for {0}'.format(vm))
    return vt


def get_compute_node(vm, compute_node=None):
    if compute_node is None:
        compute_node = cli('mc_cloud_compute_node.target_for_vm', vm)
    if not compute_node:
        raise KeyError('compute node is empty for {0}'.format(vm))
    return compute_node


def _vm_configure(what, target, compute_node, vm, ret, output):
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'VM: Installing {2} on vm '
        '{0}/{1}\n'.format(compute_node, vm, what))
    pref = 'makina-states.cloud.generic.vm'
    ret = __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(pref, what), **{
            'salt_target': target,
            'ret': ret,
            'sls_kw': {'pillar': vm_sls_pillar(compute_node, vm)}})
    salt_output(ret, __opts__, output=output)
    return ret


def vm_markers(vm, compute_node=None, vt=None, ret=None, output=True):
    '''install markers at / of the vm for proxified access

        compute_node
            where to act
        vm
            vm to install grains into
    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    return _vm_configure('markers', vm, compute_node, vm, ret, output)


def vm_grains(vm, compute_node=None, vt=None, ret=None, output=True):
    '''install marker grains

        compute_node
            where to act
        vm
            vm to install grains into
    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    return _vm_configure('grains', vm, compute_node, vm, ret, output)


def vm_initial_highstate(vm, compute_node=None, vt=None, ret=None, output=True):
    '''Run the initial highstate, this step will run only once and will
    further check for the existence of
    <saltroot>/makina-states/.initial_hs file

        compute_node
            where to act
        vm
            vm to run highstate on
    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    return _vm_configure('initial_highstate',
                         None, compute_node, vm, ret, output)


def vm_sshkeys(vm, compute_node=None, vt=None, ret=None, output=True):
    '''Install controller ssh keys for user too on this specific vm

        compute_node
            where to act
        vm
            vm to install keys into
    '''
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('sshkeys', vm, compute_node, vm, ret, output)


def vm_ping(vm, compute_node=None, vt=None, ret=None, output=True):
    '''ping a specific vm on a specific compute node

        compute_node
            where to act
        vm
            vm to ping

    '''
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    if ret is None:
        ret = result()
    try:
        ping = cli('test.ping', salt_target=vm)
    except Exception:
        ret['trace'] += "{0}\n".format(traceback.format_exc())
        ping = False
    ret['result'] = ping
    if ret['result']:
        comment = green('VM {0} is pinguable\n')
    else:
        comment = red('VM {0} is unreachable\n')
    ret['comment'] += comment.format(vm)
    salt_output(ret, __opts__, output=output)
    return ret


def step(vm, step, compute_node=None, vt=None, ret=None, output=True):
    '''Execute a step on a VM noder'''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    if ret is None:
        ret = result()
    pre_vid_ = 'mc_cloud_{0}.vm_{1}'.format(vt, step)
    id_ = 'mc_cloud_vm.vm_{1}'.format(vt, step)
    post_vid_ = 'mc_cloud_{0}.post_vm_{1}'.format(vt, step)
    for cid_ in [pre_vid_, id_, post_vid_]:
        if (not ret['result']) or (cid_ not in __salt__):
            continue
        try:
            ret = __salt__[cid_](vm, compute_node=compute_node,
                                 vt=vt,
                                 ret=ret, output=False)
            check_point(ret, __opts__, output=output)
        except FailedStepError:
            ret['result'] = False
        except Exception, exc:
            trace = traceback.format_exc()
            ret['trace'] += 'lxcprovision: {0} in {1}\n'.format(
                exc, cid_)
            ret['trace'] += trace
            ret['result'] = False
            ret['comment'] += red('unmanaged exception for '
                                  '{0}/{1}/{2}'.format(compute_node, vt,
                                                       vm))
        if ret['result']:
            ret['trace'] = ''
            ret['output'] = ''
    salt_output(ret, __opts__, output=output)
    return ret


def provision(vm, compute_node=None, vt=None,
              steps=None, ret=None, output=True):
    '''provision a vm

    compute_node
         where to act
    vt
         virtual type
    vm
         vm to spawn
    steps
         list or comma separated list of steps
         Default::

              ['spawn', 'hostsfile', 'sshkeys',
              'grains', 'initial_setup', 'initial_highstate']
    '''
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    if isinstance(steps, basestring):
        steps = steps.split(',')
    if steps is None:
        steps = ['spawn',
                 'hostsfile',
                 'sshkeys',
                 'grains',
                 'markers',
                 'initial_setup',
                 'initial_highstate']
    if ret is None:
        ret = result()
    for step in steps:
        cret = __salt__['mc_cloud_vm.step'](vm, step,
                                            compute_node=compute_node,
                                            vt=vt,
                                            output=False)
        merge_results(ret, cret)
    if ret['result']:
        ret['comment'] += green(
            '{0}/{1}/{2} deployed\n').format(compute_node, vt, vm)
    else:
        ret['comment'] += red(
            '{0}/{1}/{2} failed to deploy\n').format(compute_node, vt, vm)
    salt_output(ret, __opts__, output=output)
    return ret


def post_provision(vm, compute_node=None, vt=None, ret=None, output=True):
    '''post provision a vm

    compute_node
         where to act
    vt
         virtual type
    vm
         vm to spawn
    steps
         list or comma separated list of steps
         Default::

              ['ping', 'post_provision_hook']

    '''
    if ret is None:
        ret = result()
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    for step in ['ping', 'post_provision_hook']:
        cret = __salt__['mc_cloud_vm.step'](vm, step,
                                            compute_node=compute_node,
                                            vt=vt, output=False)
        merge_results(ret, cret)
    if ret['result']:
        ret['comment'] += green(
            '{0}/{1}/{2} deployed\n').format(compute_node, vt, vm)
    else:
        ret['comment'] += red(
            '{0}/{1}/{2} failed to deploy\n').format(compute_node, vt, vm)
    salt_output(ret, __opts__, output=output)
    return ret


def filter_vms(compute_node, vms, skip, only):
    todo = {}
    for vm, data in vms.items():
        if vm in skip:
            continue
        if only:
            if vm not in only:
                continue
        todo[vm] = data
    return todo


def provision_vms(compute_node,
                  skip=None, only=None, ret=None,
                  output=True, refresh=False):
    '''Provision all vms on a compute node
    '''
    if ret is None:
        ret = result()
    if isinstance(only, basestring):
        only = only.split(',')
    if isinstance(skip, basestring):
        skip = skip.split(',')
    if only is None:
        only = []
    if skip is None:
        skip = []
    if refresh:
        cli('saltutil.refresh_pillar')
    settings = cli('mc_cloud_compute_node.settings')
    gprov = ret['changes'].setdefault('vms_provisionned', {})
    gerror = ret['changes'].setdefault('vms_in_error', {})
    provisionned = gprov.setdefault(compute_node, [])
    provision_error = gerror.setdefault(compute_node, [])
    vms = settings['targets'].get(compute_node, {'virt_types': [], 'vms': {}})
    vms = filter_vms(compute_node, vms['vms'], skip, only)
    kvms = [a for a in vms]
    kvms.sort()
    for idx, vm in enumerate(kvms):
        vt = vms[vm]
        cret = result()
        try:
            #if idx == 1:
            #    raise FailedStepError('foo')
            #elif idx > 0:
            #    raise Exception('bar')
            cret = provision(vm, compute_node=compute_node, vt=vt,
                             ret=cret, output=False)
        except FailedStepError, exc:
            trace = traceback.format_exc()
            cret['trace'] += '{0}\n'.format(exc.message)
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
            if vm not in provisionned:
                provisionned.append(vm)
            # if everything is well, wipe the unseful output
            cret['output'] = ''
            cret['trace'] = ''
        else:
            ret['result'] = False
            for k in ['trace', 'comment']:
                if k in cret:
                    val = ret.setdefault(k, '')
                    val += cret[k]
            if vm not in provision_error:
                provision_error.append(vm)
        cret.pop('result', False)
        merge_results(ret, cret)
    if len(provision_error):
        ret['comment'] += red('There were errors while provisionning '
                              'vms nodes {0}\n'.format(provision_error))
    else:
        if ret['result']:
            ret['trace'] = ''
            ret['comment'] += green('All vms were provisionned\n')
    salt_output(ret, __opts__, output=output)
    return ret


def post_provision_vms(compute_node,
                       skip=None, only=None, ret=None,
                       output=True, refresh=False):
    '''post provision all compute node vms'''
    if ret is None:
        ret = result()
    if isinstance(only, basestring):
        only = only.split(',')
    if isinstance(skip, basestring):
        skip = skip.split(',')
    if only is None:
        only = []
    if skip is None:
        skip = []
    if refresh:
        cli('saltutil.refresh_pillar')
    settings = cli('mc_cloud_compute_node.settings')
    gerror = ret['changes'].setdefault('postp_vms_provisionned', {})
    gprov = ret['changes'].setdefault('postp_vms_in_error', {})
    provisionned = gprov.setdefault(compute_node, [])
    provision_error = gerror.setdefault(compute_node, [])
    vms = settings['targets'].get(compute_node, {'virt_types': [], 'vms': {}})
    vms = filter_vms(compute_node, vms['vms'], skip, only)
    kvms = [a for a in vms]
    kvms.sort()
    for idx, vm in enumerate(kvms):
        vt = vms[vm]
        cret = result()
        try:
            #if idx == 1:
            #    raise FailedStepError('foo')
            #elif idx > 0:
            #    raise Exception('bar')
            cret = post_provision(vm, compute_node=compute_node, vt=vt,
                                  ret=cret, output=False)
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
            if vm not in provisionned:
                provisionned.append(vm)
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
        ret['comment'] += red('There were errors while post provisionning '
                              'vms nodes {0}\n'.format(provision_error))
    else:
        if ret['result']:
            ret['trace'] = ''
            ret['comment'] += green('All vms were post provisionned\n')
    salt_output(ret, __opts__, output=output)
    return ret


def orchestrate(compute_node,
                skip=None,
                only=None,
                output=True,
                refresh=False,
                ret=None):
    '''install all compute node vms'''
    ret = provision_vms(compute_node, skip=skip, only=only,
                        output=output, refresh=refresh, ret=ret)
    salt_output(ret, __opts__, output=output)
    return ret

# vim:set et sts=4 ts=4 tw=80:
