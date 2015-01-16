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

def is_devhost():
    is_devhost = os.path.exists('/root/vagrant/provision_settings.sh')
    default_snapshot = False
    if is_devhost:
        default_snapshot = True
    return is_devhost


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
            'default_snapshot': _s['mc_cloud_vm.is_devhost'](),
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


def vm_settings(suf='', ttl=60):
    '''
    VM cloud related settings
    THIS IS USED ON THE VM SIDE !
    '''
    def _do(suf):
        reg = __salt__['mc_macros.get_local_registry'](
            'cloud_vm_settings{0}'.format(suf),
            registry_format='pack')
        if 'vmSettings' not in reg:
            raise ValueError(
                'Registry not yet configured {0}'.format(
                    suf))
        return reg
    cache_key = 'mc_cloud_vm.vm_settings{0}'.format(suf)
    return memoize_cache(_do, [suf], {}, cache_key, ttl)


def settings(suf='', ttl=60):
    '''
    Alias to vm_settings
    '''
    return vm_settings(suf=suf, ttl=ttl)


def default_settings_for_vm(target,
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
        ](target, vt, vm, default=vm_data.get('mac', None)),
        'name': vm,
        'domains': [vm],
        'password': _s[
            'mc_cloud_compute_node.find_password_for_vm'
        ](target, vt, vm,
          default=_s['mc_pillar.get_passwords'](vm)['clear']['root']),
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
                target, vt, vm, k, default=mac)
        if not mac:
            _s['mc_cloud_compute_node.set_conf_for_vm'](
                target, vt, vm,
                k, _s['mc_cloud_compute_node.gen_mac']())
        ipinfos['mac'] = mac
        ipinfos.setdefault('gateway', None)
        if ipinfos['gateway']:
            vm_data['gateway'] = None
        ipinfos.setdefault('netmask', '32')
        ipinfos.setdefault('link', 'br0')
    return vm_data


def expose_pillar(id_, vt, vm_pillar_fun, vtSettings, cloudSettings):
    _s = __salt__
    conf = _s['mc_pillar.get_configuration'](id_)
    vm_ids = vtSettings.setdefault('vms', OrderedDict())
    non_managed_hosts = _s['mc_pillar.query']('non_managed_hosts')
    data = OrderedDict()
    for i in vtSettings:
        if i.startswith('vms.'):
            del vtSettings[i]
    vms = _s[
        'mc_cloud_compute_node.get_cloud_vms_conf'
    ]().get(vt, {})
    vt_vms = {}
    for target, tdata in vms.items():
        vm_ids.setdefault(target, [])
        tdata = vms[target]
        if tdata is None:
            vms[target] = []
            continue
        for vmname in tdata:
            vm_ids[target].append(vmname)
            vt_vms[vmname] = target

    vtSettings = _s['mc_utils.format_resolve'](vtSettings)
    if id_ not in non_managed_hosts:
        # expose vm conf to vm
        if id_ in vt_vms:
            data['makina-states.cloud.is.vm.{0}'.format(vt)] = True
            data['makina-states.cloud.is.vm'] = True
            data.update(vm_pillar_fun(id_, vt_vms[id_],
                                      cloudSettings=cloudSettings,
                                      default_settings=vtSettings))
        # expose to compute node their relative vm configurations
        if id_ in vms:
            data['makina-states.cloud.is.compute_node.{0}'.format(vt)] = True
            data['makina-states.cloud.is.compute_node'] = True
            for owned_vm in vms[id_]:
                if (owned_vm not in vt_vms) or (id_ == owned_vm):
                    continue
                data.update(vm_pillar_fun(owned_vm, id_,
                                          cloudSettings=cloudSettings,
                                          default_settings=vtSettings))
        # expose global conf to cloud master and cloud nodes
        if (
            conf.get('cloud_master', False)
            or id_ in vms
            or id_ in vt_vms
        ):
            data['makina-states.cloud.{0}'.format(vt)] = vtSettings
            if not (id_ in vms or id_ in vt_vms):
                data['makina-states.cloud.vt_vms'] = vt_vms
    return data


def overridable_default_settings(id_=None, cloudSettings):
    if id_ is None:
        id_ = __grains__['id']
    default_snapshot = False
    if _s['mc_cloud_vm.is_devhost']():
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
    if not additionnal_defaults:
        additionnal_defaults = {}
    if not extdata:
        extdata = None
    data = _s['mc_utils.dictupdate'](
        _s['mc_utils.dictupdate'](
            defaults_fun(),
            _s['mc_utils.dictupdate'](
                _s['mc_cloud_vm.overridable_default_settings'](
                    id_, cloudSettings), additionnal_defaults
            )
        ), extdata
    )
    return data


def vm_settings_for(vm, ttl=60):
    '''
    VM cloud related settings
    THIS IS USED ON THE COMPUTE NODE SIDE !
    '''
    def _do(vm):
        return vm_settings('_' + vm)
    cache_key = ('mc_cloud_vm.vm_settings_for'
                 '{0}').format(vm)
    return memoize_cache(_do, [vm], {}, cache_key, ttl)


def vt_extpillar(id_,
                 prefix,
                 vt,
                 default_settings_fun,
                 vm_ext_pillar_fun,
                 additionnal_defaults=None):
    cloudSettings = _s['mc_cloud.default_settings']()
    extdata = _s['mc_pillar.get_global_clouf_conf'](vt)
    if not additionnal_defaults:
        additionnal_defaults = {}
    vtSettings = _s['mc_cloud_vm.mangle_default_settings'](
        id_,
        cloudSettings,
        default_settings_fun,
        extdata=extdata,
        additionnal_defaults=additionnal_defaults)
    data = _s['mc_cloud_vm.expose_pillar'](
        id_, vt, vm_ext_pillar_fun, vtSettings, cloudSettings)
    return {prefix: data}


def extpillar_for(vm, vt):
    return __salt__['mc_cloud_{0}.ext_pillar'.format(vt)](vm)
# vim:set et sts=4 ts=4 tw=81:
