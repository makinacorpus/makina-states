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
import re
import datetime
import logging

# Import salt libs
import salt.client
import salt.payload
from mc_states.utils import memoize_cache
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
_REGISTRATION_CALL = {}
LXC_REF_RE = re.compile('lxc.*ref')


def vm_sls_pillar(compute_node, vm, ttl=api.RUNNER_CACHE_TIME):
    '''limited cloud pillar to expose to a vm
    This will be stored locally inside a local registry

    compute_node
        compute node to gather pillar from
    vm
        vm to gather pillar from
    '''
    func_name = 'mc_cloud_vm.vm_sls_pillar {0} {1}'.format(
        compute_node, vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))

    def _do(compute_node, vm):
        compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
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
        targets = cnsettings.get('targets', {})
        cnSettingsData['virt_types'] = targets.get(
            compute_node, {}).get('virt_types', [])
        vmSettingsData['vm_name'] = vm
        vt = targets.get(compute_node, {}).get('vms', {}).get(vm, None)
        vmSettingsData['vm_vt'] = vt
        supported_vts = cli('mc_cloud_compute_node.get_vts', supported=True)
        # vmSettingsData = api.json_dump(vmSettingsData)
        # cloudSettingsData = api.json_dump(cloudSettingsData)
        # cnSettingsData = api.json_dump(cnSettingsData)
        pillar = {'cloudSettings': cloudSettingsData,
                  'mccloud_vmname': vm,
                  'mccloud_vm_ssh_port': cli(
                      'mc_cloud_compute_node.get_ssh_port',
                      vm, target=compute_node),
                  'mccloud_targetname': compute_node,
                  'vmSettings': vmSettingsData,
                  'isdevhost': cli('mc_nodetypes.registry')['is']['devhost'],
                  'cnSettings': cnSettingsData}
        if vt in supported_vts:
            vtVmData = cli(
                'mc_cloud_{0}.get_settings_for_vm'.format(vt),
                compute_node, vm, full=False)
            pillar['vtVmData'] = vtVmData
        return pillar
    cache_key = 'mc_cloud_vm.vm_sls_pillar_{0}_{1}'.format(
        compute_node, vm)
    ret = memoize_cache(_do, [compute_node, vm], {}, cache_key, ttl)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def get_vt(vm, vt=None):
    func_name = 'mc_cloud_vm.get_vt {0} {1}'.format(vm, vt)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if vt is None:
        vt = cli('mc_cloud_compute_node.vt_for_vm', vm)
    if not vt:
        raise KeyError('vt is empty for {0}'.format(vm))
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return vt


def get_compute_node(vm, compute_node=None):
    func_name = 'mc_cloud_vm.get_vt {0} {1}'.format(vm, compute_node)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if compute_node is None:
        compute_node = cli('mc_cloud_compute_node.target_for_vm', vm)
    if not compute_node:
        raise KeyError('compute node is empty for {0}'.format(vm))
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return compute_node


def _vm_configure(what, target, compute_node, vm, ret, output):
    __salt__['mc_cloud_vm.lazy_register_configuration'](vm, compute_node)
    func_name = 'mc_cloud_vm._vm_configure {0} {1} {2} {3}'.format(
        what, target, compute_node, vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
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


def vm_initial_highstate(vm, compute_node=None, vt=None,
                         ret=None, output=True):
    '''Run the initial highstate, this step will run only once and will
    further check for the existence of
    <saltroot>/makina-states/.initial_hs file

        compute_node
            where to act
        vm
            vm to run highstate on

    ::

        mastersalt-run -lall mc_cloud_vm.vm_initial_highstate foo.domain.tld
    '''
    __salt__['mc_cloud_vm.lazy_register_configuration'](
        vm, compute_node)
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    if not ret:
        ret = result()
    pillar = __salt__['mc_cloud_vm.vm_sls_pillar'](compute_node, vm)
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    cmd = ("ssh -o\"ProxyCommand=ssh {target} nc -w300 {vm} 22\""
           " footarget {cloudSettings[root]}/makina-states/"
           "_scripts/boot-salt.sh "
           "--initial-highstate").format(vm=vm, target=compute_node,
                                         cloudSettings=pillar['cloudSettings'])
    unless = ("ssh -o\"ProxyCommand=ssh {target} "
              "nc -w300 {vm} 22\" footarget "
              "test -e '/etc/makina-states/initial_highstate'").format(
                  vm=vm, target=compute_node,
                  cloudSettings=pillar['cloudSettings'])
    cret = cli('cmd.run_all', unless)
    if cret['retcode']:
        rcret = cli('cmd.run_all', cmd, use_vt=True, output_loglevel='info')
        if not rcret['retcode']:
            ret['comment'] = (
                'Initial highstate done on {0}'.format(vm)
            )
        else:
            ret['result'] = False
            ret['trace'] += rcret['stdout'] + '\n'
            ret['trace'] += rcret['stderr'] + '\n'
            ret['comment'] += (
                'Initial highstate failed on {0}\n'.format(vm)
            )
    else:
        ret['comment'] += 'Initial highstate already done on {0}\n'.format(vm)
    salt_output(ret, __opts__, output=output)
    return ret


def vm_preprovision(vm, compute_node=None, vt=None,
                    ret=None, output=True):
    '''Run the preprovision:

        For performance reasons, this is a merge of steps

        - markers
        - grains
        - sshkeys

    ::

        mastersalt-run -lall mc_cloud_vm.vm_preprovision foo.domain.tld
    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    return _vm_configure('preprovision', vm, compute_node, vm, ret, output)


def vm_sshkeys(vm, compute_node=None, vt=None, ret=None, output=True):
    '''Install controller ssh keys for user too on this specific vm

        compute_node
            where to act
        vm
            vm to install keys into

     ::

        mastersalt-run -lall mc_cloud_vm.vm_sshkeys foo.domain.tld

    '''
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    # moved in the sls
    # id_rsa = cli('cmd.run', 'cat /root/.ssh/id_rsa.pub', salt_target=vm)
    # id_dsa = cli('cmd.run', 'cat /root/.ssh/id_dsa.pub', salt_target=vm)
    # if not LXC_REF_RE.search(vm):
    #     if LXC_REF_RE.search(id_rsa):
    #         log.info('Deleting default rsa ssh key')
    #         id_rsa = cli('cmd.run', 'rm -f /root/.ssh/id_rsa*', salt_target=vm)
    #     if LXC_REF_RE.search(id_dsa):
    #         log.info('Deleting default dsa ssh key')
    #         id_rsa = cli('cmd.run', 'rm -f /root/.ssh/id_dsa*', salt_target=vm)
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('sshkeys', vm, compute_node, vm, ret, output)


def vm_ping(vm, compute_node=None, vt=None, ret=None, output=True):
    '''ping a specific vm on a specific compute node

        compute_node
            where to act
        vm
            vm to ping
     ::

        mastersalt-run -lall mc_cloud_vm.vm_ping foo.domain.tld


    '''
    __salt__['mc_cloud_vm.lazy_register_configuration'](
        vm, compute_node)
    func_name = 'mc_cloud_vm.provision.ping {0}'.format(vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def vm_fix_dns(vm,
               compute_node=None,
               vt=None,
               ret=None,
               output=True,
               force=False):
    func_name = 'mc_cloud_vm.vm_fix_dns {0}'.format(vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if not ret:
        ret = result()
    # if we found some default dnses, set them as soon as we can
    # to avoid state orchestration problems and DNS issues that
    # would break the minion network
    dnses = cli('mc_bind.settings', salt_target=vm)['default_dnses']
    if dnses:
        cmd = 'echo > /etc/resolv.conf;echo >> /etc/resolv.conf;'
        for i in dnses:
            cmd += 'echo "nameserver \"{0}\"">>/etc/resolv.conf;'.format(i)
        cret = cli('cmd.retcode', cmd, salt_target=vm)
        if cret:
            ret['result'] = False
            ret['comment'] += red('pb with dns on {0}'.format(vm))
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def step(vm, step, compute_node=None, vt=None, ret=None, output=True):
    '''Execute a step on a VM noder'''
    func_name = 'mc_cloud_vm.provision.step {0} {1}'.format(vm, step)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
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
            ret['trace'] += 'VM provision: {0} in {1}\n'.format(
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
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

    ::

        mastersalt-run -lall mc_cloud_vm.provision foo.domain.tld

    '''
    func_name = 'mc_cloud_vm.provision {0}'.format(vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    vt = __salt__['mc_cloud_vm.get_vt'](vm, vt)
    if isinstance(steps, basestring):
        steps = steps.split(',')
    if steps is None:
        steps = ['register_configuration_on_cn',
                 'spawn',
                 'fix_dns',
                 'reconfigure',
                 'volumes',
                 'register_configuration',
                 'preprovision',
                 # 'sshkeys',
                 # 'hostsfile',
                 # 'grains',
                 # 'markers',
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
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

    ::

        mastersalt-run -lall mc_cloud_vm.post_provision foo.domain.tld
    '''
    func_name = 'mc_cloud_vm.post_provision {0}'.format(vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def filter_vms(compute_node, vms, skip, only):
    func_name = 'mc_cloud_vm.filter_vms'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    todo = {}
    for vm, data in vms.items():
        if vm in skip:
            continue
        if only:
            if vm not in only:
                continue
        todo[vm] = data
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return todo


def lazy_register_configuration_on_cn(vm, *args, **kwargs):
    '''
    Wrapper to register_configuration_on_cn at the exception
    that only one shared call can de done in a five minutes row.

    This can be used as a decorator in orchestrations functions
    to ensure configuration has been dropped on target tenants
    and is enoughtly up to date.
    '''
    ttl = kwargs.get('ttl', 5 * 60)
    salt_target = kwargs.get('salt_target', '')
    cache_key = 'mc_cloud_vm.lazy_register_configuration_on_cn_{0}_{1}'.format(
        vm, salt_target)

    def _do(vm, *args, **kwargs):
        return __salt__['mc_cloud_vm.register_configuration_on_cn'](
            vm, *args, **kwargs)
    ret = memoize_cache(_do, [vm] + list(args), kwargs, cache_key, ttl)
    return ret



def lazy_register_configuration(vm, *args, **kwargs):
    '''
    Wrapper to register_configuration at the exception
    that only one shared call can de done in a five minutes row.

    This can be used as a decorator in orchestrations functions
    to ensure configuration has been dropped on target tenants
    and is enoughtly up to date.
    '''
    ttl = kwargs.get('ttl', 5 * 60)
    salt_target = kwargs.get('salt_target', '')
    cache_key = 'mc_cloud_vm.lazy_register_configuration_{0}_{1}'.format(
        vm, salt_target)

    def _do(vm, *args, **kwargs):
        return __salt__['mc_cloud_vm.register_configuration'](
            vm, *args, **kwargs)
    ret = memoize_cache(_do, [vm] + list(args), kwargs, cache_key, ttl)
    return ret


def register_configuration(vm,
                           compute_node=None,
                           vt=None,
                           ret=None,
                           output=True,
                           salt_target=None):
    '''
    Register the configuration on the 'salt_target' node as a local registry

    salt_target is aimed to be the vm as default but can be
    any other reachable minion.

    Idea is that we copy this configuration on the compute node at first
    to provision the vm with the rights settings.
    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    func_name = 'mc_cloud_vm.register_configuration {0}'.format(vm)
    suf = ''
    if not salt_target:
        salt_target = vm
    if salt_target != vm:
        suf = '_{0}'.format(vm)
    if ret is None:
        ret = result()
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    settings = __salt__['mc_cloud_vm.vm_sls_pillar'](compute_node, vm)
    cret = cli(
        'mc_macros.update_local_registry',
        'cloud_vm_settings{0}'.format(suf),
        settings, registry_format='pack',
        salt_target=salt_target)
    if (
        isinstance(cret, dict)
        and(
            (
                'makina-states.local.'
                'cloud_vm_settings{0}.vmSettings'.format(
                    suf
                ) in cret
            )
        )
    ):
        ret['result'] = True
        ret['comment'] += yellow('VM Configuration stored'
                                 ' on {0}\n'.format(salt_target))
    else:
        ret['result'] = False
        ret['comment'] += red('VM Configuration failed to store'
                              ' on {0}\n'.format(salt_target))
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def register_configuration_on_cn(vm, compute_node=None, vt=None,
                                 ret=None, output=True):
    '''Register vm configuration copy on compute node

        compute_node
            where to act
        vm
            vm to install grains into
    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return register_configuration(vm, compute_node=compute_node, vt=vt,
                                  ret=ret, output=output,
                                  salt_target=compute_node)


def register_configurations(compute_node,
                            skip=None, only=None, ret=None,
                            output=True, refresh=False):
    '''Register all configurations in localregistries for reachable vms
    ::

        mastersalt-run -lall mc_cloud_vm.register_configurations host1.domain.tld
        mastersalt-run -lall mc_cloud_vm.register_configurations host1.domain.tld only=['foo.domain.tld']
        mastersalt-run -lall mc_cloud_vm.register_configurations host1.domain.tld skip=['foo2.domain.tld']

    '''
    func_name = 'mc_cloud_vm.configuration_vms'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    _, only, __, skip = (
        __salt__['mc_cloud_controller.gather_only_skip'](
            only_vms=only, skip_vms=skip))
    if refresh:
        cli('saltutil.refresh_pillar')
    settings = cli('mc_cloud_compute_node.settings')
    gprov = ret['changes'].setdefault('vms_configured', {})
    gerror = ret['changes'].setdefault('vms_in_error', {})
    configured = gprov.setdefault(compute_node, [])
    configuration_error = gerror.setdefault(compute_node, [])
    vms = settings['targets'].get(compute_node, {'virt_types': [], 'vms': {}})
    vms = filter_vms(compute_node, vms['vms'], skip, only)
    kvms = [a for a in vms]
    kvms.sort()
    for idx, vm in enumerate(kvms):
        vt = vms[vm]
        cret = result()
        try:
            # first: register the conf on compute node
            if not cli('test.ping', salt_target=compute_node):
                raise FailedStepError('not reachable')
            cret = register_configuration_on_cn(vm, compute_node=compute_node,
                                                vt=vt, ret=cret, output=False)
            check_point(cret, __opts__, output=output)
            # second: register the conf on VM
            # this may fail if the vm is not yet spawned
            if not cli('test.ping', salt_target=vm):
                raise FailedStepError('not reachable')
            cret = register_configuration(vm, compute_node=compute_node,
                                          vt=vt, ret=cret, output=False)
            check_point(cret, __opts__, output=output)
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
            if vm not in configured:
                configured.append(vm)
            # if everything is well, wipe the unseful output
            cret['output'] = ''
            cret['trace'] = ''
        else:
            ret['result'] = False
            for k in ['trace', 'comment']:
                if k in cret:
                    val = ret.setdefault(k, '')
                    val += cret[k]
            if vm not in configuration_error:
                configuration_error.append(vm)
        cret.pop('result', False)
        merge_results(ret, cret)
    if len(configuration_error):
        ret['comment'] += red('There were errors while configuring '
                              'vms nodes {0}\n'.format(configuration_error))
    else:
        if ret['result']:
            ret['trace'] = ''
            ret['comment'] += green('All vms were configured\n')
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def provision_vms(compute_node,
                  skip=None, only=None, ret=None,
                  output=True, refresh=False):
    '''Provision all or selected vms on a compute node

    ::

        mastersalt-run -lall mc_cloud_vm.provision_vms host1.domain.tld
        mastersalt-run -lall mc_cloud_vm.provision_vms host1.domain.tld only=['foo.domain.tld']
        mastersalt-run -lall mc_cloud_vm.provision_vms host1.domain.tld skip=['foo2.domain.tld']

    '''
    func_name = 'mc_cloud_vm.provision_vms'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    _, only, __, skip = (
        __salt__['mc_cloud_controller.gather_only_skip'](
            only_vms=only, skip_vms=skip))
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def post_provision_vms(compute_node,
                       skip=None, only=None, ret=None,
                       output=True, refresh=False):
    '''post provision all or selected compute node vms

    ::

        mastersalt-run -lall mc_cloud_vm.post_provision_vms host1.domain.tld
        mastersalt-run -lall mc_cloud_vm.post_provision_vms host1.domain.tld only=['foo.domain.tld']
        mastersalt-run -lall mc_cloud_vm.post_provision_vms host1.domain.tld skip=['foo2.domain.tld']

    '''
    func_name = 'mc_cloud_vm.post_provision_vms'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    _, only, __, skip = (
        __salt__['mc_cloud_controller.gather_only_skip'](
            only_vms=only, skip_vms=skip))
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def orchestrate(compute_node,
                skip=None,
                only=None,
                output=True,
                refresh=False,
                ret=None):
    '''install all compute node vms

    ::

        mastersalt-run -lall mc_cloud_vm.orchestrate host1.domain.tld
        mastersalt-run -lall mc_cloud_vm.orchestrate host1.domain.tld only=['foo.domain.tld']
        mastersalt-run -lall mc_cloud_vm.orchestrate host1.domain.tld skip=['foo2.domain.tld']

    '''
    func_name = 'mc_cloud_vm.orchestrate'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    __salt__['mc_api.time_log'](func_name)
    if refresh:
        cli('saltutil.refresh_pillar')
    ret = provision_vms(compute_node, skip=skip, only=only,
                        output=output, refresh=False,
                        ret=ret)
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret
# vim:set et sts=4 ts=4 tw=80:
