#!/usr/bin/env python
'''
.. _module_mc_cloud_controller:

mc_cloud_compute_node / cloudcontroller functions
=================================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import yaml
import mc_states.utils

__name = 'mc_cloud_compute_node'

log = logging.getLogger(__name__)


def find_avalaible_port(targets, target):
    ssh_start_port = int(
        __salt__['mc_utils.get'](
            'makina-states.services.'
            'cloud.cloudcontroller.'
            'ssh_start_port', 40000)
    )
    (int(ssh_start_port) +
     (256 * int(ip_parts[2])) +
     int(ip_parts[3]))


def get_lxc_vm_settings(targets):
    return targets
    lxc = __salt__['mc_lxc.settings']()
    for target, tdata in lxc['vm'].iteritems():
        for dns, data in tdata.iteritems():
            targets[target][data['name']] = {
                'ip':  data['iap'],
                'dns':  data['name'],
            }


def get_reverse_proxies(reverse_proxies, targets):
    return reverse_proxies, targets
    for target, tdata in targets.iteritems():
        ssh_proxies = []
        https_backends = []
        http_backends = []
        http_proxy = {'name': target,
            'mode': 'http',
            'bind': '*:80',
            'raw_opts': [],
        }
        https_proxy = {
            'name': "secure-" + target,
            'mode': 'http',
            'bind': '*:443',
            'raw_opts': []}
        for dns, data in tdata.iteritems():

            ip = data['ip']
            dns = data.get('name', dns)
            http_proxy['raw_opts'].insert(
                0, 'acl host_{0} hdr(host) -i {0}'.format(dns))
            http_proxy['raw_opts'].append(
                'use_backend bck_{0} if host_{0}'.format(dns)
            )
            http_backends.append({
                'name': 'bck_{0}'.format(dns),
                'servers': [
                    {'name': 'bck_{0}1'.format(dns),
                     'bind': '{0}:80'.format(ip),
                     'opts': 'check'},
                ]})
            https_proxy['raw_opts'].insert(
                0, 'acl host_{0} hdr(host) -i {0}'.format(dns),
            )
            https_proxy['raw_opts'].append(
                'use_backend securebck_{0} if host_{0}'.format(dns),
            )
            https_backends.append({
                'name': 'securebck_{0}'.format(dns),
                'servers': [
                    {'name': 'bck_{0}1'.format(dns),
                     'bind': '{0}:443'.format(ip),
                     'opts': 'check'},
                ]})
            ip_parts = ip.split('.')
            ssh_port = find_avalaible_port(targets, target)
            ssh_proxies.extend([{
                'name': 'lst_{0}'.format(dns),
                'bind': ':{0}'.format(ssh_port),
                'mode': 'tcp',
                'raw_opts': [],
                'servers': [{
                    'name': 'sshserver',
                    'bind': '{0}:22'.format(ip),
                    'opts': 'check',
                }]}])
            targets[target] = {
                'ssh_proxies': ssh_proxies,
                'http_proxy': http_proxy,
                'https_proxy': https_proxy,
                'https_backends': https_backends,
                'http_backends': http_backends,
            }
    return targets, current_port


def settings():
    '''
    compute node related settings

    Basically the compute node needs to:

        - setup reverse proxying
        - setup it's local dns to point to private ips

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        targets, reverse_proxies = {}, {}
        targets = get_lxc_vm_settings(targets)
        reverse_proxies = get_reverse_proxies(reverse_proxies, targets)
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.cloud.compute_node', {
                'targets': targets,
                'reverse_proxies': reverse_proxies,
            }
        )
        return data
    return _settings()

def dump():
    return mc_states.utils.dump(__salt__,__name)

#
# vim:set et sts=4 ts=4 tw=80:
