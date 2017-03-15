# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_kvm:

mc_cloud_kvm / kvm registry for compute nodes
===============================================



'''

# Import python libs
import logging
import mc_states.api

from mc_states import saltapi
from salt.utils.odict import OrderedDict

_errmsg = saltapi._errmsg
__name = 'mc_cloud_kvm'

log = logging.getLogger(__name__)
VT = 'kvm'
PREFIX = 'makina-states.cloud.{0}'.format(VT)


def vt():
    return __salt__['mc_cloud_vm.vt'](VT)


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


def vt_default_settings(cloudSettings, imgSettings):
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
        _s['mc_cloud_vm.vt_default_settings'](cloudSettings, imgSettings), {
            'vt': VT,
            'defaults': {'gateway': '10.6.0.1',
                         'network': '10.6.0.0',
                         'bridge': 'kvmbr1',
                         'profile': 'medium'}})
    return vmSettings


def vt_extpillar(target, data, **kw):
    '''
    KVM extpillar
    '''
    return data


def vm_extpillar(vm, data, *args, **kw):
    '''
    Get per KVM specific settings
    '''
    return data
# vim:set et sts=4 ts=4 tw=80:
