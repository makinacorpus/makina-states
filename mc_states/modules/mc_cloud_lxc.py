# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_lxc:

mc_cloud_lxc / lxc registry for compute nodes
===============================================

'''
__docformat__ = 'restructuredtext en'

# Import python libs
import logging
import mc_states.utils

from mc_states import saltapi
from salt.utils.odict import OrderedDict

_errmsg = saltapi._errmsg
__name = 'mc_cloud_lxc'

log = logging.getLogger(__name__)
MAC_GID = 'makina-states.cloud.lxc.vmsettings.{0}.{1}.mac'
PW_GID = 'makina-states.cloud.lxc.vmsettings.{0}.{1}.password'
IP_GID = 'makina-states.cloud.lxc.vmsettings.{0}.{1}.ip'


def is_lxc():
    """
    in case of a container, we have the container name in cgroups
    else, it is equal to /

    in lxc:
        ['11:name=systemd:/user/1000.user/1.session',
        '10:hugetlb:/thisname',
        '9:perf_event:/thisname',
        '8:blkio:/thisname',
        '7:freezer:/thisname',
        '6:devices:/thisname',
        '5:memory:/thisname',
        '4:cpuacct:/thisname',
        '3:cpu:/thisname',
        '2:cpuset:/thisname']

    in host:
        ['11:name=systemd:/',
        '10:hugetlb:/',
        '9:perf_event:/',
        '8:blkio:/',
        '7:freezer:/',
        '6:devices:/',
        '5:memory:/',
        '4:cpuacct:/',
        '3:cpu:/',
        '2:cpuset:/']
    """

    try:
        cgroups = open('/proc/1/cgroup').read().splitlines()
        lxc = not '/' == [a.split(':')[-1]
                          for a in cgroups if ':cpu:' in a][-1]
    except Exception:
        lxc = False
    return lxc


def settings():
    '''Lxc registry

    TODO:
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
        default_container
            default image
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
        sudo
            True
        use_bridge
            True
        backing
            (lvm, overlayfs, dir, brtfs) 'lvm'
        users
            ['root', 'sysadmin']
        ssh_username
            'ubuntu'
        vgname
            'data'
        lvname
            'data'
        lxc_conf
            []
        lxc_conf_unset'
            []
    vms
        List of containers ids classified by host ids::

            (Mapping of {hostid: [vmid]})

        The settings are not stored here for obvious performance reasons
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        _s = __salt__
        cloudSettings = _s['mc_cloud.settings']()
        imgSettings = _s['mc_cloud_images.settings']()
        nt_registry = _s['mc_nodetypes.registry']()
        default_container = [a for a in imgSettings['lxc']['images']][0]
        default_vm = OrderedDict()
        # no lvm on devhost
        # nor cron sync
        dptype = 'lvm'
        backing = 'lvm'
        if nt_registry['is']['devhost']:
            backing = dptype = 'overlayfs'
            # backing = dptype = 'dir'
        default_snapshot = False
        if nt_registry['is']['devhost']:
            default_snapshot = True
        lxcSettings = _s['mc_utils.defaults'](
            'makina-states.cloud.lxc', {
                'dnsservers': ['8.8.8.8', '4.4.4.4'],
                'defaults': {
                    'default_container': default_container,
                    'autostart': True,
                    'snapshot': default_snapshot,
                    'size': None,  # via profile
                    'profile': 'medium',
                    'profile_type': dptype,
                    'gateway': '10.5.0.1',
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
                    'network': '10.5.0.0',
                    'netmask': '16',
                    'bootsalt_branch': cloudSettings['bootsalt_branch'],
                    'netmask_full': '255.255.0.0',
                    'bridge': 'lxcbr1',
                    'sudo': True,
                    'use_bridge': True,
                    'backing': backing,
                    'users': ['root', 'sysadmin'],
                    'ssh_username': 'ubuntu',
                    'vgname': 'lxc',
                    'lvname': None,
                    'lxc_conf': [],
                    'lxc_conf_unset': [],
                },
                'vms': default_vm,
                'lxc_cloud_profiles': {
                    'xxxtrem': {'size': '2000g', },
                    'xxtrem': {'size': '1000g', },
                    'xtrem': {'size': '500g', },
                    'xxxlarge': {'size': '100g', },
                    'xxlarge': {'size': '50g', },
                    'large': {'size': '20g', },
                    'medium': {'size': '10g', },
                    'small': {'size': '5g', },
                    'xsmall': {'size': '3g', },
                    'xxsmall': {'size': '1g', },
                    'xxxsmall': {'size': '500m', },
                }
            }
        )
        # do not store in cached
        # registry the whole conf, memory would explode
        try:
            vms = lxcSettings.pop('vms')
        except:
            vms = OrderedDict()
        lxcSettings['vms'] = vm_ids = OrderedDict()
        for target in vms:
            vm_ids.setdefault(target, [])
            data = vms[target]
            for vmname in data:
                vm_ids[target].append(vmname)
        return lxcSettings
    return _settings()


def get_settings_for_vm(target, vm):
    '''get per container specific settings

    All the defaults defaults registry settings are redinable here +

        Corpus API

        ip
            do not set it, or use at ure own risk, prefer just to read the
            value.
        domains
            list of domains tied with this host (first is minion id
            and main domain name, it is automaticly added)
    '''
    cloudSettings = __salt__['mc_cloud.settings']()
    _s = __salt__
    lxcSettings = settings()
    lxc_defaults = lxcSettings['defaults']
    master = lxc_defaults['master']
    # if it is not a distant minion, use private gateway ip
    if __grains__['id'] == target:
        master = lxc_defaults['gateway']
    # filter dicts and overiddes
    lxc_data = _s['mc_utils.defaults'](
        'makina-states.cloud.lxc.vms.{0}.{1}'.format(target, vm),
        {})
    lxc_data.setdefault('master', master)
    lxc_data['password'] = _s[
        'mc_cloud_compute_node.find_password_for_vm'
    ](target, 'lxc', vm, default=lxc_data.get('password', None))
    lxc_data.setdefault('master', master)
    lxc_data.setdefault('ssh_gateway', target)
    lxc_data['mac'] = _s[
        'mc_cloud_compute_node.find_mac_for_vm'
    ](target, 'lxc', vm, default=lxc_data.get('mac', None))
    # shortcut name for profiles
    # small -> ms-target-small
    profile_type = lxc_data.get(
        'profile_type',
        lxc_defaults['profile_type'])
    profile = lxc_data.get('profile',
                           lxc_defaults['profile'])
    if (
        profile in lxcSettings['lxc_cloud_profiles']
        and 'profile' in lxc_data
    ):
        del lxc_data['profile']
    if 'overlayfs' in profile_type or 'scratch' in profile_type:
        sprofile = ''
        lxc_data['backing'] = 'overlayfs'
    elif 'dir' in profile_type or 'scratch' in profile_type:
        sprofile = ''
        lxc_data['backing'] = 'dir'
    else:
        sprofile = '-{0}'.format(profile)
    lxc_data.setdefault(
        'profile', _s['mc_cloud_controller.gen_id'](
            'ms-{0}{1}-{2}'.format(
                target, sprofile, profile_type)))
    lxc_data.setdefault('name', vm)
    lxc_data.setdefault('domains', [])
    if not vm in lxc_data['domains']:
        lxc_data['domains'].insert(0, vm)

    def _sort_domains(dom):
        if dom == vm:
            return '0{0}'.format(dom)
        else:
            return '1{0}'.format(dom)
    lxc_data['domains'].sort(key=_sort_domains)
    lxc_data.setdefault('mode', lxc_defaults['mode'])
    lxc_data.setdefault('size', None)
    lxc_data.setdefault('snapshot', lxc_defaults['snapshot'])
    if 'mastersalt' in lxc_data.get('mode', 'salt'):
        default_args = cloudSettings['bootsalt_mastersalt_args']
    else:
        default_args = cloudSettings['bootsalt_args']
    lxc_data['script_args'] = lxc_data.get('script_args',
                                           default_args)
    branch = lxc_data.get('bootsalt_branch',
                          cloudSettings['bootsalt_branch'])
    if (
        not '-b' in lxc_data['script_args']
        or not '--branch' in lxc_data['script_args']
    ):
        lxc_data['script_args'] += ' -b {0}'.format(branch)
    d_ct = None
    if not 'scratch' in profile_type:
        d_ct = lxc_defaults['default_container']
    lxc_data.setdefault('from_container', d_ct)
    lxc_data.setdefault('ssh_gateway', None)
    lxc_data = saltapi.complete_gateway(lxc_data, lxcSettings)
    for i in ['bootsalt_branch',
              "master", "master_port", "autostart",
              'size', 'image', 'bridge',
              'network', 'netmask', 'gateway',
              'dnsservers', 'backing', 'vgname', 'lvname',
              'ssh_gateway_password',
              'ssh_gateway_user',
              'ssh_gateway_key',
              'ssh_gateway_port',
              "gateway",
              'vgname', 'ssh_username', 'users', 'sudo',
              'lxc_conf_unset', 'lxc_conf']:
        lxc_data.setdefault(
            i, lxc_defaults.get(i,
                                lxcSettings.get(i, None)))
    if ('overlayfs' in profile_type) or ('dir' in profile_type):
        for k in ['lvname', 'vgname', 'size']:
            if k in lxc_data:
                del lxc_data[k]
    # at this stage, only get already allocated ips
    lxc_data['ip'] = _s['mc_cloud_compute_node.find_ip_for_vm'](
        target, 'lxc', vm,
        network=lxc_data['network'],
        netmask=lxc_data['netmask'],
        default=lxc_data.get('ip'))
    return lxc_data


def dump():
    return mc_states.utils.dump(__salt__,__name)


# vim:set et sts=4 ts=4 tw=80:
