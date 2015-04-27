# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_lxc:

mc_cloud_lxc / lxc registry for compute nodes
===============================================



'''

# Import python libs
import os
import logging
import copy
import mc_states.api

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

        from_container
            default image
        image
            LXC template to use
            'ubuntu'
        profile
            default size profile to use (medium) (apply only to lvm)
        profile_type
            default profile type to use (lvm)

                lvm
                    lvm backend from default container
                lvm-scratch
                    lvm backend from default lxc template
                dir
                    dir backend from default container
                dir-scratch
                    dir backend from default lxc template

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
    from_container = [a for a in imgSettings['lxc']['images']][0]
    dptype = 'dir'
    backing = 'dir'
    if _s['mc_nodetypes.is_devhost']():
        backing = dptype = 'overlayfs'
    vmSettings = _s['mc_utils.dictupdate'](
        _s['mc_cloud_vm.vt_default_settings'](cloudSettings, imgSettings), {
            'vt': VT,
            'defaults': {'from_container': from_container,
                         'profile': 'medium',
                         'profile_type': dptype,
                         #
                         'gateway': '10.5.0.1',
                         'network': '10.5.0.0',
                         'bridge': 'lxcbr1',
                         #
                         'backing': backing,
                         'vgname': 'lxc',
                         'lvname': None,
                         #
                         #
                         'fstab': None,
                         'lxc_conf': [],
                         'lxc_conf_unset': []},
            'host_confs': {
                '/etc/apparmor.d/lxc/lxc-default': {'mode': 644},
                '/etc/default/lxc': {},
                '/etc/default/lxc-net-makina': {},
                '/etc/dnsmasq.d/lxc': {},
                '/etc/reset-net-bridges': {},
                '/usr/bin/lxc-net-makina.sh': {},
                '/usr/share/lxc/templates/lxc-ubuntu': {'template': None},
            },
            'lxc_cloud_profiles': {
                'xxxtrem': {'size': '2000g'},
                'xxtrem': {'size': '1000g'},
                'xtrem': {'size': '500g'},
                'xxxlarge': {'size': '100g'},
                'xxlarge': {'size': '50g'},
                'large': {'size': '20g'},
                'medium': {'size': '10g'},
                'small': {'size': '5g'},
                'xsmall': {'size': '3g'},
                'xxsmall': {'size': '1g'},
                'xxxsmall': {'size': '500m'}}})
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
    backing = data.setdefault('backing', 'dir')
    if data['from_container'] is not None:
        data.pop('image', None)
    if ('overlayfs' in backing) or ('dir' in backing):
        for k in ['lvname', 'vgname', 'size']:
            if k in data:
                data.pop(k, None)
    return data
# vim:set et sts=4 ts=4 tw=80:
