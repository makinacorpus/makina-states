# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_lxc:

mc_cloud_lxc / lxc registry for compute nodes
===============================================



'''

# Import python libs
import logging

from mc_states import saltapi
from salt.utils.odict import OrderedDict

# early in mcpillar, we dont have __salt__
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
    return _is_lxc()


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
# vim:set et sts=4 ts=4 tw=80:
