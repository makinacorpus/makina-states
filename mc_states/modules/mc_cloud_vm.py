#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_vm:

mc_cloud_vm / vm registry for compute nodes
===============================================

'''
__docformat__ = 'restructuredtext en'

# Import python libs
import logging
import mc_states.utils
import os
import copy


from mc_states import saltapi
from salt.utils.odict import OrderedDict
from mc_states.utils import memoize_cache

__name = 'mc_cloud_vm'

log = logging.getLogger(__name__)
PREFIX = 'makina-states.cloud.vms'


def default_settings():
    '''
    VM default settings
    This may be needed to be database backended in the future.
    As well, we may need iterator loops inside jinja templates
    to not eat that much memory loading large datasets.

    makina-states.services.cloud.lxc
        The settings of lxc containers that are meaningful on the
        cloud controller

    cloud defaults (makina-states.services.cloud.lxc)
        defaults settings to provision lxc containers
        Those are all redefinable at each container level

        LXC API:

        mode
            (salt (default) or mastersalt)

        ssh_gateway
            ssh gateway info
        ssh_gateway_port
            ssh gateway info
        ssh_gateway_user
            ssh gateway info
        ssh_gateway_key
            ssh gateway info
        size
            default filesystem size for container on lvm
            None
        gateway
            10.5.0.1
        master
            master to uplink the container to
            None
        master_port
            '4506'
        image
            LXC template to use
            'ubuntu'
        network
            '10.5.0.0'
        netmask
            '16'
        netmask_full
            '255.255.0.0'
        autostart
            lxc is autostarted
        bridge
            we install via states a bridge in 10.5/16 lxcbr1)
            'lxcbr1'
        sudo
            True
        use_bridge
            True
        users
            ['root', 'sysadmin']
        ssh_username
            'ubuntu'
        vgname
            'data'
        lvname
            'data'

    vms
        List of containers ids classified by host ids::

            (Mapping of {hostid: [vmid]})

        The settings are not stored here for obvious performance reasons
    '''
    _s = __salt__
    cloudSettings = _s['mc_cloud.default_settings']()
    vmSettings = {
        'dnsservers': ['8.8.8.8', '4.4.4.4'],
        'defaults': {
            #
            'image': 'ubuntu',
            'default_snapshot': _s['mc_nodetypes.is_devhost'](),
            'autostart': True,
            #
            'gateway': '127.0.0.1',
            'use_bridge': True,
            'main_bridge': 'br0',
            'netmask': '16',
            'network': '10.3.0.0',
            'netmask_full': '255.255.0.0',
            'bridge': 'br0',
            'additional_ips': [],
            'domains': [__grains__['id']],
            #
            'ssh_gateway': cloudSettings['ssh_gateway'],
            'ssh_username': 'ubuntu',
            'ssh_gateway_password': cloudSettings[
                'ssh_gateway_password'],
            'ssh_gateway_user': cloudSettings['ssh_gateway_user'],
            'ssh_gateway_key': cloudSettings['ssh_gateway_key'],
            'ssh_gateway_port': cloudSettings['ssh_gateway_port'],
            #
            'master': cloudSettings['master'],
            'mode': cloudSettings['mode'],
            'master_port': cloudSettings['master_port'],
            'bootsalt_branch': cloudSettings['bootsalt_branch'],
            #
            'sudo': True,
            'users': ['root', 'sysadmin'],
            #
            'size': None,  # via profile
            'backing': 'lvm',
        },
        'vms': OrderedDict(),
    }
    return vmSettings


def vm_default_settings(target,
                        vt,
                        vm,
                        cloudSettings,
                        vmSettings,
                        vm_defaults,
                        vm_data):

    '''
    Get per VM specific settings
     All the defaults defaults registry settings are redinable here +
    This is for the moment the only backend of corpus cloud infra.
    If you want to implement another backend, mimic the dictionnary
    for this method and also settings.

        Corpus API

        ip
            do not set it, or use at ure own risk, prefer just to read the
            value. This is the main ip (private network)
        aditonnal_ips
            additionnal ips which will be wired on the main bridge (br0)
            which is connected to internet.
            Be aware that you may use manual virtual mac addresses
            providen by you provider (online, ovh).
            This is a list of mappings {ip: '', mac: '',netmask:''}
            eg::

                makina-states.cloud.lxc.vms.<target>.<name>.additionnal_ips:
                  - {'mac': '00:16:3e:01:29:40',
                     'gateway': None, (default)
                     'link': 'br0', (default)
                     'netmask': '32', (default)
                     'ip': '22.1.4.25'}
        domains
            list of domains tied with this host (first is minion id
            and main domain name, it is automaticly added)
    '''
    _g = __grains__
    _s = __salt__

    def _sort_domains(dom):
        if dom == vm:
            return '0{0}'.format(dom)
        else:
            return '1{0}'.format(dom)

    vm_defaults = vmSettings.get('defaults', {})
    master = vm_defaults['master']
    # if it is not a distant minion, use private gateway ip
    if _g['id'] == target:
        master = vm_defaults['gateway']
    data = {
        'mac': _s[
            'mc_cloud_compute_node.find_mac_for_vm'
        ](vm, default=vm_data.get('mac', None)),
        'name': vm,
        'domains': [vm],
        'password': _s[
            'mc_cloud_compute_node.find_password_for_vm'
        ](vm, default=_s['mc_pillar.get_passwords'](vm)['clear']['root']),
        'master': master,
        'master_port': None,
        'autostart': None,
        'size': None,
        'bootsalt_shell': cloudSettings['bootsalt_shell'],
        'bootsalt_branch': None,
        'script': cloudSettings['script'],
        'script_args': cloudSettings['bootsalt_mastersalt_args'],
        'snapshot': None,
        'image': None,
        'main_bridge': None,
        'ip': None,
        'additional_ips': None,
        'bridge': None,
        'network': None,
        'netmask': None,
        'dnsservers': None,
        'ssh_gateway': None,
        'ssh_gateway_password': None,
        'ssh_gateway_user': None,
        'ssh_gateway_key': None,
        'ssh_gateway_port': None,
        'gateway': target,
        'ssh_username': None,
        'users': None,
        'mode': None,
        'vgname': None,
        'backing': None,
        'sudo': None,
        'ssh_reverse_proxy_port': _s[
            'cloud_compute_node.get_ssh_port'](
                vm=vm, target=target),
        'snmp_reverse_proxy_port': _s[
            'mc_cloud_compute_node.get_snmp_port'](
                vm=vm, target=target)
    }
    for i, val in _s['mc_utils.dictupdate'](
        data, vm_defaults
    ).items():
        if val is None:
            val = vmSettings.get(i, vm_defaults.get(i, None))
        vm_data.setdefault(i, val)
    vm_data = saltapi.complete_gateway(vm_data, vmSettings)
    if vm not in vm_data['domains']:
        vm_data['domains'].insert(0, vm)
    vm_data['domains'].sort(key=_sort_domains)
    if (
        '-b' not in vm_data['script_args']
        or '--branch' not in vm_data['script_args']
    ):
        vm_data['script_args'] += ' -b {0}'.format(
            vm_data['bootsalt_branch'])
    # at this stage, only get already allocated ips
    vm_data['ip'] = _s['mc_cloud_compute_node.find_ip_for_vm'](
        target, vm,
        virt_type=vt,
        network=vm_data['network'],
        netmask=vm_data['netmask'],
        default=vm_data.get('ip'))
    for ix, ipinfos in enumerate(vm_data['additional_ips']):
        k = '{0}_{1}_{2}_aip_fo'.format(target, vm, ix)
        mac = ipinfos.setdefault('mac', None)
        if not mac:
            mac = _s['mc_cloud_compute_node.get_conf_for_vm'](
                vm, k, default=mac)
        if not mac:
            _s['mc_cloud_compute_node.set_conf_for_vm'](
                vm, k, _s['mc_cloud_compute_node.gen_mac']())
        ipinfos['mac'] = mac
        ipinfos.setdefault('gateway', None)
        if ipinfos['gateway']:
            vm_data['gateway'] = None
        ipinfos.setdefault('netmask', '32')
        ipinfos.setdefault('link', 'br0')
    return vm_data


def overridable_default_settings(id_, cloudSettings):
    if id_ is None:
        id_ = __grains__['id']
    default_snapshot = False
    if _s['mc_nodetypes.is_devhost']():
        default_snapshot = True
    data = {'defaults': {'snapshot': default_snapshot,
                         'mode': cloudSettings['mode'],
                         'ssh_gateway': cloudSettings['ssh_gateway'],
                         'ssh_gateway_password': cloudSettings[
                             'ssh_gateway_password'],
                         'ssh_gateway_user': cloudSettings['ssh_gateway_user'],
                         'ssh_gateway_key': cloudSettings['ssh_gateway_key'],
                         'ssh_gateway_port': cloudSettings['ssh_gateway_port'],
                         'master': cloudSettings['master'],
                         'master_port': cloudSettings['master_port'],
                         'domains': [id_],
                         'bootsalt_branch': cloudSettings['bootsalt_branch']}}
    return data


def mangle_default_settings(id_,
                            cloudSettings,
                            defaults_fun,
                            extdata=None,
                            additionnal_defaults=None):
    _s = __salt__
    if not additionnal_defaults:
        additionnal_defaults = {}
    if not extdata:
        extdata = None
    data = _s['mc_utils.dictupdate'](
        _s['mc_utils.dictupdate'](
            _s[defaults_fun],
            _s['mc_utils.dictupdate'](
                _s['mc_cloud_vm.overridable_default_settings'](
                    id_, cloudSettings), additionnal_defaults
            )
        ), extdata)
    return data


def vt_extpillar_settings(id_, vt,
                          default_settings_fun=None,
                          additionnal_defaults=None):
    _s = __salt__
    if not default_settings_fun:
        default_settings_fun = _s['mc_cloud_{0}.default_settings'.format(vt)]
    if not additionnal_defaults:
        additionnal_defaults = {}
    extdata = _s['mc_pillar.get_global_clouf_conf'](vt)
    cloudSettings = _s['mc_cloud.extpillar_settings']()
    vtSettings = _s['mc_cloud_vm.mangle_default_settings'](
        id_,
        cloudSettings,
        default_settings_fun,
        extdata=extdata,
        additionnal_defaults=additionnal_defaults)
    return vtSettings


def vt_extpillar(id_,
                 prefix,
                 vt,
                 default_settings_fun=None,
                 vm_extpillar_fun=None,
                 additionnal_defaults=None):
    _s = __salt__
    if not vm_extpillar_fun:
        vm_extpillar_fun = _s['mc_cloud_{0}.vm_extpillar'.format(vt)]
    cloudSettings = _s['mc_cloud.extpillar_settings']()
    vtSettings = vt_extpillar_settings(
        id_, vt, default_settings_fun=default_settings_fun)
    return {prefix: data}


def extpillar_for(vm, vt):
    return __salt__['mc_cloud_{0}.ext_pillar'.format(vt)](vm)


def extpillar(id_, *args, **kw):
    _s = __salt__
    data = OrderedDict()
    conf = _s['mc_pillar.get_configuration'](id_)
    vm_ids = vtSettings.setdefault('vms', OrderedDict())
    vms = all_vms = _s['mc_cloud_compute_node.get_all_vms']()
    targets = _s['mc_cloud_compute_node.get_all_targets']()
    virt_types = []
    if id_ not in targets and id_ not in vms:
        return {}
    if id_ in vms:
        vt = vms[id_]['virt_type']
        if vt not in virt_types:
            virt_types.append(vt)
    if id_ in targets:
        vms = targets[id_]['vms']
        [virt_types.append(i) for i in targets[id_]['virt_types']
         if i not in virt_types]
    for vt in virt_types:
        data['makina-states.cloud.{0}'.format(vt)] = {}
    for vm, vmdata in vms.items():
        vmextdata = extpillar_for(vm, vt)
        vt = vmdata['vt']
        data['{0}.{1}'.format(PREFIX, vt)] = vm_pillar_fun(
            id_, vt_vms[id_],
            cloudSettings=cloudSettings,
            default_settings=vtSettings)

'''
Methods usable
After the pillar has loaded, on the compute node itself
'''


def settings(vt, additionnal_defaults=None):
    _s = __salt__
    if additionnal_defaults is None:
        additionnal_defaults = {}
    cloudSettings = _s['mc_cloud.settings']()
    mod = 'mc_cloud_{0}'.format(vt)
    default_settings_fun = '{0}.default_settings'.format(mod)
    prefix = 'makina-states.cloud.{0}'.format(vt)
    data = _s['mc_utils.defaults'](prefix, _s[default_settings_fun]())
    vtSettings = _s['mc_utils.defaults'](
        prefix,
        _s['mc_cloud_vm.mangle_default_settings'](
            __grains__['id'],
            cloudSettings,
            default_settings,
            additionnal_defaults=additionnal_defaults))
    return vtSettings
# vim:set et sts=4 ts=4 tw=81:
