#!/usr/bin/env python
'''

.. _runner_mc_cloud_docker:

mc_cloud_docker runner
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
VT = 'docker'


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def post_deploy_controller(output=True):
    '''
    Prepare cloud controller DOCKER configuration
    '''
    fname = 'mc_cloud_docker.post_deploy_controller'
    _s = __salt__
    _s['mc_api.time_log']('start', fname)
    ret = result()
    ret['comment'] = yellow('Installing controller docker configuration\n')
    p = 'makina-states.cloud.docker.controller'
    ret = _s['mc_api.apply_sls'](['{0}.postdeploy'.format(p)], **{'ret': ret})
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def cn_configure(what, target, ret=None, output=True):
    fname = 'mc_cloud_docker.cn_configure'
    _s = __salt__
    _s['mc_api.time_log']('start', fname, what, target)
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'DOCKER: Installing {1} on compute node {0}\n'.format(target, what))
    pref = 'makina-states.cloud.docker.compute_node'
    ret = _s['mc_api.apply_sls']('{0}.{1}'.format(pref, what),
                                 **{'salt_target': target, 'ret': ret})
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def configure_install_vt(target, ret=None, output=True):
    '''
    install docker
    '''
    return cn_configure('install_docker', target, ret=ret, output=output)


def configure_images(target, ret=None, output=True):
    '''
    configure all images templates
    '''
    return cn_configure('images', target, ret=ret, output=output)


def upgrade_vt(target, ret=None, output=True):
    '''
    Upgrade DOCKER hosts
    This will reboot all containers upon docker upgrade
    Containers are marked as being rebooted, and unmarked
    as soon as this script unmark explicitly them to be
    done.
    '''
    fname = 'mc_cloud_docker.upgrade_vt'
    __salt__['mc_api.time_log']('start', fname, target)
    if not ret:
        ret = result()
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', fname)
    return ret


def sync_images(target, output=True, ret=None):
    '''sync images on target'''
    fname = 'mc_cloud_docker.sync_images'
    __salt__['mc_api.time_log']('start', fname, target)
    if ret is None:
        ret = result()
    # iret = __salt__['mc_docker.sync_images'](only=[target])
    # if iret['result']:
    #     ret['comment'] += yellow(
    #         'DOCKER: images synchronnised on {0}\n'.format(target))
    # else:
    #     merge_results(ret, iret)
    #     ret['comment'] += yellow(
    #         'DOCKER: images failed to synchronnise on {0}\n'.format(target))
    # __salt__['mc_api.out'](ret, __opts__, output=output)
    # __salt__['mc_api.time_log']('end', fname)
    return ret


def install_vt(target, output=True):
    '''install & configure docker'''
    fname = 'mc_cloud_docker.install_vt'
    __salt__['mc_api.time_log']('start', fname, target)
    ret = result()
    ret['comment'] += yellow('Installing docker on {0}\n'.format(target))
    for step in [configure_install_vt, configure_images]:
        try:
            step(target, ret=ret, output=False)
        except FailedStepError:
            pass
    __salt__['mc_cloud_docker.sync_images'](target, output=False, ret=ret)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', fname)
    return ret


def post_post_deploy_compute_node(target, output=True):
    '''
    post deployment hook for controller
    '''
    fname = 'mc_cloud_docker.post_post_deploy_compute_node'
    __salt__['mc_api.time_log']('start', fname, target)
    ret = result()
    nodetypes_reg = cli('mc_nodetypes.registry')
    slss, pref = [], 'makina-states.cloud.docker.compute_node'
    if nodetypes_reg['is']['devhost']:
        slss.append('{0}.devhost'.format(pref))
    if slss:
        ret = __salt__['mc_api.apply_sls'](
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
    fname = 'mc_cloud_docker.vm_configure'
    _s = __salt__
    _s['mc_api.time_log']('start', fname, what, vm)
    vm_data = _s['mc_api.get_vm'](vm)
    cn = vm_data['target']
    if ret is None:
        ret = result()
    ret['comment'] += yellow('DOCKER: Installing {2} on vm'
                             ' {0}/{1}\n'.format(cn, vm, what))
    p = 'makina-states.cloud.docker.vm'
    ret = _s['mc_api.apply_sls']('{0}.{1}'.format(p, what),
                                 **{'salt_target': vm, 'ret': ret})
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def _load_profile(data, profile_data=None):
    if profile_data is None:
        profile_data = {'target': data['target'],
                        'dnsservers': data.get("dnsservers",
                                               ["8.8.8.8", "4.4.4.4"]),
                        'minion': {'master': data['master'],
                                   'master_port': data['master_port']}}
    for var in ["clone_from", "snapshot", "image",
                "additional_ips",
                "bootstrap_shell",
                "gateway", "bridge", "mac", "docker_conf_unset",
                "ssh_gateway", "ssh_gateway_user", "ssh_gateway_port",
                "ssh_gateway_key", "ip", "netmask",
                "size", "backing", "vgname", "script",
                "lvname", "script_args", "dnsserver",
                "ssh_username", "password", "docker_conf"]:
        val = data.get(var)
        if val:
            if var in ['script_args']:
                if '--reattach-dir' not in val:
                    val = '{0} {1}'.format(
                        val, '--reattach-dir {0}')
            profile_data[var] = val
    return profile_data


def vm_spawn(vm, ret=None, output=True, force=False):
    '''spawn the vm

    ::

        salt-run -lall mc_cloud_docker.vm_spawn foo.domain.tld

    '''
    _s = __salt__
    fname = 'mc_cloud_docker.vm_spawn'
    _s['mc_api.time_log']('start', fname, vm)
    if not ret:
        ret = result()
    data = _s['mc_api.get_vm'](vm)
    cn = data['target']
    lreg = 'mc_cloud_docker_containers'
    reg = cli('mc_macros.get_local_registry', lreg)
    provisioned_containers = reg.setdefault('provisioned_containers',
                                            OrderedDict())
    containers = provisioned_containers.setdefault(cn, [])
    cloudSettings = _s['mc_api.get_cloud_settings'](vm)
    pdt = _load_profile(data)
    marker = "{cloudSettings[prefix]}/pki/master/minions/{vm}".format(
        cloudSettings=cloudSettings, vm=vm)
    lret = cli('cmd.run_all', 'test -e {0}'.format(marker), python_shell=True)
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
            # XXX: using the docker runner which is now faster and nicer.
            _s['mc_api.time_log']('start', 'docker_vm_init',  vm, cn)
            cret = _s['docker.cloud_init']([vm], host=cn, **pdt)
            _s['mc_api.time_log']('end', 'docker_vm_end',  vm=vm)
            if not cret['result']:
                # convert to regular dict for pformat
                errors = dict(cret.pop('errors', {}))
                hosts = {}
                for h in errors:
                    hosts[h] = dict(errors[h])
                cret['errors'] = hosts
                ret['trace'] += 'FAILURE ON DOCKER {0}:\n{1}\n'.format(
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
        reg = cli('mc_macros.update_local_registry', lreg, reg)
    if not ret['result'] and not ret['comment']:
        ret['comment'] = ('Failed to provision docker {0},'
                          ' see {1}, see salt-minion log').format(vm, cn)
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def vm_reconfigure(vm, ret=None, output=True, force=False):
    '''
    Reconfigure the vm if neccessary

    ::

        salt-run -lall mc_cloud_docker.vm_reconfigure_net foo.domain.tld

    '''
    fname = 'mc_cloud_docker.vm_spawn'
    _s = __salt__
    _s['mc_api.time_log']('start', fname, vm)
    if not ret:
        ret = result()
    # data = _s['mc_api.get_vm'](vm)
    # cs = _s['mc_api.get_cloud_settings'](vm)
    # cn = data['target']
    # reg = cli('mc_macros.get_local_registry', 'mc_cloud_docker_containers')
    # provisioned_containers = reg.setdefault('provisioned_containers',
    #                                         OrderedDict())
    # containers = provisioned_containers.setdefault(cn, [])
    # pdt = _load_profile(data)
    # marker = "{cs[prefix]}/pki/master/minions/{vm}".format(cs=cs, vm=vm)
    # lret = cli('cmd.run_all', 'test -e {0}'.format(marker), python_shell=True)
    # lret['retcode'] = 1
    # try:
    #     raise
    #     ping = False
    #     if vm in containers:
    #         ping = cli('test.ping', salt_timeout=10, salt_target=vm)
    # except Exception:
    #     ping = False
    # if force or (lret['retcode'] and not ping):
    #     try:
    #         kw = OrderedDict()
    #         # XXX: using the docker runner which is now faster and nicer.
    #         args = cli(
    #             'docker.cloud_init_interface',
    #             vm, pdt, salt_target=cn)
    #         for i in [
    #             'cpu',
    #             'cpuset',
    #             'cpushare',
    #             'memory',
    #             'profile',
    #             'network_profile',
    #             'nic_opts',
    #             'bridge',
    #             'gateway',
    #             'autostart'
    #         ]:
    #             if i == 'memory' and not i:
    #                 continue
    #             if i in args:
    #                 kw[i] = args[i]
    #         _s['mc_api.time_log']('start', 'docker_vm_init',  vm, cn)
    #         kw['salt_target'] = cn
    #         cret = cli('docker.reconfigure', vm, **kw)
    #         _s['mc_api.time_log']('end', 'docker_vm_end',  vm=vm)
    #         if not cret['result']:
    #             ret['trace'] += 'FAILURE ON DOCKER {0}:\n{1}\n'.format(
    #                 vm, pformat(dict(cret)))
    #             merge_results(ret, cret)
    #             ret['result'] = False
    #         else:
    #             ret['comment'] += '{0} reconfigured\n'.format(vm)
    #     except Exception, ex:
    #         ret['trace'] += '{0}\n'.format(traceback.format_exc())
    #         ret['result'] = False
    #         ret['comment'] += red("{0}".format(ex))
    # if ret['result']:
    #     containers.append(vm)
    #     reg = cli('mc_macros.update_local_registry',
    #               'mc_cloud_docker_containers', reg)
    # if not ret['result'] and not ret['comment']:
    #     ret['comment'] = ('Failed to reconfigure docker {0},'
    #                       ' see {1} salt-minion log').format(vm, cn)
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def vm_volumes(vm, ret=None, output=True, force=False):
    fname = 'mc_cloud_docker.vm_volumes'
    _s = __salt__
    _s['mc_api.time_log']('start', fname, vm)
    if not ret:
        ret = result()
    return ret


def vm_initial_setup(vm, ret=None, output=True):
    '''
    set initial password at least

    ::

        salt-run -lall mc_cloud_docker.vm_initial_setup foo.domain.tld


    '''
    return vm_configure('initial_setup', vm, ret=ret, output=output)


def vm_hostsfile(vm, ret=None, output=True):
    '''
    manage vm /etc/hosts to add link to host

    ::

        salt-run -lall mc_cloud_docker.vm_hostsfile foo.domain.tld

    '''
    return vm_configure('hostsfile', vm, ret=ret, output=output)


def vm_preprovision(vm, ret=None, output=True):
    '''
    Shortcut to run all preprovision steps like initial_setup or hostfiles

    ::

        salt-run -lall mc_cloud_docker.vm_grains foo.domain.tld

    '''
    return vm_configure('preprovision', vm, ret=ret, output=output)


# def remove(vm, destroy=False, only_stop=False, **kwargs):
#     '''
#     Remove a container
#     '''
#     _s = __salt__
#     vm_data = _s['mc_api.get_vm'](vm)
#     tgt = vm_data['target']
#     ret = None
#     if destroy:
#         if cli('test.ping', salt_target=tgt):
#             if not cli('docker.exists', vm, salt_target=tgt):
#                 return True
#             if 'running' == cli('docker.state', vm, salt_target=tgt):
#                 ret = cli('docker.stop', vm, salt_target=tgt)
#                 if ret:
#                     log.info('{0}/{1} stopped'.format(tgt, vm))
#             ret = cli('docker.reconfigure', vm,
#                       autostart=False, salt_target=tgt)
#             if not only_stop:
#                 ret = cli('docker.destroy', vm, salt_target=tgt)['result']
#                 if ret:
#                     log.info('{0}/{1} destroyed'.format(tgt, vm))
#     return ret
# 
# 
# def destroy(vm, **kwargs):
#     '''
#     Alias to remove
#     '''
#     return remove(vm, **kwargs)

# vim:set et sts=4 ts=4 tw=80:
