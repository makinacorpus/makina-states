# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_kvm:

mc_cloud_kvm / kvm registry for compute nodes
===============================================

'''
__docformat__ = 'restructuredtext en'

# Import python libs
import logging
import mc_states.utils

from mc_states import saltapi
from salt.utils.odict import OrderedDict

_errmsg = saltapi._errmsg
__name = 'mc_cloud_kvm'

log = logging.getLogger(__name__)
MAC_GID = 'makina-states.cloud.kvm.vmsettings.{0}.{1}.mac'
PW_GID = 'makina-states.cloud.kvm.vmsettings.{0}.{1}.password'
IP_GID = 'makina-states.cloud.kvm.vmsettings.{0}.{1}.ip'
VT = 'kvm'
PREFIX = 'makina-states.cloud.{0}'.format(VT)


def vt():
    return VT


def is_kvm():
    """
    in case of a container, we have the container name in cgroups
    else, it is equal to /

    in kvm:

        model name : QEMU Virtual CPU version 0.9.1

    """

    try:
        with open('/proc/cpuinfo') as fic:
            kvm = 'qemu virtual' in fic.read().lower()
    except Exception:
        kvm = False
    return kvm


def default_settings():
    '''
    Default KVM vm settings

        image
            KVM template to use
        backing
            (lvm)
        storage_pools
            pool defs (only lvm is supported for now)
    '''
    _s = __salt__
    vmSettings = _s['mc_utils.dictupdate'](
        _s['mc_cloud_vm.default_settings'](), {
            'defaults': {
                'gateway': '10.6.0.1',
                'network': '10.6.0.0',
                'bridge': 'kvmbr1',
                'profile': 'medium',
                'pools': {'vg': {'type': 'lvm'}},
            },
        }
    )
    return vmSettings


def settings():
    '''
    KVM registry
    '''
    _s = __salt__
    cloudSettings = _s['mc_cloud.settings']()
    id_ = __grains__['id']
    # any additionnal VT specific settings
    additionnal_defaults = {}
    vtSettings = _s['mc_utils.defaults'](
        PREFIX,
        _s['mc_cloud_vm.mangle_default_settings'](
            id_,
            cloudSettings,
            default_settings,
            additionnal_defaults=additionnal_defaults))
    # do not store in cached
    # registry the whole conf, memory would explode
    try:
        vms = vtSettings.pop('vms')
    except:
        vms = OrderedDict()
    vtSettings['vms'] = vm_ids = OrderedDict()
    for i in vtSettings:
        if i.startswith('vms.'):
            del vtSettings[i]
    for target in [a for a in vms]:
        vm_ids.setdefault(target, [])
        data = vms[target]
        if data is None:
            vms[target] = []
            continue
        for vmname in data:
            vm_ids[target].append(vmname)
    return vtSettings


def get_settings_for_vm(target, vm, vmSettings=None, cloudSettings=None, **kw):
    '''
    Get per KVM vm specific settings

    '''
    _s = __salt__
    _g = __grains__
    vm_data = _s['mc_pillar.get_global_clouf_conf'](
        'cloud_vm_attrs', vm)
    if vmSettings is None:
        vmSettings = settings()
    if cloudSettings is None:
        cloudSettings = _s['mc_cloud.settings']()
    vm_defaults = {'pools': None}
    vm_data = _s['mc_cloud_vm.default_settings_for_vm'](
        target, VT, vm, cloudSettings, vmSettings, vm_defaults, vm_data
    )
    if ('overlayfs' in vm_data['backing']) or ('dir' in vm_data['backing']):
        for k in ['lvname', 'vgname', 'size']:
            if k in vm_data:
                del vm_data[k]
    return vm_data


def vm_extpillar(vm, target, vmSettings=None, cloudSettings=None, **kw):
    '''
    Get specific settings for a vm
    '''
    return {'{0}.vms.{1}'.format(PREFIX, vm): get_settings_for_vm(
        vm, target, cloudSettings=cloudSettings, vmSettings=vmSettings, **kw)}


def ext_pillar(id_, *args, **kw):
    '''
    KVM extpillar
    '''
    _s = __salt__
    # any additionnal VT specific settings
    additionnal_defaults = {}
    return _s['mc_cloud_vm.vt_extpillar'](
        id_, PREFIX, VT, default_settings,  vm_extpillar,
        additionnal_defaults=additionnal_defaults)
# vim:set et sts=4 ts=4 tw=80:
