# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_lxc:

mc_cloud_lxc / lxc registry for compute nodes
===============================================



'''

# Import python libs
import os
import logging
import difflib
import traceback

from mc_states import saltapi
from salt.utils.odict import OrderedDict

# early in mcpillar, we dont have __salt__
from mc_states import api
from mc_states.grains.makina_grains import _is_lxc

_errmsg = saltapi._errmsg
__name = 'mc_cloud_lxc'

log = logging.getLogger(__name__)
VT = 'lxc'
PREFIX = 'makina-states.cloud.{0}'.format(VT)


def vt():
    return __salt__['mc_cloud_vm.vt'](VT)


def is_lxc():
    """
    Return true if we find a system or grain flag
    that explicitly shows us we are in a LXC context
    """
    return _is_lxc(_o=__opts__)


def vt_default_settings(cloudSettings, imgSettings):
    '''
    Default lxc container settings

        clone_from
            default image
        image
            LXC template to use
            'ubuntu'
        profile
            default profile to use. see saltstack definition
            of container profiles
        network_profile
            default net profile to use. see saltstack definition
            of container networking profiles
        bridge
            we install via states a bridge in 10.5/16 lxcbr1)
            'lxcbr1'
        backing
            (lvm, overlayfs, dir, brtfs) 'lvm'
        vgname
            'data'
        fstab
            list of fstab entries
        lvname
            'data'
        lxc_conf
            []
        lxc_conf_unset
            []
        vms
            List of containers ids classified by host ids::

                (Mapping of {hostid: [vmid]})

            The settings are not stored here for obvious performance reasons
    '''
    _s = __salt__
    clone_from = imgSettings['lxc']['default']
    backing = 'dir'
    if _s['mc_nodetypes.is_devhost']():
        backing = 'overlayfs'
    vmSettings = _s['mc_utils.dictupdate'](
        _s['mc_cloud_vm.vt_default_settings'](cloudSettings, imgSettings), {
            'vt': VT,
            'defaults': {
                'profile': {'clone_from': clone_from, 'backing': backing},
                'network_profile': {'eth0': {'link': 'lxcbr1'}},
                'gateway': '10.5.0.1',
                'netmask': '16',
                'network': '10.5.0.0',
                'netmask_full': '255.255.0.0',
                'fstab': None,
                'vgname': 'lxc',
                'lvname': None,
                'backing': backing,
                'volumes': [
                    # non implemented yet in any drivers
                    # {"name": "w", "kind": "host",
                    #  "source": "/o/t", "readOnly": True}
                ],
                'mounts': [
                    # {"volume": "w", "mountPoint": "/path/backup"}
                ],
                'lxc_conf': [],
                'lxc_conf_unset': []
            },
            'host_confs': {
                '/etc/apparmor.d/lxc/lxc-default': {'mode': 644},
                '/etc/default/lxc': {},
                '/etc/default/magicbridge_lxcbr1': {},
                # retrocompatible generation alias
                '/etc/default/lxc-net-makina': {
                    'source':
                    'salt://makina-states/files/etc/'
                    'default/magicbridge_lxcbr1'},
                '/etc/dnsmasq.lxcbr1/conf.d/makinastates_lxc': {},
                '/etc/dnsmasq.d/lxcbr1': {},
                '/etc/dnsmasq.d/lxcbr0': {},
                '/etc/reset-net-bridges': {},
                '/usr/bin/lxc-net-makina.sh': {
                    "mode": "755",
                    "template": False,
                    'source': (
                        'salt://makina-states/files/usr/bin/magicbridge.sh'
                    )
                },
                # '/usr/share/lxc/templates/lxc-ubuntu': {'template': None}
            }})
    return vmSettings


def vt_extpillar(target, data, *args, **kw):
    '''
    LXC extpillar
    '''
    return data


def vm_extpillar(vm, data, *args, **kw):
    '''
    Get per LXC container specific settings
    '''
    profile = data.setdefault('profile', OrderedDict())
    backing = profile.setdefault('backing', {})
    # dhcp now
    # data['network_profile']['eth0']['ipv4'] = data['ip']
    data['network_profile']['eth0']['hwaddr'] = data['mac']
    if data['profile'].get('clone_from') is not None:
        data.pop('image', None)
    if not data.get('fstab'):
        data['fstab'] = []
    shm = True
    for i in data['fstab']:
        if 'dev/shm' in i:
            shm = False
    if shm:
        data['fstab'].append('none dev/shm tmpfs rw,nosuid,nodev,create=dir')
    if ('overlayfs' in backing) or ('dir' in backing):
        for k in ['lvname', 'vgname', 'size']:
            if k in data:
                data.pop(k, None)
    return data


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


def snapshot_container(destination):
    cmd = ('if [ -e \'{0}/sbin/makinastates-snapshot.sh\' ];then'
           ' chroot \'{0}\' /sbin/makinastates-snapshot.sh;'
           'fi').format(destination)
    cret = __salt__['cmd.run_all'](cmd, python_shell=True)
    return cret


def sync_container(origin, destination,
                   ret=None,
                   snapshot=True,
                   force=False):
    _s = __salt__
    if ret is None:
        ret = saltapi.result()
    if os.path.exists(origin) and os.path.exists(destination):
        if test_same_versions(origin, destination, force=force):
            return ret
        cmd = ('rsync -aA --exclude=lock --delete '
               '{0}/ {1}/').format(origin, destination)
        cret = _s['cmd.run_all'](cmd)
        if cret['retcode']:
            ret['comment'] += (
                '\nRSYNC(local builder) failed {0} {1}'.format(
                    origin, destination))
            ret['result'] = False
            return ret
        if snapshot:
            cret = snapshot_container(destination)
            if cret['retcode']:
                ret['comment'] += (
                    '\nRSYNC(local builder) reset failed {0}'.format(
                        destination))
                ret['result'] = False
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


def sync_image_reference_containers(builder_ref, img, ret=None,
                                    template='ubuntu',
                                    force=False):
    _s = __salt__
    # try to find the local img reference building counterpart
    # and sync it back to the reference lxc
    if ret is None:
        ret = saltapi.result()
    rootfs = '/var/lib/lxc/{0}/rootfs'.format(img)
    if not os.path.exists(rootfs):
        lxccreate = _s['cmd.run_all'](
            'lxc-create -t {1} -n {0}'.format(img, template))
        if lxccreate['retcode'] != 0:
            ret['result'] = False
            ret['comment'] = (
                'creation container for {0} failed'.format(img))
    sync_container('/var/lib/lxc/{0}/rootfs'.format(builder_ref),
                   rootfs,
                   ret,
                   force=force)
    clean_lxc_config(img)
    return ret


def sync_images(images=None,
                lxctargets=None,
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
    _s = __salt__
    if not images:
        images = []
    if not lxctargets:
        lxctargets = []
    if isinstance(images, basestring):
        images = images.split(',')
    if isinstance(lxctargets, basestring):
        lxctargets = lxctargets.split(',')
    ret = saltapi.result()
    ret['targets'] = OrderedDict()
    rsync_cmd = (
        'rsync -aA --delete-excluded --exclude="makina-states-lxc-*xz"'
        ' --numeric-ids '
    )
    for target in lxctargets:
        subret = saltapi.result()
        ret['targets'][target] = subret
        try:
            # sync img to temp location
            for img in images:
                # transfert: 3h max
                imgroot = os.path.join('/var/lib/lxc', img)
                try:
                    if not os.path.exists(imgroot):
                        _errmsg('{0} does not exists'.format(img))
                    cmd = (
                        'ps aux|egrep "rsync.*{0}"|grep -v grep|wc -l'
                    ).format(imgroot)
                    cret = _s['cmd.run_all'](cmd, python_shell=True)
                    if cret['stdout'].strip() > '0':
                        _errmsg(
                            'Transfer already in progress')
                    cmd = '{2} -z {0}/ root@{1}:{0}/'.format(
                        imgroot, target, rsync_cmd)
                    cret = _s['cmd.run_all'](cmd, python_shell=True)
                    if not cret['retcode']:
                        subret['comment'] += (
                            '\n{0} RSYNC(net -> tmp) complete'
                        ).format(target)
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
        if images and (target not in images):
            continue
        api.msplitstrip(subret)
        if not subret['result']:
            ret['result'] = False
    if ret['result']:
        ret['comment'] = 'We have successfully sync all targets\n'
    else:
        ret['comment'] = 'We have missed some target, see logs\n'
    api.msplitstrip(ret)
    return ret
# vim:set et sts=4 ts=4 tw=80:
