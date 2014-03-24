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


def find_avalaible_port(targets, target, data):
    ip = data['ip']
    ip_parts = ip.split('.')
    ssh_start_port = int(get_ssh_port_start())
    return (int(ssh_start_port) +
            (256 * int(ip_parts[2])) +
            int(ip_parts[3]))


def add_vt_to_target(target, vt):
    vts = target.setdefault('virt_types', OrderedDict())
    default_has(vts, **{vt: True})


def feed_settings_from_virt_modules(targets):
    # iterate over all supported vts
    for virt_type, mtdata in VIRT_TYPES.iteritems():
        vt = __salt__['mc_cloud_{0}.settings'.format(virt_type)]()
        for target, tdata in vt['vms'].iteritems():
            # implicitly create host target
            targets.setdefault(target, OrderedDict())
            add_vt_to_target(targets[target], 'lxc')
            # link onto the host the vm infos
            for dns, data in tdata.iteritems():
                dns = data.get('name', dns)
                targets.setdefault(target['vms'], OrderedDict())
                targets[target]['vms'][data['name']] = {
                    'ip':  data['ip'],
                    'dns':  data['name']}
    return targets


def feed_firewall_settings(targets):
    for target, cdata in targets.iteritems():
        cdata['firewall'] = get_firewall_toggle()


def feed_reverse_proxies_settings(targets):
    for target, cdata in targets.iteritems():
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
        ssh_proxies = cdata.setdefault('ssh_proxies',
                                       'ssh_proxies', [])
        https_backends = cdata.setdefault('https_backends', [])
        http_backends = cdata.setdefault('http_backends', [])
        for vm, tdata in cdata.get('vms', {}).iteritems():
            for dns, data in tdata.iteritems():
                ip = data['ip']
                dns = data['dns']
                http_proxy['raw_opts'].insert(
                    0, 'acl host_{0} hdr(host) -i {0}'.format(dns))
                http_proxy['raw_opts'].append(
                    'use_backend bck_{0} if host_{0}'.format(dns))
                http_backends.append({
                    'name': 'bck_{0}'.format(dns),
                    'servers': [
                        {'name': 'bck_{0}1'.format(dns),
                         'bind': '{0}:80'.format(ip),
                         'opts': 'check'}]})
                https_proxy['raw_opts'].insert(
                    0, 'acl host_{0} hdr(host) -i {0}'.format(dns))
                https_proxy['raw_opts'].append(
                    'use_backend securebck_{0} if host_{0}'.format(dns))
                https_backends.append({
                    'name': 'securebck_{0}'.format(dns),
                    'servers': [
                        {'name': 'bck_{0}1'.format(dns),
                         'bind': '{0}:443'.format(ip),
                         'opts': 'check'}]})
                ssh_port = find_avalaible_port(targets, target, data)
                ssh_proxies.extend([{
                    'name': 'lst_{0}'.format(dns),
                    'bind': ':{0}'.format(ssh_port),
                    'mode': 'tcp',
                    'raw_opts': [],
                    'servers': [{
                        'name': 'sshserver',
                        'bind': '{0}:22'.format(ip),
                        'opts': 'check'}]}])


def settings():
    '''
    compute node related settings

    targets
        all registered compute nodes information
    has
        global configuration toggle

        firewall
            global firewall toggle

    ssh_start_port

        from where we start to enable ssh NAT ports

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
        feed_settings_from_virt_modules(targets)
        feed_reverse_proxies_settings(targets)
        feed_firewall_settings(targets)
        data = __salt__['mc_utils.defaults'](
            'makina-states.cloud.compute_node', {
                'has': {
                    'firewall': get_ssh_port_start(),
                },
                'ssh_start_port': get_ssh_port_start(),
                'targets': targets,
            })
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

# vim:set et sts=4 ts=4 tw=80:
