#!/usr/bin/env python
'''
.. _module_mc_cloud_compute_node:

mc_cloud_compute_node / cloud compute node related functions
==============================================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import random
import os
import msgpack
import mc_states.utils
from salt.utils.odict import OrderedDict
import msgpack.exceptions
from salt.utils.pycrypto import secure_password
import msgpack.exceptions
try:
    import netaddr
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False

from mc_states import api

__name = 'mc_cloud_compute_node'

log = logging.getLogger(__name__)

VIRT_TYPES = {
    'lxc': {}
}
_RP = 'reverse_proxies'
_CUR_API = 2


def gen_mac():
    return ':'.join(map(lambda x: "%02x" % x, [0x00, 0x16, 0x3E,
                                               random.randint(0x00, 0x7F),
                                               random.randint(0x00, 0xFF),
                                               random.randint(0x00, 0xFF)]))


def _encode(value):
    '''encode using msgpack backend'''
    return msgpack.packb({'value': value})


def _fencode(filep, value):
    '''encode in a file using msgpack backend'''
    dfilep = os.path.dirname(filep)
    if not os.path.exists(dfilep):
        os.makedirs(dfilep)
    with open(filep, 'w') as fic:
        fic.write(_encode(value))
    try:
        os.chmod(filep, 0700)
    except:
        pass


def _decode(filep):
    '''decode in a file using msgpack backend'''
    value = None
    try:
        if os.path.exists(filep):
            with open(filep) as fic:
                rvalue = fic.read()
                value = msgpack.unpackb(rvalue)['value']
    except msgpack.exceptions.UnpackValueError:
        log.error('decoding error, removing stale {0}'.format(filep))
        os.unlink(filep)
        value = None
    return value


def set_conf_for_target(target, setting, value):
    '''Register a specific setting for a specific target'''
    target = target.replace('.', '')
    cloudSettings = __salt__['mc_cloud.settings']()
    filep = os.path.join(
        cloudSettings['root'],
        cloudSettings['compute_node_sls_dir'],
        target, 'settings',
        setting + '.pack'
    )
    _fencode(filep, value)
    return value


def get_conf_for_target(target, setting, default=None):
    '''get the stored specific setting for a specific target'''
    target = target.replace('.', '')
    cloudSettings = __salt__['mc_cloud.settings']()
    filep = os.path.join(
        cloudSettings['root'],
        cloudSettings['compute_node_sls_dir'],
        target, 'settings', setting + '.pack'
    )
    value = default
    if os.path.exists(filep):
        value = _decode(filep)
    return value


def set_conf_for_vm(target, virt_type, vm, setting, value):
    target = target.replace('.', '')
    vm = vm.replace('.', '')
    cloudSettings = __salt__['mc_cloud.settings']()
    filep = os.path.join(
        cloudSettings['root'],
        cloudSettings['compute_node_sls_dir'],
        target, virt_type, vm, 'settings',
        setting + '.pack'
    )
    _fencode(filep, value)
    return value


def find_mac_for_vm(target, virt_type, vm, default=None):
    '''Generate and assign a mac addess to a specific
    vm on a specific host'''
    mac = get_conf_for_vm(target, virt_type, vm, 'mac')
    if not mac:
        mac = default
    if not mac:
        mac = gen_mac()
        if not mac:
            raise Exception(
                'Error while setting grainmac for {0}/{1}'.format(target,
                                                                  vm))
        set_conf_for_vm(target, virt_type, vm, 'mac', mac)
    return mac


def find_password_for_vm(target,
                         virt_type,
                         vm,
                         default=None,
                         pwlen=32):
    '''Return the vm password after creating it
    the first time
    '''
    password = get_conf_for_vm(target, virt_type, vm, 'password')
    if not password:
        password = default
    if not password:
        password = secure_password(pwlen)
        if not password:
            raise Exception('Error while setting password '
                            'grain for {0}/{1}'.format(target, vm))
        set_conf_for_vm(target, virt_type, vm, 'password', password)
    return password


def remove_allocated_ip(target, ip):
    sync = False
    all_ips = get_allocated_ips(target)
    if ip in all_ips['ips'].values():
        for i in [a for a in all_ips]:
            if all_ips[i] == ip:
                del all_ips[i]
                sync = True
    if sync:
        set_conf_for_target(target, 'allocated_ips', all_ips)
    return get_allocated_ips(target)


def get_allocated_ips(target):
    allocated_ips = get_conf_for_target(target, 'allocated_ips')
    if (allocated_ips is None) or (not isinstance(allocated_ips, dict)):
        allocated_ips = {}
    for k in ['api', 'ips']:
        if k not in allocated_ips:
            sync = True
    allocated_ips.setdefault('api', _CUR_API)
    cur_ips = allocated_ips.setdefault('ips', {})
    existing_vms = get_vms_for_target(target)
    # recycle old ips for unexisting vms
    sync = False
    for name in [n for n in cur_ips]:
        if name not in existing_vms:
            sync = True
            del cur_ips[name]
    if sync:
        set_conf_for_target(target, 'allocated_ips', allocated_ips)
    return allocated_ips


def find_ip_for_vm(target,
                   virt_type,
                   vm,
                   network,
                   netmask,
                   default=None):
    '''Search for:

        - an ip already allocated
        - an random available ip in the range

    '''

    if not HAS_NETADDR:
        raise Exception('netaddr required for ip generation')
    allocated_ips = get_allocated_ips(target)
    try:
        ip4 = get_conf_for_vm(target, virt_type, vm, 'ip4')
    except msgpack.exceptions.UnpackValueError:
        ip4 = None
    if not ip4:
        ip4 = default
    if not ip4:
        # get network bounds
        network = netaddr.IPNetwork('{0}/{1}'.format(network, netmask))
        # converts stringued ips to IPAddress objects
        all_ips = allocated_ips['ips'].values()
        for try_ip in network[2:-2]:  # skip the firsts and last for gateways
            parts = try_ip.bits().split('.')
            stry_ip = "{0}".format(try_ip)
            if (
                stry_ip in all_ips  # already allocated
            ) or (
                parts[-1] in ['00000000', '11111111']  # 10.*.*.0 or 10.*.*.255
            ):
                continue
            else:
                ip4 = stry_ip
                break
            raise Exception('Did not get an available ip in the {2} network'
                            ' for {0}/{1}'.format(target, vm, virt_type))
        set_conf_for_vm(target, virt_type, vm, 'ip4', ip4)
    cur_ip = allocated_ips['ips'].get(vm)
    if ip4 and (ip4 != cur_ip):
        allocated_ips['ips'][vm] = ip4
        set_conf_for_target(target, 'allocated_ips', allocated_ips)
    return ip4


def get_conf_for_vm(target,
                    virt_type,
                    vm,
                    setting,
                    default=None):
    target = target.replace('.', '')
    vm = vm.replace('.', '')
    cloudSettings = __salt__['mc_cloud.settings']()
    filep = os.path.join(
        cloudSettings['root'],
        cloudSettings['compute_node_sls_dir'],
        target, virt_type, vm, 'settings', setting + '.pack')
    value = default
    if os.path.exists(filep):
        value = _decode(filep)
    return value


def default_has(vts=None, **kwargs):
    if vts is None:
        vts = {}
    for vt in VIRT_TYPES:
        vts.setdefault(vt, bool(kwargs.get(vt, False)))
    return vts


def get_firewall_toggle():
    return __salt__['mc_utils.get'](
        'makina-states.cloud.compute_node.has.firewall', True)


def get_ssh_port_end():
    return __salt__['mc_utils.get'](
        'makina-states.cloud.compute_node.ssh_start_port', '50000')


def get_ssh_port_start():
    return __salt__['mc_utils.get'](
        'makina-states.cloud.compute_node.ssh_start_port', 40000)


def _find_available_port(targets, target, data):
    ip = data['ip']
    ip_parts = ip.split('.')
    ssh_start_port = int(get_ssh_port_start())
    return (int(ssh_start_port) +
            (256 * int(ip_parts[2])) +
            int(ip_parts[3]))


def _add_server_to_backend(reversep, backend_name, domain, ip, kind='http'):
    """The domain is ppurely informative here"""
    _backends = reversep.setdefault('{0}_backends'.format(kind), {})
    bck = _backends.setdefault(backend_name,
                               {'name': backend_name,
                                'raw_opts': [
                                    'balance roundrobin',
                                ],
                                'servers': []})
    # for now rely on settings xforwardedfor header
    if reversep['{0}_proxy'.format(kind)].get(
        'http_proxy_mode', 'xforwardedfor'
    ) == 'xforwardedfor':
        bck['raw_opts'].append('option http-server-close')
        bck['raw_opts'].append('option forwardfor')
    else:
        # in not much time we ll switch to the haproxy proxy protocol which
        # leverage the xforwardedfor hack
        bck['raw_opts'].append('source 0.0.0.0 usesrc clientip')
    srv = {'name': 'srv_{0}{1}'.format(domain, len(bck['servers']) + 1),
           'bind': '{0}:80'.format(ip),
           'opts': 'check'}
    if not srv['bind'] in [a.get('bind') for a in bck['servers']]:
        bck['servers'].append(srv)


def _get_rp(target):
    _default_rp = {
        'target': target['target'],
    }
    return target.setdefault(_RP, _default_rp)


def _configure_http_reverses(reversep, domain, ip, http_proxy_mode=None):
    if not http_proxy_mode:
        http_proxy_mode = 'xforwardedfor'
    http_proxy = reversep.setdefault(
        'http_proxy',
        {'name': reversep['target'],
         'mode': 'http',
         'http_proxy_mode': http_proxy_mode,
         'bind': '*:80',
         'raw_opts': []})
    https_proxy = reversep.setdefault(
        'https_proxy',
        {'name': "secure-" + reversep['target'],
         'mode': 'http',
         'http_proxy_mode': http_proxy_mode,
         'bind': '*:443',
         'raw_opts': []})
    backend_name = 'bck_{0}'.format(domain)
    sbackend_name = 'securebck_{0}'.format(domain)
    rule = 'acl host_{0} hdr(host) -i {0}'.format(domain)
    if rule not in http_proxy['raw_opts']:
        http_proxy['raw_opts'].insert(0, rule)
        https_proxy['raw_opts'].insert(0, rule)
    rule = 'use_backend {1} if host_{0}'.format(domain, backend_name)
    if rule not in http_proxy['raw_opts']:
        http_proxy['raw_opts'].append(rule)
    rule = 'use_backend {1} if host_{0}'.format(domain, sbackend_name)
    if rule not in https_proxy['raw_opts']:
        https_proxy['raw_opts'].append(rule)
    _add_server_to_backend(reversep, backend_name, domain, ip)
    _add_server_to_backend(reversep, sbackend_name, domain, ip, kind='https')


def feed_http_reverse_proxy_for_target(target, target_data=None):
    '''Get reverse proxy information mapping for a specicific target
    This return a useful mappings of infos to reverse proxy http
    and ssh services with haproxy
    '''
    _s = __salt__.get
    if target_data is None:
        target_data = get_settings_for_target(target)
    reversep = _get_rp(target_data)
    for vmname in target_data['vms']:
        vm = target_data['vms'][vmname]
        for domain in vm['domains']:
            _configure_http_reverses(reversep, domain, vm['ip'],
                                     http_proxy_mode=vm.get('http_proxy_mode',
                                                            None))
    return reversep


def _get_next_available_port(ports, start, stop):
    for i in range(start, stop + 1):
        if i not in ports:
            return i
    raise ValueError('mc_compute_node: No more available ssh port')


def get_ssh_mapping_for_target(target, target_data=None):
    feed_http_reverse_proxy_for_target(target, target_data=target_data)
    return get_conf_for_target(target, 'ssh_map',  {})


def get_ssh_port(target, vm, target_data=None):
    feed_http_reverse_proxy_for_target(target, target_data=target_data)
    return get_conf_for_target(target, 'ssh_map',  {}).get(vm, None)


def feed_ssh_reverse_proxies_for_target(target, target_data=None):
    _s = __salt__.get
    _settings = settings()
    if target_data is None:
        target_data = get_settings_for_target(target)
    reversep = _get_rp(target_data)
    start = int(_settings['ssh_port_range_start'])
    end = int(_settings['ssh_port_range_end'])
    need_sync = False
    ssh_map = get_conf_for_target(target, 'ssh_map', {})
    vms_infos = target_data.get('vms', {})
    ssh_proxies = reversep.setdefault('ssh_proxies', [])
    for a in [a for a in ssh_map]:
        ssh_map[a] = int(ssh_map[a])
    # filter old vms grains
    for avm in [a for a in ssh_map]:
        if avm not in vms_infos:
            del ssh_map[avm]
            need_sync = True
    for vm, data in vms_infos.items():
        port = ssh_map.get(vm, None)
        if not port:
            port = _get_next_available_port(ssh_map.values(), start, end)
            ssh_map[vm] = port
            need_sync = True
        ssh_proxy = {'name': 'lst_{0}'.format(vm),
                     'bind': ':{0}'.format(port),
                     'mode': 'tcp',
                     'raw_opts': [],
                     'servers': [{
                         'name': 'sshserver',
                         'bind': '{0}:22'.format(data['ip']),
                         'opts': 'check'}]}
        if ssh_proxy not in ssh_proxies:
            ssh_proxies.append(ssh_proxy)
    if need_sync:
        set_conf_for_target(target, 'ssh_map', ssh_map)
    return reversep


def _add_vt_to_target(target, vt):
    vts = target.setdefault('virt_types', OrderedDict())
    default_has(vts, **{vt: False})


def get_settings_for_target(target, target_data=None):
    '''Return specific compute node related settings for a specific target

        reverse_proxies
            mapping of reverse proxies info
        domain
            list of domains served by host
        virt_types
            virt types supported by the box.
            This is a mapping and the value is weither the virt type is
            enabled or not
        vms
            light mappings infos of underlying vms

                ip
                    ip of vm
                virt_type
                    virt type of vm
                domains
                    domains related to the vm
                vmname
                    name of the vm
    '''
    _s = __salt__
    # iterate over all supported vts
    if target_data is None:
        target_data = {}
    target_data['target'] = target
    vms = get_vms_per_type(target)
    for virt_type, vm_ids in vms.items():
        _add_vt_to_target(target_data, virt_type)
        target_data['virt_types'][virt_type] = True
        vms = target_data.setdefault('vms', OrderedDict())
        for vmname in vm_ids:
            vm_settings = _s[
                'mc_cloud_{0}.get_settings_for_vm'.format(virt_type)
            ](target, vmname, full=False)
            ip = vm_settings['ip']
            # reload allocated_ips each time in case settings were updated
            allocated_ips = get_allocated_ips(target)
            # assert that the allocated_ips configuration has
            # been updated
            assert ip in allocated_ips['ips'].values()
            target_data.setdefault('domains', [])
            for domain in vm_settings['domains']:
                if domain not in target_data['domains']:
                    target_data['domains'].append(domain)
            # link onto the host the vm infos
            target_data['vms'][vmname] = {
                'virt_type':  virt_type,
                'ip': ip,
                'http_proxy_mode': vm_settings.get('http_proxy_mode',
                                                   'xforwardedfor'),
                'domains': vm_settings['domains'],
                'vmname':  vm_settings['name']}
            if target_data.get('virt_type', '') in ['lxc', 'docker']:
                target_data['virt_types']['lxc'] = True
    target_data['firewall'] = get_firewall_toggle()
    feed_http_reverse_proxy_for_target(target, target_data)
    feed_ssh_reverse_proxies_for_target(target, target_data)
    return target_data


def get_reverse_proxies_for_target(target):
    '''Get reverse proxy information mapping for a specicific target
    See feed_reverse_proxy_for_target'''
    target_data = get_settings_for_target(target)
    return dict([(k, target_data[k]) for k in target_data
                 if k in (_RP, 'target')])


def settings():
    '''
    compute node related settings

    targets
        a mapping indexed by target minions ids

        vms
        A mapping indexed by vm minion ids and containing some info::

           {vm name: virt type}

        virt_types
            a list of supported virt types (lxc)
    has
        global configuration toggle

        firewall
            global firewall toggle

    ssh_port_range_start
        from where we start to enable ssh NAT ports.
        Default to 40000.

    ssh_port_range_end

        from where we end to enable ssh NAT ports.
        Default to 50000.

    Basically the compute node needs to:

        - setup reverse proxying
        - setup it's local internal addressing dns to point to private ips
        - everything else that's local to the compute node

    The computes nodes are often created implicitly by registration of vms
    on specific drivers like LXC but you can register some manually.

    makina-states.cloud.compute_node.settings.targets.devhost11.local: {}

    To add or modify a value, use the mc_utils.default habitual way of
    modifying the default dict.
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        data = _s['mc_utils.defaults'](
            'makina-states.cloud.compute_node', {
                'has': {'firewall': get_firewall_toggle()},
                'ssh_port_range_start': get_ssh_port_start(),
                'ssh_port_range_end': get_ssh_port_end(),
                'targets': get_vms(),
            })
        return data
    return _settings()


def is_compute_node():
    _settings = settings()
    return __salt__['mc_utils.get']('makina-states.cloud.is.compute_node')


def get_targets_and_vms_for_virt_type(virt_type):
    _s = __salt__
    virtsettings = _s['mc_cloud_{0}.settings'.format(virt_type)]()
    vtargets = virtsettings.get('vms', {})
    return vtargets


def get_vms_per_type(target):
    '''Return all vms indexed by virt_type for a special target'''
    all_targets = OrderedDict()
    for virt_type in VIRT_TYPES:
        per_type = all_targets.setdefault(virt_type, set())
        all_infos = get_targets_and_vms_for_virt_type(virt_type)
        for vmname in all_infos.get(target, []):
            per_type.add(vmname)
    for i in [a for a in all_targets]:
        all_targets[i] = [a for a in all_targets[i]]
    return all_targets


def get_vms():
    '''Return all vms indexed by targets'''
    data = OrderedDict()
    for virt_type in VIRT_TYPES:
        all_infos = get_targets_and_vms_for_virt_type(virt_type)
        for t in all_infos:
            target = data.setdefault(t, {})
            vms = {}
            vts = set()
            for vmname in all_infos[t]:
                vms.setdefault(vmname, virt_type)
                vts.add(virt_type)
            target['virt_types'] = [a for a in vts]
            target['vms'] = vms
    return data


def get_vms_for_target(target):
    '''Return all vms for a target'''
    return get_vms().get(target, {}).get('vms', [])


def dump():
    return mc_states.utils.dump(__salt__,__name)

# vim:set et sts=4 ts=4 tw=80:
