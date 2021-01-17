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
from distutils.version import LooseVersion


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
    _g = __grains__
    clone_from = imgSettings['lxc']['default']
    backing = 'dir'
    # if _s['mc_nodetypes.is_devhost']():
    #     backing = 'overlayfs'
    pkgs = ['lxc-templates', 'lxc', 'python3-lxc',
            'liblxc1', 'lxcfs', 'dnsmasq']
    if _s['mc_utils.loose_version'](_g.get('osrelease', '')) < _s['mc_utils.loose_version']('20.04'):
        pkgs.append('cgmanager')
    # package exists but is currently broken
    # if (
    #     __grains__['os'] in ['Ubuntu'] and
    #     LooseVersion(__grains__['osrelease']) >= '15.10'
    # ):
    #     for p in ['cgmanager']:
    #         if p not in pkgs:
    #             continue
    #         pkgs.pop(pkgs.index(p))
    vmSettings = _s['mc_utils.dictupdate'](
        _s['mc_cloud_vm.vt_default_settings'](cloudSettings, imgSettings), {
            'vt': VT,
            'defaults': {
                'profile': {'clone_from': clone_from, 'backing': backing},
                'network_profile': {'eth0': {'link': 'lxcbr1'}},
                'gateway': '10.5.0.1',
                'netmask': '16',
                'network': '10.5.0.0',
                'proc_mode': 'rw',
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
            'pkgs': pkgs,
            'host_confs': {
                '/etc/apparmor.d/lxc/lxc-default': {'mode': 644},
                '/etc/default/lxc': {},
                '/etc/default/magicbridge_lxcbr1': {},
                # retrocompatible generation alias
                '/etc/default/lxc-net-makina': {
                    'source':
                    'salt://makina-states/files/etc/'
                    'default/lxc-net-makina'},
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


def clean_lxc_config(container, rootfs=None, fstab=None, start=True):
    if not rootfs:
        rootfs = '/var/lib/lxc/{0}/rootfs'.format(container)
    if not fstab:
        fstab = '/var/lib/lxc/{0}/fstab'.format(container)
    config = os.path.join(os.path.dirname(rootfs), 'config')
    if os.path.exists(config):
        lines = []
        ocontent = []
        has_start = False
        with open(config) as fic:
            ocontent = fic.readlines()
            for i in ocontent:
                if 'lxc.start.auto =' in i:
                    has_start = True
                    i = 'lxc.start.auto = {0}\n'.format(start and '1' or '0')
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
        if not has_start:
            lines.append('lxc.start.auto = 0')
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
                                    snapshot=True,
                                    force=False):
    '''
    Sapshot container (copy to img & impersonate)
    '''
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
                   snapshot=snapshot,
                   force=force)
    clean_lxc_config(img, start=False)
    return ret
# vim:set et sts=4 ts=4 tw=80:
