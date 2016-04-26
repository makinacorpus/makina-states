#!/usr/bin/env python
'''

.. _runner_mc_cloud_lxc:

mc_cloud_lxc runner
==========================



'''
# -*- coding: utf-8 -*-

# Import python libs
import logging
from pprint import pformat
import traceback

# Import salt libs
import salt.client
import salt.payload
import salt.utils
import time
import salt.output
import salt.minion
from salt.utils.odict import OrderedDict

from mc_states.saltapi import (
    LXC_IMPLEMENTATION,
    merge_results,
    result,
    check_point,
    SaltExit,
    green, red, yellow,
    SaltCopyError,
    FailedStepError,
)

log = logging.getLogger(__name__)
VT = 'lxc'


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def post_deploy_controller(output=True):
    '''
    Prepare cloud controller LXC configuration
    '''
    fname = 'mc_cloud_lxc.post_deploy_controller'
    _s = __salt__
    _s['mc_api.time_log']('start', fname)
    ret = result()
    ret['comment'] = yellow('Installing controller lxc configuration\n')
    p = 'makina-states.cloud.lxc.controller'
    ret = _s['mc_api.apply_sls'](['{0}.postdeploy'.format(p)], **{'ret': ret})
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def cn_configure(what, target, ret=None, output=True):
    fname = 'mc_cloud_lxc.cn_configure'
    _s = __salt__
    _s['mc_api.time_log']('start', fname, what, target)
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'LXC: Installing {1} on compute node {0}\n'.format(target, what))
    pref = 'makina-states.cloud.lxc.compute_node'
    ret = _s['mc_api.apply_sls']('{0}.{1}'.format(pref, what),
                                 **{'salt_target': target, 'ret': ret})
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def configure_install_vt(target, ret=None, output=True):
    '''
    install lxc
    '''
    return cn_configure('install_lxc', target, ret=ret, output=output)


def configure_images(target, ret=None, output=True):
    '''
    configure all images templates
    '''
    return cn_configure('images', target, ret=ret, output=output)


def upgrade_vt(target, ret=None, output=True):
    '''
    Upgrade LXC hosts
    This will reboot all containers upon lxc upgrade
    Containers are marked as being rebooted, and unmarked
    as soon as this script unmark explicitly them to be
    done.
    '''
    fname = 'mc_cloud_lxc.upgrade_vt'
    __salt__['mc_api.time_log']('start', fname, target)
    if not ret:
        ret = result()
    ret['comment'] += yellow('Upgrading lxc on {0}\n'.format(target))
    version = cli('cmd.run', 'lxc-info --version', python_shell=True,
                  salt_target=target)
    # run the install SLS which should take care of upgrading
    for step in [configure_install_vt]:
        try:
            step(target, ret=ret, output=False)
        except FailedStepError:
            ret['result'] = False
            ret['comment'] += red('Failed to upgrade lxc\n')
            return ret
    # after upgrading
    nversion = cli('cmd.run', 'lxc-info --version', python_shell=True,
                   salt_target=target)
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
    __salt__['mc_api.time_log']('end', fname)
    return ret


def sync_images(target, output=True, ret=None):
    '''sync images on target'''
    fname = 'mc_cloud_lxc.sync_images'
    __salt__['mc_api.time_log']('start', fname, target)
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
    __salt__['mc_api.time_log']('end', fname)
    return ret


def install_vt(target, output=True):
    '''install & configure lxc'''
    fname = 'mc_cloud_lxc.install_vt'
    __salt__['mc_api.time_log']('start', fname, target)
    ret = result()
    ret['comment'] += yellow('Installing lxc on {0}\n'.format(target))
    for step in [configure_install_vt, configure_images]:
        try:
            step(target, ret=ret, output=False)
        except FailedStepError:
            pass
    __salt__['mc_cloud_lxc.sync_images'](target, output=False, ret=ret)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', fname)
    return ret


def post_post_deploy_compute_node(target, output=True):
    '''
    post deployment hook for controller
    '''
    fname = 'mc_cloud_lxc.post_post_deploy_compute_node'
    __salt__['mc_api.time_log']('start', fname, target)
    ret = result()
    nodetypes_reg = cli('mc_nodetypes.registry')
    slss, pref = [], 'makina-states.cloud.lxc.compute_node'
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
    fname = 'mc_cloud_lxc.vm_configure'
    _s = __salt__
    _s['mc_api.time_log']('start', fname, what, vm)
    vm_data = _s['mc_api.get_vm'](vm)
    cn = vm_data['target']
    if ret is None:
        ret = result()
    ret['comment'] += yellow('LXC: Installing {2} on vm'
                             ' {0}/{1}\n'.format(cn, vm, what))
    p = 'makina-states.cloud.lxc.vm'
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
    for var in [
        'profile', 'network_profile',
        "dnsservers", "password",
        "bootstrap_shell", "script", "script_args",
        "additional_ips",
        "from_container",  # old, but too toochy to support only
                           # the migrated place
        # migrated to lxc profiles
        # "size", "backing", "vgname",
        # "gateway", "bridge", "mac", "lxc_conf_unset",
        # "ssh_gateway", "ssh_gateway_user", "ssh_gateway_port",
        # "clone_from", "snapshot", "image", "lvname",
        # "ssh_gateway_key", "ip", "netmask", "ssh_username", "lxc_conf"
    ]:
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

        salt-run -lall mc_cloud_lxc.vm_spawn foo.domain.tld

    '''
    _s = __salt__
    fname = 'mc_cloud_lxc.vm_spawn'
    _s['mc_api.time_log']('start', fname, vm)
    if not ret:
        ret = result()
    data = _s['mc_api.get_vm'](vm)
    cn = data['target']
    lreg = 'mc_cloud_lxc_containers'
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
            # XXX: using the lxc runner which is now faster and nicer.
            _s['mc_api.time_log']('start', 'lxc_vm_init',  vm, cn)
            cret = _s[LXC_IMPLEMENTATION + '.cloud_init']([vm], host=cn, **pdt)
            _s['mc_api.time_log']('end', 'lxc_vm_end',  vm=vm)
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
        reg = cli('mc_macros.update_local_registry', lreg, reg)
    if not ret['result'] and not ret['comment']:
        ret['comment'] = ('Failed to provision lxc {0},'
                          ' see {1}, see salt-minion log').format(vm, cn)
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def vm_reconfigure(vm,
                   ret=None,
                   output=True,
                   rootfs=None,
                   force=False):
    '''
    Reconfigure the vm if neccessary

    ::

        salt-run -lall mc_cloud_lxc.vm_reconfigure_net foo.domain.tld

    '''
    fname = 'mc_cloud_lxc.vm_spawn'
    _s = __salt__
    _s['mc_api.time_log']('start', fname, vm)
    if not ret:
        ret = result()
    data = _s['mc_api.get_vm'](vm)
    cs = _s['mc_api.get_cloud_settings'](vm)
    cn = data['target']
    reg = cli('mc_macros.get_local_registry', 'mc_cloud_lxc_containers')
    provisioned_containers = reg.setdefault('provisioned_containers',
                                            OrderedDict())
    containers = provisioned_containers.setdefault(cn, [])
    pdt = _load_profile(data)
    marker = "{cs[prefix]}/pki/master/minions/{vm}".format(cs=cs, vm=vm)
    lret = cli('cmd.run_all', 'test -e {0}'.format(marker), python_shell=True)
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
            args = cli(
                LXC_IMPLEMENTATION + '.cloud_init_interface',
                vm, pdt, salt_target=cn)
            kw['utsname'] = vm
            kw['rootfs'] = (rootfs or
                            '{0}/{1}/rootfs'.format(
                                '/var/lib/lxc', vm))
            for i in [
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
                if i == 'memory' and not i:
                    continue
                if i in args:
                    kw[i] = args[i]
            _s['mc_api.time_log']('start', 'lxc_vm_init',  vm, cn)
            kw['salt_target'] = cn
            cret = cli(LXC_IMPLEMENTATION + '.reconfigure', vm, **kw)
            _s['mc_api.time_log']('end', 'lxc_vm_end',  vm=vm)
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
                          ' see {1} salt-minion log').format(vm, cn)
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def vm_volumes(vm, ret=None, output=True, force=False):
    fname = 'mc_cloud_lxc.vm_volumes'
    _s = __salt__
    _s['mc_api.time_log']('start', fname, vm)
    if not ret:
        ret = result()
    vm_data = _s['mc_api.get_vm'](vm)
    cn = vm_data['target']
    content = "# generated by salt do not edit\n"
    fstab = vm_data['fstab']
    rmark = '/var/lib/lxc/{0}/restart_marker'.format(vm)
    if fstab:
        for i in fstab:
            content += i + '\n'
        cret = cli('mc_utils.manage_file',
                   name='/var/lib/lxc/{0}/fstab'.format(vm),
                   contents=content, mode='750', salt_target=cn)
        if not cret['result']:
            ret['result'] = False
            merge_results(ret, cret)
            ret['comment'] += red('fstab update error for {0}\n'.format(vm))
        elif cret['changes']:
            cret = cli('file.touch', rmark, salt_target=cn)
            ret['comment'] += yellow('fstab updated for {0}\n'.format(vm))
    cmd = ("lxc-stop -t 10 -n \"{0}\";lxc-start -d -n \"{0}\""
           "&& rm -f \"{1}\"").format(vm, rmark)
    if ret['result'] and not cli(
        "cmd.retcode",
        "test -e \"{1}\" &&"
        "test \"x$(lxc-ls --fancy|grep RUNNING|"
        "awk '{{print $1}}'|egrep '^{0}$')\" = 'x{0}'".format(
            vm, rmark), python_shell=True, salt_target=cn
    ):
        # if container is running, restart it
        cret = cli('cmd.run_all', cmd, use_vt=True,
                   python_shell=True, salt_target=cn)
        if cret['retcode']:
            ret['result'] = False
            merge_results(ret, cret)
            ret['comment'] += red(
                'Container {0} error while rebooting\n'.format(vm))
        else:
            ret['comment'] += yellow('Container {0} rebooted\n'.format(vm))
    _s['mc_api.out'](ret, __opts__, output=output)
    _s['mc_api.time_log']('end', fname)
    return ret


def vm_initial_setup(vm, ret=None, output=True):
    '''
    set initial password at least

    ::

        salt-run -lall mc_cloud_lxc.vm_initial_setup foo.domain.tld


    '''
    return vm_configure('initial_setup', vm, ret=ret, output=output)


def vm_hostsfile(vm, ret=None, output=True):
    '''
    manage vm /etc/hosts to add link to host

    ::

        salt-run -lall mc_cloud_lxc.vm_hostsfile foo.domain.tld

    '''
    return vm_configure('hostsfile', vm, ret=ret, output=output)


def vm_preprovision(vm, ret=None, output=True):
    '''
    Shortcut to run all preprovision steps like initial_setup or hostfiles

    ::

        salt-run -lall mc_cloud_lxc.vm_grains foo.domain.tld

    '''
    return vm_configure('preprovision', vm, ret=ret, output=output)


def remove(vm, destroy=False, only_stop=False, **kwargs):
    '''
    Remove a container
    '''
    _s = __salt__
    vm_data = _s['mc_api.get_vm'](vm)
    tgt = vm_data['target']
    ret = None
    if destroy:
        if cli('test.ping', salt_target=tgt):
            if not cli('lxc.exists', vm, salt_target=tgt):
                return True
            if 'running' == cli('lxc.state', vm, salt_target=tgt):
                ret = cli(LXC_IMPLEMENTATION + '.stop', vm, salt_target=tgt)
                if ret:
                    log.info('{0}/{1} stopped'.format(tgt, vm))
            ret = cli(LXC_IMPLEMENTATION + '.reconfigure', vm,
                      autostart=False, salt_target=tgt)
            if not only_stop:
                ret = cli(LXC_IMPLEMENTATION + '.destroy', vm,
                          salt_target=tgt)['result']
                if ret:
                    log.info('{0}/{1} destroyed'.format(tgt, vm))
    return ret


RESET_TEMPLATE = '''




'''


class MoveError(Exception):
    '''.'''


def copy(destination,
         origin,
         controller=True,
         sync=True,
         reset=True,
         cn_config=True,
         lxc_config=None,
         cn_wire=None,
         stop_old=False,
         reset_files=None,
         reset_salt=None,
         reset_ssh=None,
         reset_postfix=None,
         output=True,
         reboot=True,
         autoaccept=True,
         timeout=60,
         ret=None):
    _s = __salt__
    fname = 'mc_cloud_lxc.move'
    _s['mc_api.time_log']('start', fname, origin, destination)
    if not ret:
        ret = result()
    if reset_salt is None:
        reset_salt = reset
    if reset_files is None:
        reset_files = reset
    if reset_ssh is None:
        reset_ssh = reset
    if reset_postfix is None:
        reset_postfix = reset
    if cn_wire is None:
        cn_wire = cn_config
    if lxc_config is None:
        lxc_config = cn_config
    vm_data = _s['mc_api.get_vm'](destination)
    old_vm_data = _s['mc_api.get_vm'](origin)
    p = 'makina-states.cloud.lxc.controller'
    cn = vm_data['target']
    old_cn = old_vm_data['target']
    if controller:
        _s['mc_api.time_log']('controller', fname, origin, destination)
        scret = _s['mc_api.apply_sls'](
            ['{0}.postdeploy'.format(p)], **{'ret': ret})
        check_point(scret, __opts__, output=output)
        ret['controller'] = scret
    if sync:
        _s['mc_api.time_log']('sync', fname, origin, destination)
        sshkey = cli('cmd.run', 'cat /root/.ssh/id_rsa.pub', salt_target=cn)
        sshkeyp = sshkey.split()
        status = cli('ssh.check_key', user='root', enc=sshkeyp[0],
                     key=sshkeyp[1], comment=sshkeyp[2], options=[],
                     salt_target=old_cn)
        nstatus = 'no change'
        try:
            if status == 'add':
                nstatus = cli('ssh.set_auth_key', user='root', enc=sshkeyp[0],
                              key=sshkeyp[1], comment=sshkeyp[2], options=[],
                              salt_target=old_cn)
                if nstatus not in ['new', 'no change']:
                    raise MoveError(
                        'SSH KEY WONT ADD: {0} {1} {2}'
                        ''.format(old_cn, sshkey, status))
            ret['rsync'] = cli('cmd.run_all',
                               'rsync -aAz --delete'
                               ' {0}:/var/lib/lxc/{1}/'
                               '     /var/lib/lxc/{2}/'
                               ''.format(old_cn, origin, destination),
                               salt_target=cn)
            if ret['rsync']['retcode']:
                ret['result'] = False
            check_point(ret, __opts__, output=output)
        finally:
            if nstatus != 'new':
                status = cli('ssh.rm_auth_key', user='root',
                             key=sshkeyp[1], salt_target=old_cn)
    if cn_config:
        if lxc_config:
            _s['mc_api.time_log']('lxc_config', fname, origin, destination)
            cret = vm_reconfigure(destination, force=True)
            check_point(cret, __opts__, output=output)
            ret['lxc_config'] = cret
        if reset_files or reset_salt or reset_ssh:
            _s['mc_api.time_log']('reset', fname, origin, destination)
            cmd = ('chroot /var/lib/lxc/{destination}/rootfs'
                   ' python /tmp/reset-host.py'
                   ' --destination="{destination}" --origin="{origin}"'
                   '').format(origin=origin, destination=destination)
            if reset_postfix:
                cmd += ' --reset-postfix'
            if reset_files:
                cmd += ' --reset-files'
            if reset_ssh:
                cmd += ' --reset-ssh'
            if reset_salt:
                cmd += ' --reset-salt'
            cret = cli(
                'cp.get_file',
                'salt://makina-states/files/usr/bin/reset-name.py',
                '/var/lib/lxc/{0}/rootfs/tmp/reset-name.py'
                ''.format(destination),
                salt_target=cn)
            ret['rename'] = cli('cmd.run_all', cmd, salt_target=cn)
            if ret['rename']['retcode']:
                ret['result'] = False
            check_point(ret, __opts__, output=output)
        if cn_wire:
            _s['mc_api.time_log']('cn_wire', fname, origin, destination)
            for sls in [
                'makina-states.cloud.generic.compute_node.host',
                'makina-states.services.virt.lxc'
            ]:
                cret = _s['mc_api.apply_sls'](sls, salt_target=cn)
                check_point(cret, __opts__, output=output)
                ret['cn_{0}'.format(sls)] = cret
        if reboot:
            _s['mc_api.time_log']('lxc_reboot', fname, origin, destination)
            ret['stop'] = cli('lxc.state', destination, salt_target=cn)
            if ret['stop'].lower() == 'running':
                ret['stop'] = cli('lxc.stop', destination,
                                  kill=True, salt_target=cn)
                ret['stop'] = cli('lxc.state', destination, salt_target=cn)
            if ret['stop'].lower() == 'running':
                ret['result'] = False
            else:
                ret['start'] = cli('lxc.start', destination, salt_target=cn)
                ret['start'] = cli('lxc.state', destination, salt_target=cn)
                if ret['start'].lower() != 'running':
                    ret['result'] = False
    if (
        ret['result'] and autoaccept and
        'running' == cli('lxc.state', destination, salt_target=cn)
    ):
        now = time.time()
        found = False
        while (not found) and time.time() < now + timeout:
            if not cli(
                'cmd.run_all',
                'test -e'
                ' /etc/salt/pki/master'
                '/minions_pre/{0}'.format(destination)
            )['retcode']:
                found = True
        if not found:
            raise Exception('Key challenge failed')
        else:
            ret['challenge'] = cli(
                'cmd.run_all',
                'salt-key -y -a {0}'.format(destination))
            if ret['challenge']['retcode']:
                ret['result'] = False
            check_point(ret, __opts__, output=output)
    if ret['result'] and stop_old:
        ret['old_reconfig'] = cli(
            'lxc.reconfigure', origin, autostart=False, salt_target=old_cn)
        if 'running' == cli('lxc.state', origin, salt_target=old_cn):
            ret['old_stop'] = cli(
                'lxc.stop', origin, kill=True, salt_target=old_cn)
    _s['mc_api.time_log']('end', fname, origin, destination)
    return ret


def move(*args, **kwargs):
    kwargs['stop_old'] = True
    return copy(*args, **kwargs)


def destroy(vm, **kwargs):
    '''
    Alias to remove
    '''
    return remove(vm, **kwargs)

# vim:set et sts=4 ts=4 tw=80:
