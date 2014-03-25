#!/usr/bin/env python
'''
.. _module_mc_cloud_compute_node:

mc_cloud_compute_node / cloudcontroller functions
=================================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import socket
import os
import yaml
import mc_states.utils
from salt.utils.odict import OrderedDict

from mc_states import api

__name = 'mc_cloud_compute_node'

log = logging.getLogger(__name__)

VIRT_TYPES = {
    'lxc': {}
}

def default_has(vts=None, **kwargs):
    if vts is None:
        vts = {}
    for vt in VIRT_TYPES:
        vts.setdefault(vt, bool(kwargs.get(vt, False)))
    return vts


def get_firewall_toggle():
    return __salt__['mc_utils.get'](
        'makina-states.cloud.compute_node.has.firewall', True)


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


def _add_vt_to_target(target, vt):
    vts = target.setdefault('virt_types', OrderedDict())
    default_has(vts, **{vt: False})


def _feed_settings_from_virt_modules(targets):
    # iterate over all supported vts
    for virt_type, mtdata in VIRT_TYPES.items():
        vt = __salt__['mc_cloud_{0}.settings'.format(virt_type)]()
        for target, tdata in vt['vms'].items():
            # implicitly create host target
            targets.setdefault(target, OrderedDict())
            #targets[targets].setdefault('has', OrderedDict())
            _add_vt_to_target(targets[target], virt_type)
            # link onto the host the vm infos
            for dns, data in tdata.items():
                dns = data.get('name', dns)
                targets[target].setdefault('vms', OrderedDict())
                targets[target]['vms'][data['name']] = {
                    'virt_type':  virt_type,
                    'ip':  data['ip'],
                    'domains':  data['domains'],
                    'dns':  data['name']}
                if data.get('virt_type', '') in ['lxc', 'docker']:
                    targets[targets]['virt_types']['lxc'] = True
    return targets


def _feed_firewall_settings(targets):
    for target, cdata in targets.items():
        cdata['firewall'] = get_firewall_toggle()


def _configure_http_reverse(main_domain,
                            ip,
                            http_proxy,
                            https_proxy,
                            http_backends,
                            https_backends,
                            domain=None):
    if not domain:
        domain = main_domain
    rule = 'acl host_{0} hdr(host) -i {0}'.format(domain)
    if not rule in http_proxy['raw_opts']:
        http_proxy['raw_opts'].insert(0, rule)
        https_proxy['raw_opts'].insert(0, rule)
    rule = 'use_backend bck_{1} if host_{0}'.format(domain, main_domain)
    if not rule in http_proxy['raw_opts']:
        http_proxy['raw_opts'].append(rule)
    rule = 'use_backend securebck_{1} if host_{0}'.format(domain, main_domain)
    if not rule in https_proxy['raw_opts']:
        https_proxy['raw_opts'].append(rule)
    bck = {
        'name': 'bck_{0}'.format(main_domain),
        'servers': [
            {'name': 'bck_{0}1'.format(main_domain),
             'bind': '{0}:80'.format(ip),
             'opts': 'check'}]}
    if not bck in http_backends:
        http_backends.append(bck)
    bck = {'name': 'securebck_{0}'.format(main_domain),
           'servers': [
               {'name': 'bck_{0}1'.format(main_domain),
                'bind': '{0}:443'.format(ip),
                'opts': 'check'}]}
    if not bck in https_backends:
        https_backends.append(bck)


def _feed_reverse_proxies_settings(targets):
    _s = __salt__.get
    for target, cdata in targets.items():
        http_proxy = cdata.setdefault('http_proxy',
                                      {'name': target,
                                       'mode': 'http',
                                       'bind': '*:80',
                                       'raw_opts': []})
        https_proxy = cdata.setdefault('https_proxy',
                                       {'name': "secure-" + target,
                                        'mode': 'http',
                                        'bind': '*:443',
                                        'raw_opts': []})
        https_backends = cdata.setdefault('https_backends', [])
        http_backends = cdata.setdefault('http_backends', [])
        vms_infos = cdata.get('vms', {}).items()
        for vm, data in vms_infos:
            ip = data['ip']
            main_domain = data['domains'][0]
            domains = data['domains']
            for domain in domains:
                _configure_http_reverse(
                    main_domain, ip, http_proxy, https_proxy,
                    http_backends, https_backends, domain=domain)


def _get_next_available_port(ports, start, stop):
    for i in range(start, stop + 1):
        if not i in ports:
            return i
    raise ValueError('mc_compute_node: No more available ssh port')


def _feed_ssh_reverse_proxy(targets, start, end):
    _s = __salt__.get
    mkey = 'makina-states.cloud.ssh-mappings'
    ssh_maps = _s('mc_utils.get')(mkey, {})
    for target, cdata in targets.items():
        vms_infos = cdata.get('vms', {})
        ssh_proxies = cdata.setdefault('ssh_proxies', [])
        for a in [a for a in ssh_maps]:
            ssh_maps[a] = int(ssh_maps[a])
        # filter old vms grains
        for avm in [a for a in ssh_maps]:
            if not avm in vms_infos:
                del ssh_maps[avm]
        for vm, data in vms_infos.items():
            port = ssh_maps.get(vm, None)
            if not port:
                port = _get_next_available_port(ssh_maps.values(), start, end)
                ssh_maps[vm] = port
            ssh_proxy = {
                'name': 'lst_{0}'.format(data['domains'][0]),
                'bind': ':{0}'.format(data['ip']),
                'mode': 'tcp',
                'raw_opts': [],
                'servers': [{
                    'name': 'sshserver',
                    'bind': '{0}:22'.format(data['ip']),
                    'opts': 'check'}]}
            if not ssh_proxy in ssh_proxies:
                ssh_proxies.append(ssh_proxy)
    _s('grains.setval')(mkey, ssh_maps)
    _s('saltutil.sync_grains')()
    return ssh_maps


def settings():
    '''
    compute node related settings

    targets
        all registered compute nodes information
    has
        global configuration toggle

        firewall
            global firewall toggle

    ssh_port_range_start
        from where we start to enable ssh NAT ports

    ssh_port_range_end

        from where we end to enable ssh NAT ports

    Basically the compute node needs to:

        - setup reverse proxying
        - setup it's local internal addressing dns to point to private ips
        - everything else that's local to the compute node

    The computes nodes are often created implicitly by registration of vms
    on specific drivers like LXC but you can register some manually.

    Eg:

    makina-states.cloud.compute_node.settings.targets.devhost11.local: {}

    To add or modify a value, use the mc_utils.default habitual way of
    modifying the default dict.
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        targets = OrderedDict()
        _feed_settings_from_virt_modules(targets)
        _feed_reverse_proxies_settings(targets)
        _feed_firewall_settings(targets)
        data = __salt__['mc_utils.defaults'](
            'makina-states.cloud.compute_node', {
                'has': {
                    'firewall': True,
                },
                'ssh_port_range_start': '40000',
                'ssh_port_range_end': '48000',
                'targets': targets,
            })
        data['ssh_map'] = _feed_ssh_reverse_proxy(
            targets,
            int(data['ssh_port_range_start']),
            int(data['ssh_port_range_end']))
        return data
    return _settings()


def is_compute_node():
    _settings = settings()
    return __salt__['mc_utils.get']('id') in _settings['targets']


def dump():
    return mc_states.utils.dump(__salt__,__name)

# vim:set et sts=4 ts=4 tw=80:
