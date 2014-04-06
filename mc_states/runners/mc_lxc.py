#!/usr/bin/env python

'''
.. _runner_mc_lxc:

Jobs for lxc managment
==========================
'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import python libs
import os
import traceback

# Import salt libs
import salt.client
import salt.payload
import salt.utils
import salt.output
import salt.minion
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states import saltapi


def master_opts(*args, **kwargs):
    if not kwargs:
        kwargs = {}
    kwargs.update({
        'cfgdir': __opts__.get('config_dir', None),
        'cfg': __opts__.get('conf_file', None),
    })
    return saltapi._master_opts(*args, **kwargs)


def _cli(*args, **kwargs):
    if not kwargs:
        kwargs = {}
    kwargs.update({
        'salt_cfgdir': __opts__.get('config_dir', None),
        '__opts__': __opts__,
        'salt_cfg': __opts__.get('conf_file', None),
    })
    return saltapi.client(*args, **kwargs)


def _errmsg(msg):
    raise saltapi.MessageError(msg)


def sync_container(cmd_runner, ret, origin, destination):
    if os.path.exists(origin) and os.path.exists(destination):
        cmd = 'rsync -aA --delete {0}/ {1}/'.format(origin, destination)
        cret = cmd_runner(cmd)
        if cret['retcode']:
            ret['comment'] += (
                '\nRSYNC(local builder) failed {0} {1}'.format(
                    origin, destination))
            ret['result'] = False
            return ret
        cmd = 'chroot {0} /sbin/lxc-snap.sh'.format(destination)
        cret = cmd_runner(cmd)
        if cret['retcode']:
            ret['comment'] += (
                '\nRSYNC(local builder) reset failed {0}'.format(
                    destination))
            ret['result'] = False
    return ret


def sync_image_reference_containers(imgSettings, ret, _cmd_runner=None):
    if _cmd_runner is None:
        def _cmd_runner(cmd):
            return _cli('cmd.run_all', cmd)

    for img in imgSettings['lxc']['images']:
        bref = imgSettings['lxc']['images'][img]['builder_ref']
        # try to find the local img reference building counterpart
        # and sync it back to the reference lxc
        sync_container(_cmd_runner, ret,
                       '/var/lib/lxc/{0}/rootfs'.format(bref),
                       '/var/lib/lxc/{0}/rootfs'.format(img))


def sync_images(output=True):
    '''
    Sync the 'makina-states' image to all configured LXC hosts minions

    Configuration:

        :ref:`module_mc_lxc` settings:

            :images_root: master filesystem root to lxc containers
            :images: list of image to sync to lxc minions
            :containers: all minion targets will be synced with that list of images
    '''
    ret = saltapi.result()
    ret['targets'] = OrderedDict()
    dest = '/root/.ssh/.lxc.pub'
    this_ = saltapi.get_local_target()
    orig = 'salt://.lxcsshkey.pub'
    imgSettings = _cli('mc_cloud_images.settings')
    lxcSettings = _cli('mc_cloud_lxc.settings')
    rsync_cmd = (
        'rsync -aA --delete-excluded --exclude="makina-states-lxc-*xz"'
        ' --numeric-ids '
    )

    sync_image_reference_containers(imgSettings, ret)
    root = master_opts()['file_roots']['base'][0]
    for target in lxcSettings.get('vms', {}):
        # skip local minion :) (in fact no)
        # if this_ == target:
        #    continue
        subret = saltapi.result()
        ret['targets'][target] = subret
        try:
            host = _cli('grains.item', 'fqdn', salt_target=target)
            if not host:
                host = target
            else:
                host = host['fqdn']
            # ssh known hosts
            cret = _cli('ssh.set_known_host', 'root', host, salt_target=target)
            # ssh key
            pubkey = os.path.join(root, '.lxcsshkey.pub')

            with open('/root/.ssh/id_dsa.pub') as fic:
                with open(pubkey, 'w') as sshkey:
                    sshkey.write(fic.read())
            cret = _cli('ssh.check_key_file', 'root', orig)
            if not cret[[a for a in cret][0]] in ['exists']:
                cret = _cli('cp.get_file', orig, dest)
                cret = _cli('ssh.set_auth_key_from_file',
                            'root', 'file://{0}'.format(dest))
                if cret not in ['new', 'no changes']:
                    _errmsg(
                        'Problem while accepting key {0}'.format(cret))
                cret = _cli('ssh.check_key_file',
                            'root', orig, salt_target=target)
            if not cret[[a for a in cret][0]] in ['exists']:
                cret = _cli('cp.get_file', orig, dest, salt_target=target)
                cret = _cli('ssh.set_auth_key_from_file',
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
                    cmd = (
                        'ps aux|egrep "rsync.*{0}"|grep -v grep|wc -l'
                    ).format(imgroot)
                    cret = _cli('cmd.run_all', cmd, salt_timeout=timeout)
                    if cret['stdout'].strip() > '0':
                        _errmsg(
                            'Transfer already in progress')
                    cmd = (
                        'if [ -d {0} ];then '
                        '{1} {0}/ {0}.tmp/;'
                        'fi').format(imgroot, rsync_cmd)
                    cret = _cli('cmd.run_all', cmd, salt_target=target)
                    if not cret['retcode']:
                        subret['comment'] += '\nRSYNC(local pre sync) complete'
                        subret['trace'] += (
                            '\nRSYNC:\n{0}\n'.format(cret['stdout']))
                    cmd = (
                        '{2} -z '
                        '{0}/ root@{1}:{0}.tmp/'
                    ).format(imgroot, host, rsync_cmd)
                    cret = _cli('cmd.run_all', cmd, salt_timeout=timeout)
                    if not cret['retcode']:
                        subret['comment'] += '\nRSYNC(net) complete'
                        subret['trace'] += (
                            '\nRSYNC:\n{0}\n'.format(cret['stdout']))
                        # if transfert success sync tmp / img
                        # img to tmp location
                        cmd = (
                            '{1} {0}.tmp/ {0}/'
                        ).format(imgroot, rsync_cmd)
                        cret = _cli('cmd.run_all', cmd, salt_target=target)
                        if not cret['retcode']:
                            subret['comment'] += '\nRSYNC(local sync) complete'
                            subret['trace'] += (
                                '\nRSYNC:\n{0}\n'.format(cret['stdout']))
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
        api.msplitstrip(subret)
        if not subret['result']:
            ret['result'] = False
    ret['result'] = False
    if ret['result']:
        ret['comment'] = 'We have sucessfully sync all targets'
    else:
        ret['comment'] = 'We have missed some target, see logs'
    api.msplitstrip(ret)
    # return mail error only on error
    if output and not ret['result']:
        salt.output.display_output(ret, 'yaml', __opts__)
    return ret
#
