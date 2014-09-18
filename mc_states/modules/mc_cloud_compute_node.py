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
from mc_states.utils import memoize_cache
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
_SW_RP = 'shorewall_reverse_proxies'
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


def del_conf_for_target(target, setting):
    '''Register a specific setting for a specific target'''
    target = target.replace('.', '')
    cloudSettings = __salt__['mc_cloud.settings']()
    filep = os.path.join(
        cloudSettings['compute_node_pillar_dir'],
        target, 'settings',
        setting + '.pack'
    )
    if os.path.exists(filep):
        os.unlink(filep)


def set_conf_for_target(target, setting, value):
    '''Register a specific setting for a specific target'''
    target = target.replace('.', '')
    cloudSettings = __salt__['mc_cloud.settings']()
    filep = os.path.join(
        cloudSettings['compute_node_pillar_dir'],
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
        cloudSettings['compute_node_pillar_dir'],
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
        cloudSettings['compute_node_pillar_dir'],
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
    return password


def _construct_ips_dict(target):
    allocated_ips = get_conf_for_target(target, 'allocated_ips')
    sync = False
    if (allocated_ips is None) or (not isinstance(allocated_ips, dict)):
        allocated_ips = {}
    for k in ['api', 'ips']:
        if k not in allocated_ips:
            sync = True
    allocated_ips.setdefault('api', _CUR_API)
    allocated_ips.setdefault('ips', {})
    if sync:
        set_conf_for_target(target, 'allocated_ips', allocated_ips)
    return allocated_ips


def cleanup_allocated_ips(target):
    '''Maintenance routine to cleanup ips when ip
    exhaution arrises'''
    allocated_ips = _construct_ips_dict(target)
    existing_vms = get_vms_for_target(target)
    # recycle old ips for unexisting vms
    sync = False
    done = []
    cur_ips = allocated_ips.setdefault('ips', {})
    for name in [n for n in cur_ips]:
        ip = cur_ips[name]
        # doublon ip
        if ip in done:
            remove_allocated_ip(target, ip, vm=name)
        else:
            done.append(ip)
        # ip not allocated to any vm
        if name not in existing_vms:
            sync = True
            del cur_ips[name]
    if sync:
        set_conf_for_target(target, 'allocated_ips', allocated_ips)
    return allocated_ips


def get_allocated_ips(target):
    '''Get the allocated ips for a specific target'''
    allocated_ips = _construct_ips_dict(target)
    return allocated_ips


def remove_allocated_ip(target, ip, vm=None):
    '''Remove any ip from the allocated IP registry.
    If vm is specified, it must also match a vm
    which is allocated to this ip'''
    sync = False
    all_ips = get_allocated_ips(target)
    if ip in all_ips['ips'].values():
        for i in [a for a in all_ips['ips']]:
            if all_ips['ips'][i] == ip:
                if vm is not None and vm == i:
                    continue
                del all_ips['ips'][i]
                sync = True
    if sync:
        set_conf_for_target(target, 'allocated_ips', all_ips)
    return get_allocated_ips(target)['ips']


def target_for_vm(vm, target=None):
    '''Get target for a vm'''
    return get_vm(vm)['target']


def vt_for_vm(vm, target=None):
    '''Get VT for a vm'''
    return get_vm(vm)['vt']


def find_ip_for_vm(target,
                   vm,
                   default=None,
                   virt_type=None,
                   network=api.NETWORK,
                   netmask=api.NETMASK):
    '''Search for:

        - an ip already allocated
        - an random available ip in the range

    To get and maybe allocate an ip for a vm call

        find_ip_for_vm(target, vmname)

    For force/set an ip use::

        set_allocated_ip(target, vmname, '1.2.3.4')

    '''
    if not HAS_NETADDR:
        raise Exception('netaddr required for ip generation')
    allocated_ips = get_allocated_ips(target)
    ip4 = None
    if virt_type is None:
        virt_type = get_vms_for_target(target).get(vm, None)
    if virt_type:
        try:
            ip4 = get_conf_for_vm(target, virt_type, vm, 'ip4')
        except msgpack.exceptions.UnpackValueError:
            ip4 = None
    if not virt_type:
        virt_type = 'novtset'
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
    if not ip4:
        raise Exception('Did not get an available ip for {0}/{1}'.format(
            target, vm))
    cur_ip = allocated_ips['ips'].get(vm)
    if ip4 and (ip4 != cur_ip):
        allocated_ips['ips'][vm] = ip4
        set_conf_for_target(target, 'allocated_ips', allocated_ips)
    return ip4


def set_allocated_ip(target, vm, ip, vt=None):
    '''
    For force/set an ip use::

        set_allocated_ip(target, vmname, '1.2.3.4')

    '''
    if vt is None:
        vt = get_vms_for_target(target).get(vm, 'lxc')
    allocated_ips = get_allocated_ips(target)
    allocated_ips['ips'][vm] = ip
    set_conf_for_vm(target, vt, vm, 'ip4', ip)
    set_conf_for_target(target, 'allocated_ips', allocated_ips)
    return get_allocated_ips(target)


def get_conf_for_vm(target,
                    virt_type,
                    vm,
                    setting,
                    default=None):
    '''.'''
    target = target.replace('.', '')
    vm = vm.replace('.', '')
    cloudSettings = __salt__['mc_cloud.settings']()
    filep = os.path.join(
        cloudSettings['compute_node_pillar_dir'],
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


def get_snmp_port_end():
    return __salt__['mc_utils.get'](
        'makina-states.cloud.compute_node.snmp_start_port', '39999')


def get_snmp_port_start():
    return __salt__['mc_utils.get'](
        'makina-states.cloud.compute_node.snmp_start_port', 30000)

def get_ssh_port_end():
    return __salt__['mc_utils.get'](
        'makina-states.cloud.compute_node.ssh_start_port', '50000')


def get_ssh_port_start():
    return __salt__['mc_utils.get'](
        'makina-states.cloud.compute_node.ssh_start_port', 40000)


def _find_available_snmp_port(targets, target, data):
    ip = data['ip']
    ip_parts = ip.split('.')
    snmp_start_port = int(get_snmp_port_start())
    return (int(snmp_start_port) +
            (256 * int(ip_parts[2])) +
            int(ip_parts[3]))


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


def _configure_http_reverses(reversep, domain, ip):
    backend_name = 'bck_{0}'.format(domain)
    sbackend_name = 'securebck_{0}'.format(domain)
    # http
    http_proxy = reversep['http_proxy']
    https_proxy = reversep['https_proxy']
    rule = 'acl host_{0} hdr(host) -i {0}'.format(domain)
    if rule not in http_proxy['raw_opts']:
        http_proxy['raw_opts'].insert(0, rule)
        https_proxy['raw_opts'].insert(0, rule)
    rule = 'use_backend {1} if host_{0}'.format(domain, backend_name)
    if rule not in http_proxy['raw_opts']:
        http_proxy['raw_opts'].append(rule)
    # https
    sslr = 'http-request set-header X-SSL %[ssl_fc]'
    if sslr not in https_proxy['raw_opts']:
        https_proxy['raw_opts'].insert(0, sslr)
    rule = 'use_backend {1} if host_{0}'.format(domain, sbackend_name)
    if rule not in https_proxy['raw_opts']:
        https_proxy['raw_opts'].append(rule)
    # http/https raw rules
    for rule in reversed(https_proxy['raw_opts_pre']):
        https_proxy['raw_opts'].insert(0, rule)
    for rule in reversed(http_proxy['raw_opts_pre']):
        http_proxy['raw_opts'].insert(0, rule)
    for rule in https_proxy['raw_opts_post']:
        https_proxy['raw_opts'].append(rule)
    for rule in http_proxy['raw_opts_post']:
        http_proxy['raw_opts'].append(rule)
    _add_server_to_backend(reversep, backend_name, domain, ip)
    _add_server_to_backend(reversep, sbackend_name, domain, ip, kind='https')


def _init_http_proxies(target_data, reversep):
    http_proxy_mode = target_data.get('http_proxy_mode', 'xforwardedfor')
    reversep.setdefault(
        'http_proxy', {
            'name': reversep['target'],
            'mode': 'http',
            'http_proxy_mode': http_proxy_mode,
            'bind': '*:80',
            'raw_opts_pre': __salt__['mc_utils.get'](
                'makina-states.cloud.compute_node.conf.'
                '{0}.http_proxy.raw_opts_pre'.format(
                    reversep['target'])),
            'raw_opts_post': __salt__['mc_utils.get'](
                'makina-states.cloud.compute_node.conf.'
                '{0}.http_proxy.raw_opts_post'.format(
                    reversep['target'])),
            'raw_opts': []})

    ssl_bind = '*:443 ssl'
    if target_data['ssl_certs']:
        ssl_bind += (
            ' crt /etc/ssl/cloud/certs/{0}.crt'
            ' crt /etc/ssl/cloud/certs'
        ).format(reversep['target'])
    reversep.setdefault(
        'https_proxy', {
            'name': "secure-" + reversep['target'],
            'mode': 'http',
            'http_proxy_mode': http_proxy_mode,
            'raw_opts_pre': (
                __salt__['mc_utils.get'](
                    'makina-states.cloud.compute_node.conf.'
                    '{0}.https_proxy.raw_opts_pre'.format(
                        reversep['target']), [])),
            'raw_opts_post': __salt__['mc_utils.get'](
                'makina-states.cloud.compute_node.conf.'
                '{0}.https_proxy.raw_opts_post'.format(
                    reversep['target']), []),
            'bind': ssl_bind,
            'raw_opts': []})
    return reversep


def feed_http_reverse_proxy_for_target(target, target_data=None):
    '''Get reverse proxy information mapping for a specicific target
    This return a useful mappings of infos to reverse proxy http
    and ssh services with haproxy
    '''
    _s = __salt__.get
    if target_data is None:
        target_data = get_settings_for_target(target)
    reversep = _get_rp(target_data)
    _init_http_proxies(target_data, reversep)
    for vmname in target_data['vms']:
        vm = target_data['vms'][vmname]
        for domain in vm['domains']:
            _configure_http_reverses(reversep, domain, vm['ip'])
    return reversep


def _get_next_available_port(ports, start, stop):
    for i in range(start, stop + 1):
        if i not in ports:
            return i
    raise ValueError('mc_compute_node: No more available ssh port in'
                     '{0}:{1}'.format(start, stop))


def get_snmp_mapping_for_target(target, target_data=None):
    _s = __salt__.get
    if target_data is None:
        target_data = get_settings_for_target(target)
    mapping = {}
    vms_infos = target_data.get('vms', {})
    # generate or refresh ssh mappings
    for vm in vms_infos:
        mapping[vm] = _s('mc_cloud_compute_node.get_snmp_port')(
            target, vm, target_data=target_data)
    return mapping


def set_snmp_port(target, vm, port, target_data=None):
    if target_data is None:
        target_data = get_settings_for_target(target)
    ssh_map = get_conf_for_target(target, 'snmp_map', {})
    if ssh_map.get(vm, None) != port:
        ssh_map[vm] = port
        set_conf_for_target(target, 'snmp_map', ssh_map)
    return get_conf_for_target(target, 'snmp_map', {}).get(vm, None)


def cleanup_snmp_ports(target, target_data=None):
    '''This is a maintenance routine which can be called to cleanup
    ssh ports when range exhaustion is incoming'''
    if target_data is None:
        target_data = get_settings_for_target(target)
    vms_infos = target_data.get('vms', {})
    snmp_map = get_conf_for_target(target, 'snmp_map', {})
    # filter old vms grains
    need_sync = True
    for avm in [a for a in snmp_map]:
        if avm not in vms_infos:
            del snmp_map[avm]
            need_sync = True
    if need_sync:
        set_conf_for_target(target, 'snmp_map', snmp_map)
    return get_conf_for_target(target, 'snmp_map', {})


def get_snmp_port(vm, target=None, target_data=None):
    _s = __salt__.get
    _settings = settings()
    if target is None:
        target = __salt__['mc_cloud_compute_node.target_for_vm'](vm)
    if target_data is None:
        target_data = get_settings_for_target(target)
    vms_infos = target_data.get('vms', {})
    start = int(_settings['snmp_port_range_start'])
    end = int(_settings['snmp_port_range_end'])
    snmp_map = get_conf_for_target(target, 'snmp_map', {})
    for a in [a for a in snmp_map]:
        snmp_map[a] = int(snmp_map[a])
    port = snmp_map.get(vm, None)
    if port is None:
        if vm in vms_infos:
            port = _get_next_available_port(snmp_map.values(), start, end)
            _s('mc_cloud_compute_node.set_snmp_port')(
                target, vm, port, target_data=target_data)
        else:
            raise ValueError('{0} is not a vm of {1}'.format(vm, target))
    return port


def feed_sw_reverse_proxies_for_target(target, target_data=None):
    _s = __salt__.get
    _settings = settings()
    if target_data is None:
        target_data = get_settings_for_target(target)
    vms_infos = target_data.get('vms', {})
    reversep = _get_rp(target_data)
    sw_proxies = reversep.setdefault('sw_proxies', [])
    for vm, data in vms_infos.items():
        snmp_port = _s('mc_cloud_compute_node.get_snmp_port')(
            vm, target=target,
            target_data=target_data)
        ssh_port = _s('mc_cloud_compute_node.get_ssh_port')(
            vm, target=target,
            target_data=target_data)
        vt = 'lxc'
        sw_proxies.append({'comment': 'snmp for {0}'.format(vm)})
        sw_proxies.append({'action': 'DNAT',
                           'source': 'all',
                           'dest': '{1}:{0}:161'.format(data['ip'], vt),
                           'proto': 'udp', 'dport': snmp_port})
        sw_proxies.append({'comment': 'ssh {0}'.format(vm)})
        for i in ['tcp', 'udp']:
            sw_proxies.append({'action': 'DNAT',
                               'source': 'all',
                               'dest': '{1}:{0}:22'.format(data['ip'], vt),
                               'proto': i, 'dport': ssh_port})
    return reversep


def get_ssh_mapping_for_target(target, target_data=None):
    _s = __salt__.get
    if target_data is None:
        target_data = get_settings_for_target(target)
    mapping = {}
    vms_infos = target_data.get('vms', {})
    # generate or refresh ssh mappings
    for vm in vms_infos:
        mapping[vm] = _s('mc_cloud_compute_node.get_ssh_port')(
            target, vm, target_data=target_data)
    return mapping


def set_ssh_port(target, vm, port, target_data=None):
    if target_data is None:
        target_data = get_settings_for_target(target)
    ssh_map = get_conf_for_target(target, 'ssh_map', {})
    if ssh_map.get(vm, None) != port:
        ssh_map[vm] = port
        set_conf_for_target(target, 'ssh_map', ssh_map)
    return get_conf_for_target(target, 'ssh_map', {}).get(vm, None)


def cleanup_ssh_ports(target, target_data=None):
    '''This is a maintenance routine which can be called to cleanup
    ssh ports when range exhaustion is incoming'''
    if target_data is None:
        target_data = get_settings_for_target(target)
    vms_infos = target_data.get('vms', {})
    ssh_map = get_conf_for_target(target, 'ssh_map', {})
    # filter old vms grains
    need_sync = True
    for avm in [a for a in ssh_map]:
        if avm not in vms_infos:
            del ssh_map[avm]
            need_sync = True
    if need_sync:
        set_conf_for_target(target, 'ssh_map', ssh_map)
    return get_conf_for_target(target, 'ssh_map', {})


def get_ssh_port(vm, target=None, target_data=None):
    _s = __salt__.get
    _settings = settings()
    if target is None:
        target = __salt__['mc_cloud_compute_node.target_for_vm'](vm)
    if target_data is None:
        target_data = get_settings_for_target(target)
    vms_infos = target_data.get('vms', {})
    start = int(_settings['ssh_port_range_start'])
    end = int(_settings['ssh_port_range_end'])
    ssh_map = get_conf_for_target(target, 'ssh_map', {})
    for a in [a for a in ssh_map]:
        ssh_map[a] = int(ssh_map[a])
    port = ssh_map.get(vm, None)
    if port is None:
        if vm in vms_infos:
            port = _get_next_available_port(ssh_map.values(), start, end)
            _s('mc_cloud_compute_node.set_ssh_port')(
                target, vm, port, target_data=target_data)
        else:
            raise ValueError('{0} is not a vm of {1}'.format(vm, target))
    return port


def feed_ssh_reverse_proxies_for_target(target, target_data=None):
    _s = __salt__.get
    _settings = settings()
    if target_data is None:
        target_data = get_settings_for_target(target)
    vms_infos = target_data.get('vms', {})
    reversep = _get_rp(target_data)
    ssh_proxies = reversep.setdefault('ssh_proxies', [])
    for vm, data in vms_infos.items():
        port = _s('mc_cloud_compute_node.get_ssh_port')(
            vm, target=target,
            target_data=target_data)
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
    return reversep


def _add_vt_to_target(target, vt):
    vts = target.setdefault('virt_types', OrderedDict())
    default_has(vts, **{vt: False})


def get_settings_for_target(target, target_data=None):
    '''Return specific compute node related settings for a specific target

        target
            target name
        reverse_proxies
            mapping of reverse proxies info
        domains
            list of domains served by host
        virt_types
            virt types supported by the box.
            This is a mapping and the value is weither the virt type is
            enabled or not
        ssl_certs
            (certname, cert+key string) tuples
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
        target_data = {
            'ssl_certs': [],
        }
    target_data['target'] = target
    target_domains = target_data.setdefault('domains', [])
    vms = get_vms_per_type(target)
    for virt_type, vm_ids in vms.items():
        _add_vt_to_target(target_data, virt_type)
        target_data['virt_types'][virt_type] = True
        vms = target_data.setdefault('vms', OrderedDict())
        # TODO: make this configurable
        target_data['http_proxy_mode'] = 'xforwardedfor'
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
            for domain in vm_settings['domains']:
                if domain not in target_domains:
                    target_domains.append(domain)
            # link onto the host the vm infos
            target_data['vms'][vmname] = {
                'virt_type':  virt_type,
                'ip': ip,
                'domains': vm_settings['domains'],
                'vmname':  vm_settings['name']}
            if target_data.get('virt_type', '') in ['lxc', 'docker']:
                target_data['virt_types']['lxc'] = True
    domains = [target] + target_domains
    for cert, key in __salt__['mc_ssl.ssl_certs'](domains):
        certname = cert
        if certname.endswith('.crt'):
            certname = os.path.basename(certname)[:-4]
        if certname.endswith('.bundle'):
            certname = os.path.basename(certname)[:-7]
        fullcert = ''
        for f in [cert, key]:
            with open(f) as fic:
                fullcert += fic.read()
        if fullcert not in [a[1] for a in target_data['ssl_certs']]:
            target_data['ssl_certs'].append((certname, fullcert))
    target_data['firewall'] = get_firewall_toggle()
    feed_http_reverse_proxy_for_target(target, target_data)
    feed_ssh_reverse_proxies_for_target(target, target_data)
    feed_sw_reverse_proxies_for_target(target, target_data)
    return target_data


def get_shorewall_reverse_proxies_for_target(target):
    '''Get reverse proxy information mapping for a specicific target
    See feed_reverse_proxy_for_target'''
    target_data = get_settings_for_target(target)
    return dict([(k, target_data[k]) for k in target_data
                 if k in (_RP, 'target')])

def get_reverse_proxies_for_target(target):
    '''Get reverse proxy information mapping for a specicific target
    See feed_reverse_proxy_for_target'''
    target_data = get_settings_for_target(target)
    return dict([(k, target_data[k]) for k in target_data
                 if k in (_RP, 'target')])


def cn_settings(ttl=60):
    '''
    compute node related settings
    THIS IS USED ON THE COMPUTE NODE SIDE !
    '''
    def _do():
        reg = __salt__['mc_macros.get_local_registry'](
            'cloud_compute_node_settings',
            registry_format='pack')
        if 'cnSettings' not in reg:
            raise ValueError(
                'Registry not yet configured')
        return reg
    cache_key = 'mc_cloud_compute_node.cn_settings'
    return memoize_cache(_do, [], {}, cache_key, ttl)


def settings():
    '''
    compute node related settings
    THIS IS USED ON THE CONTROLLER SIDE !

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
    # TODO: reenable cache
    #@mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        data = _s['mc_utils.defaults'](
            'makina-states.cloud.compute_node', {
                'has': {'firewall': get_firewall_toggle()},
                'ssh_port_range_start': get_ssh_port_start(),
                'ssh_port_range_end': get_ssh_port_end(),
                'snmp_port_range_start': get_snmp_port_start(),
                'snmp_port_range_end': get_snmp_port_end(),
                'targets': get_vms()
            })
        return data
    res = _settings()
    return res


def is_compute_node():
    _settings = settings()
    return __salt__['mc_utils.get']('makina-states.cloud.is.compute_node')


def get_targets_and_vms_for_virt_type(virt_type):
    _s = __salt__
    virtsettings = _s['mc_cloud_{0}.settings'.format(virt_type)]()
    vtargets = virtsettings.get('vms', {})
    return vtargets


def targets():
    '''Get all configured compute nodes'''
    _s = __salt__
    _settings = settings()
    return dict([(a, v.get('virt_types', []))
                 for a, v in _settings['targets'].items()])


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


def get_vm(vm):
    for target, data in get_vms().items():
        vt = data.get('vms', {}).get(vm, None)
        if vt:
            vm = {'target': target, 'vt': vt}
            return vm
    raise KeyError('{0} vm not found'.format(vm))


def get_vms_for_target(target):
    '''Return all vms for a target'''
    return get_vms().get(target, {}).get('vms', [])


def dump():
    return mc_states.utils.dump(__salt__,__name)

# vim:set et sts=4 ts=4 tw=80:
