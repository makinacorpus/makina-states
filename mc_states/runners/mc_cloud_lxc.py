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
    '''Prepare cloud controller LXC configuration'''
    func_name = 'mc_cloud_lxc.post_deploy_controller'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    ret = result()
    ret['comment'] = yellow('Installing controller lxc configuration\n')
    pref = 'makina-states.cloud.lxc.controller'
    ret = __salt__['mc_api.apply_sls'](
        ['{0}.postdeploy'.format(pref)],
        **{'ret': ret})
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def _cn_configure(what, target, ret, output):
    func_name = 'mc_cloud_lxc._cn_configure {0} {1}'.format(
        what, target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'LXC: Installing {1} on compute node {0}\n'.format(target, what))
    pref = 'makina-states.cloud.lxc.compute_node'
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(pref, what), **{
            'salt_target': target,
            'ret': ret})
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def configure_install_lxc(target, ret=None, output=True):
    '''install lxc'''
    return _cn_configure('install_lxc', target, ret, output)


def configure_images(target, ret=None, output=True):
    '''configure all images templates'''
    return _cn_configure('images', target, ret, output)


def upgrade_vt(target, ret=None, output=True):
    '''Upgrade LXC hosts
    This will reboot all containers upon lxc upgrade
    Containers are marked as being rebooted, and unmarked
    as soon as this script unmark explicitly them to be
    done.
    '''
    func_name = 'mc_cloud_lxc.upgrade_vt {0}'.format(target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if not ret:
        ret = result()
    ret['comment'] += yellow('Upgrading lxc on {0}\n'.format(target))
    version = cli('cmd.run', 'lxc-info --version', salt_target=target)
    # run the install SLS which should take care of upgrading
    for step in [configure_install_lxc]:
        try:
            step(target, ret=ret, output=False)
        except FailedStepError:
            ret['result'] = False
            ret['comment'] += red('Failed to upgrade lxc\n')
            return ret
    # after upgrading
    nversion = cli('cmd.run', 'lxc-info --version', salt_target=target)
    if nversion != version:
        containers = cli('lxc.list', salt_target=target)
        reg = cli('mc_macros.update_local_registry', 'lxc_to_restart',
                  {'todo': containers.get('running', [])},
                  salt_target=target)
        ret['comment'] += red('Upgraded lxc\n')
    else:
        ret['comment'] += red('lxc was already at the last version\n')
    reg = cli('mc_macros.get_local_registry',
              'lxc_to_restart', salt_target=target)
    todo = reg.get('todo', [])
    done = []
    for lxc in todo:
        try:
            stopret = cli('lxc.stop', lxc, salt_target=target)
            if not stopret['result']:
                raise ValueError('wont stop')
            startret = cli('lxc.start', lxc, salt_target=target)
            if not startret['result']:
                raise ValueError('wont start')
            ret['comment'] += yellow('Rebooted {0}\n'.format(lxc))
            done.append(lxc)
        except Exception, ex:
            ret['result'] = False
            ret['comment'] += yellow(
                'lxc {0} failed to'
                ' reboot: {1}\n'.format(lxc, ex))
    cli('mc_macros.update_local_registry', 'lxc_to_restart',
        {'todo': [a for a in todo if a not in done]}, salt_target=target)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def sync_images(target, output=True, ret=None):
    '''sync images on target'''
    func_name = 'mc_cloud_lxc.sync_images {0}'.format(
        target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    iret = __salt__['mc_lxc.sync_images'](only=[target])
    if iret['result']:
        ret['comment'] += yellow(
            'LXC: images synchronnised on {0}\n'.format(target))
    else:
        merge_results(ret, iret)
        ret['comment'] += yellow(
            'LXC: images failed to synchronnise on {0}\n'.format(target))
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def install_vt(target, output=True):
    '''install & configure lxc'''
    func_name = 'mc_cloud_lxc.install_vt {0}'.format(
        target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    ret = result()
    ret['comment'] += yellow('Installing lxc on {0}\n'.format(target))
    for step in [configure_install_lxc, configure_images]:
        try:
            step(target, ret=ret, output=False)
        except FailedStepError:
            pass
    __salt__['mc_cloud_lxc.sync_images'](target, output=False, ret=ret)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def post_post_deploy_compute_node(target, output=True):
    '''post deployment hook for controller'''
    func_name = 'mc_cloud_lxc.post_post_deploy_compute_node {0}'.format(
        target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    ret = result()
    nodetypes_reg = cli('mc_nodetypes.registry')
    slss, pref = [], 'makina-states.cloud.lxc.compute_node'
    if nodetypes_reg['is']['devhost']:
        slss.append('{0}.devhost'.format(pref))
    if slss:
        ret =  __salt__['mc_api.apply_sls'](
            slss, **{'salt_target': target,
                     'ret': ret})
    msg = 'Post installation: {0}\n'
    if ret['result']:
        clr = green
        status = 'sucess'
    else:
        clr = red
        status = 'failure'
    ret['comment'] += clr(msg.format(status))
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def _vm_configure(what, target, compute_node, vm, ret, output):
    func_name = 'mc_cloud_lxc._vm_configure {0} {1} {2} {3}'.format(
        what, target, compute_node, vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'LXC: Installing {2} on vm '
        '{0}/{1}\n'.format(compute_node, vm, what))
    pref = 'makina-states.cloud.lxc.vm'
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(pref, what), **{
            'salt_target': target,
            'ret': ret})
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def _load_profile(compute_node, data, profile_data=None):
    if profile_data is None:
        profile_data = {
            'target': compute_node,
            'dnsservers': data.get("dnsservers", ["8.8.8.8", "4.4.4.4"]),
            'minion': {
                'master': data['master'],
                'master_port': data['master_port']}}
    for var in ["from_container", "snapshot", "image",
                "additional_ips",
                "bootstrap_shell",
                "gateway", "bridge", "mac", "lxc_conf_unset",
                "ssh_gateway", "ssh_gateway_user", "ssh_gateway_port",
                "ssh_gateway_key", "ip", "netmask",
                "size", "backing", "vgname", "script",
                "lvname", "script_args", "dnsserver",
                "ssh_username", "password", "lxc_conf"]:
        val = data.get(var)
        if val:
            if var in ['script_args']:
                if '--salt-cloud-dir' not in val:
                    val = '{0} {1}'.format(
                        val, '--salt-cloud-dir {0}')
            profile_data[var] = val
    return profile_data


def vm_spawn(vm,
             compute_node=None,
             vt='lxc',
             ret=None,
             output=True,
             force=False):
    '''spawn the vm

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_spawn foo.domain.tld

    '''
    func_name = 'mc_cloud_lxc.vm_spawn {0}'.format(vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if not ret:
        ret = result()
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    reg = cli('mc_macros.get_local_registry', 'mc_cloud_lxc_containers')
    provisioned_containers = reg.setdefault('provisioned_containers',
                                            OrderedDict())
    containers = provisioned_containers.setdefault(compute_node, [])
    pillar = __salt__['mc_cloud_vm.vm_sls_pillar'](compute_node, vm)
    data = pillar['vtVmData']
    cloudSettings = pillar['cloudSettings']
    profile_data = _load_profile(compute_node, data)
    marker = "{cloudSettings[prefix]}/pki/master/minions/{vm}".format(
        cloudSettings=cloudSettings, vm=vm)
    lret = cli('cmd.run_all', 'test -e {0}'.format(marker))
    lret['retcode'] = 1
    # verify if VM is already reachable if already marked as provisioned
    # this add a 10 seconds overhead upon VM creation
    # but enable us from crashing a vm that was loosed from local
    # registry and where reprovisionning can be harmful
    # As we are pinguing it, we are managing it, we will not
    # enforce spawning here !
    try:
        ping = False
        if vm in containers:
            ping = cli('test.ping', salt_timeout=10, salt_target=vm)
    except Exception:
        ping = False
    if force or (lret['retcode'] and not ping):
        try:
            # XXX: using the lxc runner which is now faster and nicer.
            cret = __salt__['mc_lxc_fork.cloud_init'](
                [vm], host=compute_node, **profile_data)
            if not cret['result']:
                # convert to regular dict for pformat
                errors = dict(cret.pop('errors', {}))
                hosts = {}
                for h in errors:
                    hosts[h] = dict(errors[h])
                cret['errors'] = hosts
                ret['trace'] += 'FAILURE ON LXC {0}:\n{1}\n'.format(
                    vm, pformat(dict(cret)))
                merge_results(ret, cret)
                ret['result'] = False
            else:
                ret['comment'] += '{0} provisioned\n'.format(vm)
        except Exception, ex:
            ret['trace'] += '{0}\n'.format(traceback.format_exc())
            ret['result'] = False
            ret['comment'] += red("{0}".format(ex))
    if ret['result']:
        containers.append(vm)
        reg = cli('mc_macros.update_local_registry',
                  'mc_cloud_lxc_containers', reg)
    if not ret['result'] and not ret['comment']:
        ret['comment'] = ('Failed to provision lxc {0},'
                          ' see {1}, see mastersalt-minion log').format(
                              vm, compute_node)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def vm_reconfigure(vm,
                   compute_node=None,
                   vt='lxc',
                   ret=None,
                   output=True,
                   force=False):
    '''
    Reconfigure the vm if neccessary

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_reconfigure_net foo.domain.tld

    '''
    func_name = 'mc_cloud_lxc.vm_spawn {0}'.format(vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if not ret:
        ret = result()
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    reg = cli('mc_macros.get_local_registry', 'mc_cloud_lxc_containers')
    provisioned_containers = reg.setdefault('provisioned_containers',
                                            OrderedDict())
    containers = provisioned_containers.setdefault(compute_node, [])
    pillar = __salt__['mc_cloud_vm.vm_sls_pillar'](compute_node, vm)
    data = pillar['vtVmData']
    cloudSettings = pillar['cloudSettings']
    profile_data = _load_profile(compute_node, data)
    marker = "{cloudSettings[prefix]}/pki/master/minions/{vm}".format(
        cloudSettings=cloudSettings, vm=vm)
    lret = cli('cmd.run_all', 'test -e {0}'.format(marker))
    lret['retcode'] = 1
    try:
        ping = False
        if vm in containers:
            ping = cli('test.ping', salt_timeout=10, salt_target=vm)
    except Exception:
        ping = False
    if force or (lret['retcode'] and not ping):
        try:
            kw = OrderedDict()
            # XXX: using the lxc runner which is now faster and nicer.
            args = cli('mc_lxc_fork.cloud_init_interface',
                       profile_data, salt_target=compute_node)
            for i in [
                'name',
                'cpu',
                'cpuset',
                'cpushare',
                'memory',
                'profile',
                'network_profile',
                'nic_opts',
                'bridge',
                'gateway',
                'autostart'
            ]:
                if i in args:
                    kw[i] = args[i]
            cret = cli('mc_lxc_fork.reconfigure',
                       kw, salt_target=compute_node)
            if not cret['result']:
                ret['trace'] += 'FAILURE ON LXC {0}:\n{1}\n'.format(
                    vm, pformat(dict(cret)))
                merge_results(ret, cret)
                ret['result'] = False
            else:
                ret['comment'] += '{0} reconfigured\n'.format(vm)
        except Exception, ex:
            ret['trace'] += '{0}\n'.format(traceback.format_exc())
            ret['result'] = False
            ret['comment'] += red("{0}".format(ex))
    if ret['result']:
        containers.append(vm)
        reg = cli('mc_macros.update_local_registry',
                  'mc_cloud_lxc_containers', reg)
    if not ret['result'] and not ret['comment']:
        ret['comment'] = ('Failed to reconfigure lxc {0},'
                          ' see {1} mastersalt-minion log').format(
                              vm, compute_node)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def vm_volumes(vm,
               compute_node=None,
               vt='lxc',
               ret=None,
               output=True,
               force=False):
    func_name = 'mc_cloud_lxc.vm_volumes {0}'.format(vm)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if not ret:
        ret = result()
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    content = "# generated by salt do not edit\n"
    vtdata = __salt__['mc_cloud_compute_node.cn_sls_pillar'](compute_node)['vmSettings'][vm]
    fstab = vtdata['vtVmData'].get('fstab', [])
    rmark = '/var/lib/lxc/{0}/restart_marker'.format(vm)
    if fstab:
        for i in fstab:
            content += i + '\n'
        cret = cli('mc_utils.manage_file',
                   name='/var/lib/lxc/{0}/fstab'.format(vm),
                   contents=content,
                   mode='750',
                   salt_target=compute_node)
        if not cret['result']:
            ret['result'] = False
            merge_results(ret, cret)
            ret['comment'] += red(
                'fstab error in updating for {0}\n'.format(vm))
        elif cret['changes']:
            cret = cli('file.touch', rmark, salt_target=compute_node)
            ret['comment'] += yellow(
                'fstab updated for {0}\n'.format(vm))
    cmd = ("lxc-stop -t 10 -n \"{0}\";"
           "lxc-start -d -n \"{0}\" &&"
           "rm -f \"{1}\"").format(vm, rmark)
    if ret['result'] and not cli(
        "cmd.retcode",
        "test -e \"{1}\" &&"
        "test \"x$(lxc-ls --fancy|grep RUNNING|"
        "awk '{{print $1}}'|egrep '^{0}$')\" = 'x{0}'".format(
            vm, rmark),
        salt_target=compute_node,
    ):
        # if container is running, restart it
        cret = cli('cmd.run_all', cmd, salt_target=compute_node)
        if cret['retcode']:
            ret['result'] = False
            merge_results(ret, cret)
            ret['comment'] += red(
                'Container {0} error while rebooting\n'.format(vm))
        else:
            ret['comment'] += yellow(
                'Container {0} rebooted\n'.format(vm))
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def vm_preprovision(vm, compute_node=None, vt='lxc', ret=None, output=True):
    '''install marker grains

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_grains foo.domain.tld

    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('preprovision', vm, compute_node, vm, ret, output)


def vm_grains(vm, compute_node=None, vt='lxc', ret=None, output=True):
    '''install marker grains

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_grains foo.domain.tld

    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('grains', vm, compute_node, vm, ret, output)


def vm_initial_setup(vm, compute_node=None, vt='lxc', ret=None, output=True):
    '''set initial password at least

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_initial_setup foo.domain.tld


    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('initial_setup', vm, compute_node, vm, ret, output)


def vm_hostsfile(vm, compute_node=None, vt='lxc', ret=None, output=True):
    '''manage vm /etc/hosts to add link to host

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_hostsfile foo.domain.tld

    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('hostsfile', vm, compute_node, vm, ret, output)
# vim:set et sts=4 ts=4 tw=80:
