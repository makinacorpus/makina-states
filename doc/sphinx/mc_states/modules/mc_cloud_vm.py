#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_vm:

mc_cloud_vm / vm registry for compute nodes
===============================================



'''

# Import python libs
import logging
import mc_states.api
import os
import copy


from mc_states import saltapi
from mc_states.modules.mc_pillar import PILLAR_TTL
from salt.utils.odict import OrderedDict

__name = 'mc_cloud_vm'

log = logging.getLogger(__name__)
VT = 'vm'
PREFIX = 'makina-states.cloud.vms'


def vt(vt=VT):
    # pylint: disable=W0621
    return vt


def vt_default_settings(cloudSettings, imgSettings, ttl=60):
    '''
    VM default settings:
        - This may be needed to be database backended in the future.
          As well, we may need iterator loops inside jinja templates
          to not eat that much memory loading large datasets.

    makina-states.services.cloud.lxc
        The settings of lxc containers that are meaningful on the
        cloud controller


    Lately we will focus to tie the implementation to the
    APPCONTAINER SPEC

    cloud defaults (makina-states.services.cloud.lxc)
        defaults settings to provision lxc containers
        Those are all redefinable at each container level

    Settings:
        ssh_gateway
            ssh gateway info
        ssh_gateway_port
            ssh gateway info
        ssh_gateway_user
            ssh gateway info
        ssh_gateway_key
            ssh gateway info
        ports
            if hostport is omitted, it will be dynamically assigned
            in the avalaible port range (40000-50000 by default)

            hostPortRange default to portRange if portRange found

            example::

                {name: redis, port: 6379,
                 protocol: tcp, hostPort: 22}
                {name: redis, portRange: "63:79",
                 protocol: tcp, hostPortRange: "22:23"}

        size
            default filesystem size for container on lvm
            None
        gateway
            10.5.0.1
        master
            master to uplink the container to
            None
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
    def _dovt_default_settings(cloudSettings, imgSettings):
        _s = __salt__
        _g = __grains__
        default_snapshot = False
        if _s['mc_nodetypes.is_devhost']():
            default_snapshot = True
        vte_settings = {
            'vt': VT,
            'defaults': {
                'dnsservers': ['8.8.8.8', '4.4.4.4'],
                #
                'image': 'ubuntu',
                'snapshot': default_snapshot,
                'autostart': True,
                #
                'target': None,
                'gateway': '127.0.0.1',
                'use_bridge': True,
                'main_bridge': 'br0',
                'ip': None,
                'mac': None,
                'netmask': '16',
                'network': '10.3.0.0',
                'netmask_full': '255.255.0.0',
                'bridge': 'lxcbr0',
                'additional_ips': [],
                'name': _g['id'],
                'domains': [_g['id']],
                'ports': [
                    {'name': 'ssh', 'port': 22, 'protocol': 'tcp'},
                    {'name': 'ssh', 'port': 22, 'protocol': 'udp'},
                    #{'name': 'ssh', 'portRange': "222:223", 'protocol': 'udp'},
                ],
                #
                'master': cloudSettings.get('master', __opts__['id']),
                'bootsalt_branch': cloudSettings['bootsalt_branch'],
                'bootstrap_shell': cloudSettings['bootstrap_shell'],
                'script': cloudSettings['script'],
                'script_args': ' -C --no-colors',
                #
                'ssh_reverse_proxy_port': None,
                'snmp_reverse_proxy_port': None,
                #
                'password': None,
                'sudo': True,
                'users': ['root', 'sysadmin'],
                #
                'size': None,  # via profile
                'backing': 'lvm',
                'pools': [{'name': 'vg', 'type': 'lvm'}],
                'volumes': [
                    # non implemented yet in any drivers
                    # {"name": "w", "kind": "host",
                    #  "source": "/o/t", "readOnly": True}
                ],
                'mounts': {
                    # {"volume": "w", "mountPoint": "/path/backup"}
                }
            },
            'vms': OrderedDict(),
        }
        return vte_settings
    cache_key = 'mc_cloud_vm.default_settings'
    return copy.deepcopy(
        __salt__['mc_utils.memoize_cache'](
            _dovt_default_settings, [cloudSettings, imgSettings], {},
            cache_key, ttl))


# pylint: disable=W0621
def vm_default_settings(vm,
                        cloudSettings,
                        imgSettings,
                        extpillar=False,
                        vt='lxc',
                        extdata=None):
    '''
    Get per VM specific settings

    All the defaults defaults registry settings are redinable here +
    This is for the moment the only backend of corpus cloud infra.
    If you want to implement another backend, mimic the dictionnary
    for this method and also settings.

        ip
            do not set it, or use at ure own risk, prefer just to read the
            value. This is the main ip (private network)
        additional_ips
            additionnal ips which will be wired on the main bridge (br0)
            which is connected to internet.
            Be aware that you may use manual virtual mac addresses
            providen by you provider (online, ovh, sys).
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

       expose/expose_limited
          expose configuration to other nodes, see mc_cloud.ext_pillar

    '''
    _s = __salt__
    if not extdata:
        extdata = {}
    if extpillar:
        vm_infos = _s['mc_cloud_compute_node.get_vm'](vm)
        target, vt = vm_infos['target'], vm_infos.get('vt', vt)
        vtsettings = _s['mc_cloud_vm.vt_extpillar'](target, vt)
    else:
        vt = extdata.get('vt', vt)
        vtsettings = vt_settings(vt)
        target = extdata.get('target', vtsettings['defaults']['target'])
    if extpillar:
        node = 'mc_cloud_compute_node.'
        ssh_port = _s[node + 'get_ssh_port'](vm)
        snmp_port = _s[node + 'get_snmp_port'](vm)
    else:
        ssh_port = 40000
        snmp_port = 30000
    ssh_port = extdata.get('ssh_port', ssh_port)
    snmp_port = extdata.get('snmp_port', snmp_port)
    master = extdata.get('master', vtsettings['defaults']['master'])
    master = vtsettings['defaults']['master']
    if extpillar:
        # if it is not a distant minion, use private gateway ip
        if _s['mc_pillar.minion_id']() == target:
            master = vtsettings['defaults']['gateway']
    data = _s['mc_utils.dictupdate'](
        copy.deepcopy(vtsettings['defaults']),
        {'name': vm,
         'expose': [],
         'expose_limited': {},
         'vt': vtsettings['vt'],
         'target': target,
         'master': master,
         'domains': [vm],
         'ssh_reverse_proxy_port': ssh_port,
         'snmp_reverse_proxy_port': snmp_port})
    return copy.deepcopy(data)


def vm_registry(prefixed=True):
    prefix = PREFIX + "."
    if not prefixed:
        prefix = ''
    data = OrderedDict([('{0}vts'.format(prefix), OrderedDict()),
                        ('{0}this_host'.format(prefix), ''),
                        ('{0}this_port'.format(prefix), ''),
                        ('{0}vms'.format(prefix), OrderedDict())])
    return data


def vt_extpillar_settings(vt, ttl=PILLAR_TTL):

    def _dovt_extpillar_settings(vte):
        _s = __salt__
        fun = 'mc_cloud_{0}.vt_default_settings'.format(vt)
        extdata = _s['mc_pillar.get_global_clouf_conf'](vt)
        cloudSettings = _s['mc_cloud.extpillar_settings']()
        imgSettings = _s['mc_cloud_images.extpillar_settings']()
        data = cloudSettings = _s['mc_utils.dictupdate'](
            _s[fun](cloudSettings, imgSettings), extdata)
        return data
    cache_key = 'mc_cloud_vm.vt_extpillar_settings{0}'.format(vt)
    return __salt__['mc_utils.memoize_cache'](
        _dovt_extpillar_settings, [vt], {}, cache_key, ttl)


def vm_extpillar_settings(vm, limited=False, ttl=PILLAR_TTL):
    _s = __salt__

    def _sort_domains(dom):
        if dom == vm:
            return '0{0}'.format(dom)
        else:
            return '1{0}'.format(dom)

    def _dovm_extpillar_settings(vme, limited):
        cloudSettings = _s['mc_cloud.extpillar_settings']()
        imgSettings = _s['mc_cloud_images.extpillar_settings']()
        data = _s['mc_pillar.get_cloud_conf_for_vm'](vme)
        data = _s['mc_utils.dictupdate'](
            vm_default_settings(
                vme, cloudSettings, imgSettings, extpillar=True),
            data)
        find_ip = 'mc_cloud_compute_node.find_ip_for_vm'
        data['ip'] = _s[find_ip](vme,
                                 network=data['network'],
                                 netmask=data['netmask'],
                                 default=data.get('ip'))
        data.update(__salt__['mc_cloud.ssh_host_settings'](
            data['name'], defaults=data))
        data['mac'] = _s['mc_cloud_compute_node.find_mac_for_vm'](
            vme, default=data.get('mac', None))
        data['password'] = _s[
            'mc_cloud_compute_node.find_password_for_vm'
        ](vme, default=_s['mc_pillar.get_passwords'](vme)['clear']['root'])
        data = saltapi.complete_gateway(data, data)
        if vme not in data['domains']:
            data['domains'].insert(0, vme)
        data['domains'].sort(key=_sort_domains)
        if (
            ('-b' not in data['script_args']) and
            ('--branch' not in data['script_args'])
        ):
            data['script_args'] += ' -b {0}'.format(
                data['bootsalt_branch'])
        # at this stage, only get already allocated ips
        ssh_port = None
        for ix in range(len(data['ports'])):
            pdata = data['ports'][ix]
            if not pdata.get('hostPort', ''):
                pdata['hostPort'] = __salt__[
                    'mc_cloud_compute_node.get_kind_port'
                ](vm, data['target'], pdata['name'])
            if pdata['name'] == 'ssh' or pdata.get('port') in [22]:
                ssh_port = pdata['hostPort']
        ssh_host = data['target']
        for ix, ipinfos in enumerate(data['additional_ips']):
            k = '{0}_{1}_{2}_aip_fo'.format(data['target'], vme, ix)
            mac = ipinfos.setdefault('mac', None)
            if not mac:
                mac = _s['mc_cloud_compute_node.get_conf_for_vm'](
                    vme, k, default=mac)
            if not mac:
                _s['mc_cloud_compute_node.set_conf_for_vm'](
                    vme, k, _s['mc_cloud_compute_node.gen_mac']())
            ipinfos['mac'] = mac
            ipinfos.setdefault('gateway', None)
            if ipinfos['gateway']:
                data['gateway'] = None
            ipinfos.setdefault('netmask', '32')
            ipinfos.setdefault('link', 'br0')
            # when using extra ip, force ip_port: 22
            # and direct acces top lxc
            ssh_port, ssh_host = 22, data['name']
        data.update({'ssh_port': ssh_port, 'ssh_host': ssh_host})
        return data
    cache_key = 'mc_cloud_vm.extpillar_settings{0}{1}8'.format(vm, limited)
    return __salt__['mc_utils.memoize_cache'](
        _dovm_extpillar_settings, [vm, limited], {}, cache_key, ttl)


def vt_extpillar(target, vt, limited=False, ttl=PILLAR_TTL):

    def _dovt_extpillar(target, vt, limited):
        _s = __salt__
        extdata = _s['mc_pillar.get_cloud_conf_for_cn'](target).get(vt, {})
        data = vt_extpillar_settings(vt)
        fun = 'mc_cloud_{0}.vt_extpillar'.format(vt)
        data = _s['mc_utils.dictupdate'](_s[fun](
            target, data, limited=limited), extdata)
        return data
    cache_key = 'mc_cloud_vm.vt_extpillar{0}{1}{2}1'.format(target, vt, limited)
    return __salt__['mc_utils.memoize_cache'](
        _dovt_extpillar, [target, vt, limited], {}, cache_key, ttl)


def domains_for(vm, domains=None):
    _s = __salt__
    if domains is None:
        vm_settings = _s['mc_cloud_vm.vm_extpillar_settings'](vm)
        domains = vm_settings['domains']
    # special case as domains is a list but we always want for
    # the vm id to be un domains list even if overriden in
    # extpillar
    domains = _s['mc_utils.uniquify']([vm] + domains)
    return domains


def vm_extpillar(id_, limited=False, ttl=60):

    def _dovm_extpillar(id_, limited):
        _s = __salt__
        extdata = _s['mc_pillar.get_cloud_conf_for_vm'](id_)
        data = vm_extpillar_settings(id_)
        fun = 'mc_cloud_{0}.vm_extpillar'.format(data['vt'])
        data = _s['mc_utils.dictupdate'](_s[fun](id_, data), extdata)
        data['domains'] = domains_for(id_, data['domains'])
        return data
    cache_key = 'mc_cloud_vm.vm_extpillar{0}{1}4'.format(id_, limited)
    return __salt__['mc_utils.memoize_cache'](
        _dovm_extpillar, [id_, limited], {},
        cache_key, ttl, use_memcache=True)


def ext_pillar(id_, prefixed=True, ttl=60, *args, **kw):

    def _doext_pillar(id_, prefixed, limited):
        _s = __salt__
        all_vms = _s['mc_cloud_compute_node.get_vms']()
        targets = _s['mc_cloud_compute_node.get_targets']()
        vms, vts = OrderedDict(), []
        target = None
        data = vm_registry(prefixed=prefixed)
        if prefixed:
            vts_pillar = data[PREFIX + '.vts']
            vms_pillar = data[PREFIX + '.vms']
            this_host = PREFIX + '.this_host'
            this_port = PREFIX + '.this_port'
        else:
            vts_pillar = data['vts']
            vms_pillar = data['vms']
            this_host = 'this_host'
            this_port = 'this_port'
        if id_ not in targets and id_ not in all_vms:
            return {}
        if id_ in all_vms:
            vt = all_vms[id_]['vt']
            if vt not in vts:
                vts.append(vt)
            vms[id_] = all_vms[id_]
            target = all_vms[id_]['target']
        if id_ in targets:
            target = id_
            for vm_, vmdata_ in targets[id_]['vms'].items():
                vms[vm_] = vmdata_
            # pylint: disable=W0612
            noecho = [vts.append(i) for i in targets[id_]['vts']
                      if i not in vts]
        for vt in vts:
            vts_pillar[vt] = _s['mc_cloud_vm.vt_extpillar'](
                target, vt, limited=limited)
        for vm, vmdata in vms.items():
            vt = vmdata['vt']
            vme_settings = _s['mc_cloud_vm.vm_extpillar'](
                vm, limited=limited)
            if id_ == vm:
                data[this_port] = vme_settings[
                    'ssh_reverse_proxy_port']
                data[this_host] = vme_settings['target']
            vme_settings['vt'] = vt
            vms_pillar[vm] = vme_settings
        return data
    limited = kw.get('limited', False)
    cache_key = 'mc_cloud_vm.ext_pillar{0}{1}{2}2'.format(
        id_, prefixed, limited)
    return __salt__['mc_utils.memoize_cache'](
        _doext_pillar, [id_, prefixed, limited], {},
        cache_key, ttl, use_memcache=True)


# pylint: disable=w0105
'''
Methods usable
After the pillar has loaded, on the compute node or on the VM
'''


def raw_settings(ttl=60):

    def _doraw_settings():
        _s = __salt__
        settings = _s['mc_utils.defaults'](PREFIX, vm_registry(prefixed=False))
        return settings
    cache_key = '{0}.{1}'.format(__name, 'raw_settings')
    return __salt__['mc_utils.memoize_cache'](
        _doraw_settings, [], {}, cache_key, ttl)


def vts_settings(ttl=60):

    def _dovts_settings():
        data = raw_settings()
        _s = __salt__
        svts = data.setdefault('vts', OrderedDict())
        cloudSettings = _s['mc_cloud.settings']()
        imgSettings = _s['mc_cloud_images.settings']()
        for vt in _s['mc_cloud_compute_node.get_vts']():
            vt_fun = 'mc_cloud_{0}.vt_default_settings'.format(vt)
            svts[vt] = _s['mc_utils.dictupdate'](
                _s['mc_utils.defaults'](
                    '{0}.vts.{1}'.format(PREFIX, vt),
                    _s[vt_fun](cloudSettings, imgSettings)),
                data.get(vt, {}))
        return svts
    cache_key = '{0}.{1}'.format(__name, 'vts_settings')
    return __salt__['mc_utils.memoize_cache'](
        _dovts_settings, [], {}, cache_key, ttl)


def vt_settings(vt=VT, ttl=60):

    def _dovt_settings(vte):
        return vts_settings().get(vte, {})
    cache_key = '{0}.{1}{2}'.format(__name, 'vt_settings', vt)
    return __salt__['mc_utils.memoize_cache'](
        _dovt_settings, [vt], {}, cache_key, ttl)


def vms_settings(ttl=60):
    def _dovms_settings():
        _s = __salt__
        svms = raw_settings().setdefault('vms', OrderedDict())
        if svms:
            cloudSettings = _s['mc_cloud.settings']()
            imgSettings = _s['mc_cloud_images.settings']()
            for vm in [a for a in svms]:
                data = svms[vm]
                if data and ('vt' in data):
                    fun = 'mc_cloud_vm.vm_default_settings'
                    cloudSettings = _s['mc_cloud.settings']()
                    imgSettings = _s['mc_cloud_images.settings']()
                    svms[vm] = _s['mc_utils.dictupdate'](
                        _s[fun](vm,
                                cloudSettings,
                                imgSettings,
                                extpillar=False,
                                extdata=data),
                        data)
        return svms
    cache_key = '{0}.{1}2'.format(__name, 'vms_settings')
    return __salt__['mc_utils.memoize_cache'](
        _dovms_settings, [], {}, cache_key, ttl)


def vm_host_and_port(ttl=600):
    def dovm_host_and_port():
        def fdo():
            host, port = __grains__['id'], 22
            if __salt__['mc_cloud.is_vm']():
                res = __salt__['mc_cloud_vm.vm_settings']()
                if res.get('target', None)  and res.get('ssh_reverse_proxy_port', None):
                    host = res['target']
                    port = res['ssh_reverse_proxy_port']
            return host, port
        return __salt__['mc_macros.filecache_fun'](
            fdo,
            prefix='salt_cloud_vm_host_port_2{0}'.format(__grains__['id']),
            ttl=5 * 24 * 60 * 60)
    cache_key = '{0}.{1}.{2}'.format(__name, 'vm_host_and_port', '')
    return __salt__['mc_utils.memoize_cache'](
        dovm_host_and_port, [], {}, cache_key, ttl)


def vm_settings(id_=None, ttl=60):
    def _dovm_settings(id_):
        if not id_:
            id_ = __grains__['id']
        return vms_settings().get(id_, {})
    cache_key = '{0}.{1}{2}'.format(__name, 'vm_settings', id_)
    return __salt__['mc_utils.memoize_cache'](
        _dovm_settings, [id_], {}, cache_key, ttl)


def settings(ttl=60):
    def _dosettings():
        rdata = {'vms': vms_settings(),
                 'vts': vts_settings()}
        return rdata
    cache_key = '{0}.{1}'.format(__name, 'settings')
    return __salt__['mc_utils.memoize_cache'](
        _dosettings, [], {}, cache_key, ttl)
# vim:set et sts=4 ts=4 tw=81:
