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


def settings():
    '''Lxc registry

    TODO:
    This may be needed to be database backended in the future.
    As well, we may need iterator loops inside jinja templates
    to not eat that much memory loading large datasets.

    makina-states.services.cloud.kvm
        The settings of kvm containers that are meaningful on the
        cloud controller

    cloud defaults (makina-states.services.cloud.kvm)
        defaults settings to provision kvm containers
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
            10.6.0.1
        master
            master to uplink the container to
            None
        master_port
            '4506'
        image
            LXC template to use
            'ubuntu'
        network
            '10.6.0.0'
        netmask
            '16'
        netmask_full
            '255.255.0.0'
        autostart
            kvm is autostarted
        profile
            default size profile to use (medium) (apply only to lvm)
        profile_type
            default profile type to use (lvm)

                lvm
                    lvm backend from default container
                lvm-scratch
                    lvm backend from default kvm template
                dir
                    dir backend from default container
                dir-scratch
                    dir backend from default kvm template

        bridge
            we install via states a bridge in 10.6/16 kvmbr1)
            'kvmbr1'
        sudo
            True
        use_bridge
            True
        backing
            (lvm)
        users
            ['root', 'sysadmin']
        ssh_username
            'ubuntu'
        storage_pools
            pool defs (only lvm is supported for now)
    vms
        List of containers ids classified by host ids::

            (Mapping of {hostid: [vmid]})

        The settings are not stored here for obvious performance reasons
    '''
    # TODO: reenable cache
    #@mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        _s = __salt__
        cloudSettings = _s['mc_cloud.settings']()
        imgSettings = _s['mc_cloud_images.settings']()
        nt_registry = _s['mc_nodetypes.registry']()
        default_vm = OrderedDict()
        # no lvm on devhost
        # nor cron sync
        # backing = 'lvm'
        backing = 'lvm'
        default_snapshot = False
        if nt_registry['is']['devhost']:
            default_snapshot = True
        kvmSettings = _s['mc_utils.defaults'](
            'makina-states.cloud.kvm', {
                'dnsservers': ['8.8.8.8', '4.4.4.4'],
                'defaults': {
                    'autostart': True,
                    'snapshot': default_snapshot,
                    'size': None,  # via profile
                    'profile': 'medium',
                    'gateway': '10.6.0.1',
                    'mode': cloudSettings['mode'],
                    'ssh_gateway': cloudSettings['ssh_gateway'],
                    'ssh_gateway_password': cloudSettings[
                        'ssh_gateway_password'],
                    'ssh_gateway_user': cloudSettings['ssh_gateway_user'],
                    'ssh_gateway_key': cloudSettings['ssh_gateway_key'],
                    'ssh_gateway_port': cloudSettings['ssh_gateway_port'],
                    'master': cloudSettings['master'],
                    'master_port': cloudSettings['master_port'],
                    'image': 'ubuntu',
                    'network': '10.6.0.0',
                    'netmask': '16',
                    'bootsalt_branch': cloudSettings['bootsalt_branch'],
                    'netmask_full': '255.255.0.0',
                    'bridge': 'kvmbr1',
                    'main_bridge': 'br0',
                    'sudo': True,
                    'use_bridge': True,
                    'backing': backing,
                    'users': ['root', 'sysadmin'],
                    'ssh_username': 'ubuntu',
                    'pools': {'vg': {'type': 'lvm'}},
                },
                'vms': default_vm,
            }
        )
        # do not store in cached
        # registry the whole conf, memory would explode
        try:
            vms = kvmSettings.pop('vms')
        except:
            vms = OrderedDict()
        kvmSettings['vms'] = vm_ids = OrderedDict()
        for i in kvmSettings:
            if i.startswith('vms.'):
                del kvmSettings[i]
        for target in [a for a in vms]:
            vm_ids.setdefault(target, [])
            data = vms[target]
            if data is None:
                vms[target] = []
                continue
            for vmname in data:
                vm_ids[target].append(vmname)
        return kvmSettings
    return _settings()


def get_settings_for_vm(target, vm, full=True):
    '''get per container specific settings

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

                makina-states.cloud.kvm.vms.<target>.<name>.additionnal_ips:
                  - {'mac': '00:16:3e:01:29:40',
                     'gateway': None, (default)
                     'link': 'br0', (default)
                     'netmask': '32', (default)
                     'ip': '22.1.4.25'}
        domains
            list of domains tied with this host (first is minion id
            and main domain name, it is automaticly added)
        full
            internal boolean to not retrieve some informations to
            avoid cycles, do not use unless you know what you do.
        fstab
            list of fstab entries
    '''
    cloudSettings = __salt__['mc_cloud.settings']()
    _s = __salt__
    kvmSettings = settings()
    kvm_defaults = kvmSettings['defaults']
    master = kvm_defaults['master']
    # if it is not a distant minion, use private gateway ip
    if __grains__['id'] == target:
        master = kvm_defaults['gateway']
    # filter dicts and overiddes
    kvm_data = _s['mc_utils.defaults'](
        'makina-states.cloud.kvm.vms.{0}.{1}'.format(target, vm),
        {})
    if not kvm_data:
        pkvm_data = _s['mc_utils.defaults'](
            'makina-states.cloud.kvm.vms.{0}'.format(target), {})
        if pkvm_data:
            kvm_data = pkvm_data.get(vm, {})
    kvm_data.setdefault('master', master)
    kvm_data['password'] = _s[
        'mc_cloud_compute_node.find_password_for_vm'
    ](target, 'kvm', vm, default=kvm_data.get('password', None))
    kvm_data.setdefault('master', master)
    kvm_data.setdefault('ssh_gateway', target)
    kvm_data['mac'] = _s[
        'mc_cloud_compute_node.find_mac_for_vm'
    ](target, 'kvm', vm, default=kvm_data.get('mac', None))
    # shortcut name for profiles
    # small -> ms-target-small
    kvm_data.setdefault('name', vm)
    kvm_data.setdefault('domains', [])
    if vm not in kvm_data['domains']:
        kvm_data['domains'].insert(0, vm)

    def _sort_domains(dom):
        if dom == vm:
            return '0{0}'.format(dom)
        else:
            return '1{0}'.format(dom)
    kvm_data['domains'].sort(key=_sort_domains)
    kvm_data.setdefault('mode', kvm_defaults['mode'])
    kvm_data.setdefault('size', None)
    kvm_data.setdefault('snapshot', kvm_defaults['snapshot'])
    if 'mastersalt' in kvm_data.get('mode', 'salt'):
        default_args = cloudSettings['bootsalt_mastersalt_args']
    else:
        default_args = cloudSettings['bootsalt_args']
    if 'mastersalt' in kvm_data.get('mode', 'salt'):
        script = cloudSettings['script']
    else:
        script = cloudSettings['script']
    kvm_data['script'] = kvm_data.get('script', script)
    kvm_data['script_args'] = kvm_data.get('script_args',
                                           default_args)
    branch = kvm_data.get('bootsalt_branch',
                          cloudSettings['bootsalt_branch'])
    if (
        not '-b' in kvm_data['script_args']
        or not '--branch' in kvm_data['script_args']
    ):
        kvm_data['script_args'] += ' -b {0}'.format(branch)
    d_ct = None
    kvm_data.setdefault('from_container', d_ct)
    kvm_data.setdefault('ssh_gateway', None)
    kvm_data = saltapi.complete_gateway(kvm_data, kvmSettings)
    for i in ['bootsalt_branch',
              "master", "master_port", "autostart",
              'size', 'image', 'main_bridge',
              'bridge', 'network', 'netmask',
              'gateway', 'dnsservers',
              'backing', 'vgname',
              'ssh_gateway_password',
              'ssh_gateway_user',
              'ssh_gateway_key',
              'ssh_gateway_port',
              "gateway",
              "fstab",
              'vgname', 'ssh_username', 'users', 'sudo']:
        kvm_data.setdefault(
            i, kvm_defaults.get(i,
                                kvmSettings.get(i, None)))
    # at this stage, only get already allocated ips
    kvm_data['ip'] = _s['mc_cloud_compute_node.find_ip_for_vm'](
        target, vm,
        virt_type='kvm',
        network=kvm_data['network'],
        netmask=kvm_data['netmask'],
        default=kvm_data.get('ip'))
    if full:
        kvm_data['ssh_reverse_proxy_port'] = __salt__[
            'mc_cloud_compute_node.get_ssh_port'](vm=vm, target=target)
        kvm_data['snmp_reverse_proxy_port'] = __salt__[
            'mc_cloud_compute_node.get_snmp_port'](vm=vm, target=target)

    additional_ips = kvm_data.setdefault('additional_ips', [])
    for ix, ipinfos in enumerate(additional_ips):
        k = '{0}_{1}_{2}_aip_fo'.format(target, vm, ix)
        mac = ipinfos.setdefault('mac', None)
        if not mac:
            mac = __salt__['mc_cloud_compute_node.get_conf_for_vm'](
                target, 'kvm', vm, k, default=mac)
        if not mac:
            __salt__['mc_cloud_compute_node.set_conf_for_vm'](
                target, 'kvm', vm,
                k, __salt__['mc_cloud_compute_node.gen_mac']())
        ipinfos['mac'] = mac
        ipinfos.setdefault('gateway', None)
        if ipinfos['gateway']:
            kvm_data['gateway'] = None
        ipinfos.setdefault('netmask', '32')
        ipinfos.setdefault('link', 'br0')
    return kvm_data


def dump():
    return mc_states.utils.dump(__salt__,__name)


# vim:set et sts=4 ts=4 tw=80:
