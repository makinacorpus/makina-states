#!/usr/bin/env python
from __future__ import absolute_import, print_function

'''
.. _runner_mc_lxc:

mc_lxc
==========================



Jobs for lxc managment
'''
# -*- coding: utf-8 -*-

# Import python libs
import os
import logging
import traceback
import difflib

# Import salt libs
import salt.client
import salt.payload
import salt.utils
import salt.output
import salt.minion
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states import saltapi


six = saltapi.six
log = logging.getLogger(__name__)


def _noop(*a, **kw):
    return True


def master_opts(*args, **kwargs):
    if not kwargs:
        kwargs = {}
    kwargs.update({
        'cfgdir': __opts__.get('config_dir', None),
        'cfg': __opts__.get('conf_file', None),
    })
    return saltapi._master_opts(*args, **kwargs)


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def _errmsg(msg):
    raise saltapi.MessageError(msg)


def get_ver(origin):
    try:
        with open(os.path.join(origin, '.ms_version')) as fic:
            old_ver = int(fic.read())
    except Exception:
        old_ver = 0
    return old_ver


def test_same_versions(origin, destination, force=False):
    if force:
        return False
    old_ver = get_ver(origin)
    dold_ver = get_ver(destination)
    return dold_ver == old_ver


def get__salt__(__salt__from_exec=None):
    if __salt__from_exec is None:
        return __salt__
    try:
        for i in [
            'mc_api.time_log',
            'mc_api.get_cloud_controller_settings',
            'mc_api.get_image_settings'
        ]:
            __salt__from_exec[i]
    except KeyError:
        # from exec module (mock factorization hack)
        __salt__from_exec.update(
            {'mc_api.time_log': _noop,
             'mc_api.get_cloud_controller_settings': (
                 __salt__from_exec['mc_cloud_controller.settings']),
             'mc_api.get_image_settings': (
                 __salt__from_exec['mc_cloud_images.settings'])})
    return __salt__from_exec


def snapshot_container(cmd_runner, destination):
    cmd = ('if [ -e \'{0}/sbin/makinastates-snapshot.sh\' ];then'
           ' chroot \'{0}\' /sbin/makinastates-snapshot.sh;'
           'fi').format(destination)
    cret = cmd_runner(cmd)
    return cret


def get_cmd(_cmd_runner=None):
    if _cmd_runner is None:
        def _cmd_runner(cmd):
            return cli('cmd.run_all', cmd, python_shell=True)
    return _cmd_runner


def sync_container(origin, destination,
                   cmd_runner=None, ret=None,
                   __salt__from_exec=None,
                   snapshot=True,
                   force=False):
    _s = get__salt__(__salt__from_exec)
    if ret is None:
        ret = saltapi.result()
    cmd_runner = get_cmd(cmd_runner)

    fname = 'mc_lxc.sync_container'
    _s['mc_api.time_log'](
        'start', fname, origin, destination, force=force)
    if os.path.exists(origin) and os.path.exists(destination):
        if test_same_versions(origin, destination, force=force):
            return ret
        cmd = ('rsync -aA --exclude=lock --delete '
               '{0}/ {1}/').format(origin, destination)
        cret = cmd_runner(cmd)
        if cret['retcode']:
            ret['comment'] += (
                '\nRSYNC(local builder) failed {0} {1}'.format(
                    origin, destination))
            ret['result'] = False
            return ret
        if snapshot:
            cret = snapshot_container(cmd_runner, destination)
            if cret['retcode']:
                ret['comment'] += (
                    '\nRSYNC(local builder) reset failed {0}'.format(
                        destination))
                ret['result'] = False
    _s['mc_api.time_log']('end', fname, ret=ret)
    return ret


def clean_lxc_config(container, rootfs=None, fstab=None):
    if not rootfs:
        rootfs = '/var/lib/lxc/{0}/rootfs'.format(container)
    if not fstab:
        fstab = '/var/lib/lxc/{0}/fstab'.format(container)
    config = os.path.join(os.path.dirname(rootfs), 'config')
    if os.path.exists(config):
        lines = []
        ocontent = []
        with open(config) as fic:
            ocontent = fic.readlines()
            for i in ocontent:
                if 'lxc.utsname =' in i:
                    i = 'lxc.utsname = {0}\n'.format(container)
                if 'lxc.rootfs =' in i:
                    i = 'lxc.rootfs = {0}\n'.format(rootfs)
                if 'lxc.fstab =' in i:
                    i = 'lxc.fstab = {0}\n'.format(fstab)
                if (
                    ('lxc.network.hwaddr' in i) or
                    ('lxc.network.ipv4.gateway' in i) or
                    ('lxc.network.ipv4' in i) or
                    ('lxc.network.link' in i)
                ):
                    continue
                if i.strip():
                    lines.append(i)
        content = ''.join(lines)
        if (lines != ocontent) and content:
            log.info('Patching new cleaned'
                     ' lxc config: {0}'.format(config))
            log.info('Changes:')
            for line in difflib.unified_diff(ocontent, lines):
                log.info(line.strip())
            with open(config, 'w') as fic:
                fic.write(content)


def sync_image_reference_containers(imgSettings, ret, _cmd_runner=None,
                                    force=False, __salt__from_exec=None):
    _s = get__salt__(__salt__from_exec)
    fname = 'mc_lxc.sync_image_reference_containers'
    _s['mc_api.time_log']('start', fname)
    _cmd_runner = get_cmd(_cmd_runner)

    for img in imgSettings['lxc']['images']:
        imgs = imgSettings['lxc']['images'][img]
        bref = imgs['builder_ref']
        # try to find the local img reference building counterpart
        # and sync it back to the reference lxc
        rootfs = '/var/lib/lxc/{0}/rootfs'.format(img)
        if not os.path.exists(rootfs):
            lxccreate = _cmd_runner('lxc-create -t {1} -n {0}'.format(
                img, imgs.get('template', 'ubuntu')))
            if lxccreate['retcode'] != 0:
                ret['result'] = False
                ret['comment'] = (
                    'creation container for {0} failed'.format(img))
        sync_container('/var/lib/lxc/{0}/rootfs'.format(bref),
                       rootfs,
                       _cmd_runner, ret,
                       __salt__from_exec=__salt__from_exec,
                       force=force)
        clean_lxc_config(img)
        sync_container('/var/lib/lxc/{0}/rootfs'.format(bref),
                       '/var/lib/lxc/{0}.tmp/rootfs'.format(img),
                       _cmd_runner, ret,
                       __salt__from_exec=__salt__from_exec,
                       force=force)
    _s['mc_api.time_log']('end', fname, ret=ret)


def sync_images(only=None,
                force=False,
                output=True,
                force_output=False,
                __salt__from_exec=None):
    '''
    Sync the 'makina-states' image to all configured LXC hosts minions

    WARNING
        it checks .ms_version inside the rootfs of the LXC
        if this one didnt change, images wont be synced

    Configuration:

        :ref:`module_mc_lxc` settings:

            :images_root: master filesystem root to lxc containers
            :images: list of image to sync to lxc minions
            :containers: all minion targets will be synced
                         with that list of images
    '''
    fname = 'mc_lxc.sync_images'
    _s = get__salt__(__salt__from_exec)
    if not only:
        only = []
    if isinstance(only, basestring):
        only = only.split(',')
    ret = saltapi.result()
    ret['targets'] = OrderedDict()
    dest = '/root/.ssh/.lxc.pub'
    this_ = saltapi.get_local_target()
    orig = 'salt://.lxcsshkey.pub'
    imgSettings = _s['mc_api.get_cloud_images_settings']()
    controllersettings = _s['mc_api.get_cloud_controller_settings']()
    rsync_cmd = (
        'rsync -aA --delete-excluded --exclude="makina-states-lxc-*xz"'
        ' --numeric-ids '
    )
    sync_image_reference_containers(imgSettings, ret, force=force)
    root = master_opts()['file_roots']['base'][0]
    lxctargets = []
    for vm, vmdata in controllersettings['vms'].items():
        if (
            (vmdata['vt'] == 'lxc') and
            (vmdata['target'] not in lxctargets)
        ):
            lxctargets.append(vmdata['target'])
    for target in lxctargets:
        if only and (target not in only):
            continue
        # skip local minion :) (in fact no)
        # if this_ == target:
        #    continue
        subret = saltapi.result()
        ret['targets'][target] = subret
        try:
            host = cli('grains.item', 'fqdn', salt_target=target)
            if not host:
                host = target
            else:
                host = host['fqdn']
            # ssh known hosts
            cret = cli('ssh.set_known_host', 'root', host, salt_target=target)
            # ssh key
            pubkey = os.path.join(root, '.lxcsshkey.pub')
            with open('/root/.ssh/id_dsa.pub') as fic:
                with open(pubkey, 'w') as sshkey:
                    sshkey.write(fic.read())
            cret = cli('ssh.check_key_file', 'root', orig)
            if not cret[[a for a in cret][0]] in ['exists']:
                cret = cli('cp.get_file', orig, dest)
                cret = cli('ssh.set_auth_key_from_file',
                            'root', 'file://{0}'.format(dest))
                if cret not in ['new', 'no changes']:
                    _errmsg(
                        'Problem while accepting key {0}'.format(cret))
                cret = cli('ssh.check_key_file',
                            'root', orig, salt_target=target)
            if not cret[[a for a in cret][0]] in ['exists']:
                cret = cli('cp.get_file', orig, dest, salt_target=target)
                cret = cli('ssh.set_auth_key_from_file',
                            'root', 'file://{0}'.format(dest),
                            salt_target=target)
                if cret not in ['new', 'no changes']:
                    _errmsg(
                        'Problem while accepting key - dist {0}'.format(cret))
            # sync img to temp location
            for img in imgSettings['lxc']['images']:
                # transfert: 3h max
                timeout = 3 * 60 * 60
                imgroot = os.path.join(imgSettings['lxc']['images_root'], img)
                try:
                    if not os.path.exists(imgroot):
                        _errmsg(
                            '{0} does not exists'.format(img))
                    lver = get_ver(imgroot + '/rootfs')
                    cmd = (
                        'ps aux|egrep "rsync.*{0}"|grep -v grep|wc -l'
                    ).format(imgroot)
                    cret = cli('cmd.run_all', cmd, python_shell=True,
                               salt_timeout=timeout)
                    if cret['stdout'].strip() > '0':
                        _errmsg(
                            'Transfer already in progress')
                    o = imgroot + "/rootfs"
                    d = imgroot + '.tmp/rootfs'
                    if not test_same_versions(o, d, force=force):
                        cmd = (
                            'if [ -d {0} ];then '
                            '{1} {0}/ {0}.tmp/;'
                            'fi').format(imgroot, rsync_cmd)
                        cret = cli('cmd.run_all', cmd, python_shell=True,
                                   salt_target=target)
                        if not cret['retcode']:
                            subret['comment'] += (
                                '\n{0} RSYNC(local pre sync) complete'
                            ).format(target)
                            if cret['stdout'].strip():
                                subret['trace'] += (
                                    '\n{1} RSYNC:\n{0}\n'.format(
                                        cret['stdout'], target))
                    do_sync = True
                    try:
                        cmd = 'cat {0}.tmp/rootfs/.ms_version'.format(imgroot)
                        ver = int(cli('cmd.run', cmd, python_shell=True,
                                      salt_timeout=timeout, salt_target=host))
                        if lver == ver:
                            do_sync = False
                    except Exception:
                        pass
                    good = True
                    if do_sync:
                        cmd = (
                            '{2} -z '
                            '{0}/ root@{1}:{0}.tmp/'
                        ).format(imgroot, host, rsync_cmd)
                        cret = cli('cmd.run_all', cmd, python_shell=True,
                                   salt_timeout=timeout)
                        good = not cret['retcode']
                    if good:
                        subret['comment'] += (
                            '\n{0} RSYNC(net -> tmp) complete'
                        ).format(target)
                        if cret['stdout'].strip():
                            subret['trace'] += (
                                '\n{1} RSYNC:\n{0}\n'
                            ).format(cret['stdout'], target)
                        do_sync = True
                        try:
                            cmd = 'cat {0}/rootfs/.ms_version'.format(imgroot)
                            dver = int(cli('cmd.run', cmd, python_shell=True,
                                           salt_timeout=timeout,
                                           salt_target=host))
                            if dver == lver:
                                do_sync = False
                            else:
                                do_sync = True
                        except Exception:
                            pass
                        good = True
                        if do_sync:
                            # if transfert success sync tmp / img
                            # img to tmp location
                            cmd = (
                                '{1} {0}.tmp/ {0}/'
                            ).format(imgroot, rsync_cmd)
                            cret = cli('cmd.run_all', cmd, python_shell=True,
                                       salt_target=target)
                            good = not cret['retcode']
                        if good:
                            subret['comment'] += (
                                '\n{0} RSYNC(distant local sync) complete'
                            ).format(target)
                            if cret['stdout'].strip():
                                subret['trace'] += (
                                    '\n{1} RSYNC:\n{0}\n'
                                ).format(cret['stdout'], target)
                        else:
                            _errmsg(
                                'Failed to sync local image')
                    else:
                        _errmsg(
                            'Failed to sync single image')
                except saltapi.MessageError, ex:
                    subret['trace'] += '\n{0}'.format(ex)
                    subret['result'] = False
                    subret['comment'] += (
                        '\nWe failed to sync image for {0}: {1}'
                    ).format(target, imgroot)
        except saltapi.MessageError, ex:
            subret['trace'] += ''
            subret['result'] = False
            subret['comment'] += (
                '\nWe failed to sync image for {0}:\n{1}'.format(
                    target, ex))
        except Exception, ex:
            trace = traceback.format_exc()
            subret['trace'] += trace
            subret['result'] = False
            subret['comment'] += (
                '\nWe failed to sync image for {0}:\n{1}'.format(
                    target, ex))
    for target, subret in ret['targets'].items():
        if only and (target not in only):
            continue
        api.msplitstrip(subret)
        if not subret['result']:
            ret['result'] = False
    if ret['result']:
        ret['comment'] = 'We have successfully sync all targets\n'
    else:
        ret['comment'] = 'We have missed some target, see logs\n'
    api.msplitstrip(ret)
    # return mail error only on error
    if force_output or (output and not ret['result']):
        salt.output.display_output(ret, 'yaml', __opts__)
    _s['mc_api.time_log']('end', fname, ret=ret)
    return ret
#
