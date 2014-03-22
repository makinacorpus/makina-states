# -*- coding: utf-8 -*-
'''
.. _module_mc_cloudcontroller:

mc_cloudcontroller / cloudcontroller functions
==============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import yaml
import mc_states.utils

__name = 'cloudcontroller'

log = logging.getLogger(__name__)


def settings():
    '''
    cloudcontroller settings

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        services_registry = __salt__['mc_services.registry']()
        lxc = __salt__['mc_lxc.settings']()

        ssh_start_port = int(
            __salt__['mc_utils.get'](
                'makina-states.services.'
                'cloud.cloudcontroller.'
                'ssh_start_port', 40000)
        )

        targets = {}
        for target, tdata in lxc['containers'].iteritems():
            ssh_proxies = []
            https_backends = []
            http_backends = []
            http_proxy = {
                'name': target,
                'mode': 'http',
                'bind': '*:80',
                'raw_opts': [],
            }
            https_proxy = {
                'name': "secure-" + target,
                'mode': 'http',
                'bind': '*:443',
                'raw_opts': [],
            }
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
                ssh_port = (int(ssh_start_port) +
                            (256 * int(ip_parts[2])) +
                            int(ip_parts[3]))
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
                    'haproxy': {
                        'ssh_proxies': ssh_proxies,
                        'http_proxy': http_proxy,
                        'https_proxy': https_proxy,
                        'https_backends': https_backends,
                        'http_backends': http_backends,
                    }
                }
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.firewall.cloudcontroller', {
                'targets': targets
            }
        )
        return data
    return _settings()

def dump():
    return mc_states.utils.dump(__salt__,__name)

#
