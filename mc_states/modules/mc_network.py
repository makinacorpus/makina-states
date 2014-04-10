#!/usr/bin/network python
# -*- coding: utf-8 -*-
'''

.. _module_mc_network:

mc_network / network registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_network

'''
# Import python libs
import logging
import mc_states.utils
import re

__name = 'network'

log = logging.getLogger(__name__)


def sort_ifaces(infos):
    a = infos[0]
    key = a
    if re.match('^(eth0)', key):
        key = '100___' + a
    if re.match('^(eth[123456789][0123456789]+\|em|wlan)', key):
        key = '200___' + a
    if re.match('^(lxc\|docker)', key):
        key = '300___' + a
    if re.match('^(veth\|lo)', key):
        key = '900___' + a
    return key


def settings():
    '''
    network registry

    networkManaged
        Do we manage the network configuration
    networkInterfaces
        Dict of configuration for network interfaces
    main_ip
      main server ip
    hostname
      main hostname
    domain
      main domain
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        pillar = __pillar__
        networkInterfaces = {}
        data = {'networkInterfaces': networkInterfaces}
        grainsPref = 'makina-states.localsettings.'
        # lxc configuration has the network configuration inlined in the state
        # and not in pillar
        # it can be also done for other states like this
        for k in pillar:
            if k.endswith('makina-network'):
                networkInterfaces.update(pillar[k])
        # Does the network base config file have to be managed via that
        # See makina-states.localsettings.network
        # Compat for the first test!
        data['networkManaged'] = (
            saltmods['mc_utils.get']('makina-states.network_managed', False)
            or saltmods['mc_utils.get'](grainsPref + 'network.managed', False))

        # ip managment
        default_ip = None
        ifaces = grains['ip_interfaces'].items()
        ifaces.sort(key=sort_ifaces)
        devhost_ip = None
        for iface, ips in ifaces:
            if ips:
                if not default_ip:
                    default_ip = ips[0]
                if iface == 'eth1':
                    devhost_ip = ips[0]
        if not default_ip:
            default_ip = '127.0.0.1'
        # hosts managment via pillar
        data['makinahosts'] = makinahosts = []
        # main hostname
        domain_parts = grains['id'].split('.')
        data['devhost_ip'] = devhost_ip
        data['main_ip'] = saltmods['mc_utils.get'](
            grainsPref + 'main_ip', default_ip)
        data['hostname'] = saltmods['mc_utils.get'](
            grainsPref + 'hostname', domain_parts[0])
        default_domain = ''
        if len(domain_parts) > 1:
            default_domain = '.'.join(domain_parts[1:])
        data['domain'] = saltmods['mc_utils.get'](
            grainsPref + 'domain', default_domain)
        data['fqdn'] = saltmods['mc_utils.get']('nickname', grains['id'])
        if data['domain']:
            data['makinahosts'].append({
                'ip': '{main_ip}'.format(**data),
                'hosts': '{hostname} {hostname}.{domain}'.format(**data)
            })
        data['hosts_list'] = hosts_list = []
        for k, edata in pillar.items():
            if k.endswith('makina-hosts'):
                makinahosts.extend(edata)
        # -loop to create a dynamic list of hosts based on pillar content
        for host in makinahosts:
            ip = host['ip']
            for dnsname in host['hosts'].split():
                hosts_list.append(ip + ' ' + dnsname)
        netdata = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.network', data)
        return netdata
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
