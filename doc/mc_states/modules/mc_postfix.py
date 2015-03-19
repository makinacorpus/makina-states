# -*- coding: utf-8 -*-
'''
.. _module_mc_postfix:

mc_postfix / postfix functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.api

from salt.utils.odict import OrderedDict

__name = 'postfix'

log = logging.getLogger(__name__)


def settings():
    '''
    postfix settings

    mode
        one of

            custom
                custom mode, specific explictly your options
            relay
                satellite mode
            localdeliveryonly
                mails are only delivered locally, no email
                are sent on the network

    use_tls
        do we use tls ('yes')
    inet_protocols
        which protocol to enable ('ipv4')
    check_policy_service
        content filtering service (None)
    conf_dir
        main configuration directory (/etc) (locs['conf_dir'])
    mailname
        this server address to use in recipien/exp. (grains['fqdn'])
    cert_file
        ssl cert file if any ('{conf_dir}/ssl/certs/ssl-cert-snakeoil.pem')
    cert_key
        ssl cert key if any ('{conf_dir}/ssl/private/ssl-cert-snakeoil.key')
    inet_interfaces
        where to bind('all')
    mailbox_size_limit
        size max of the mailbox(0)
    auth
        enable smtp auth
    mynetworks
        list of hosts/nets to add to mynetworks
    relay_domains
        Mapping {relaydomain: action}
    transports
        list of mappings {transport:'', 'nexthop': ''}
        default transport is '*'.
        This can be used to make a satellite
    virtual_map
        dict of key/value pair to feed the virtual table
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locs = __salt__['mc_locations.settings']()
        local_networks = ['127.0.0.0/8',
                          '[::ffff:127.0.0.0]/104',
                          '[::1]/128',]
        for iface, ips in grains['ip_interfaces'].items():
            for ip in ips:
                net = '.'.join(ip.split('.')[:3]) + '.0/'
                netm = '24'
                if net.startswith('10'):
                    netm = '16'
                if net.startswith('127.0'):
                    netm = '8'
                net += netm
                if net not in local_networks:
                    local_networks.append(net)
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.mail.postfix', {
                'use_tls': 'yes',
                'inet_protocols': 'ipv4',
                #'check_policy_service': 'inet:127.0.0.1:10023',
                'check_policy_service': None,
                'conf_dir': locs['conf_dir'],
                'mailname': __salt__['mc_network.settings']()['fqdn'],
                'cert_file': '{conf_dir}/ssl/certs/ssl-cert-snakeoil.pem',
                'cert_key': '{conf_dir}/ssl/private/ssl-cert-snakeoil.key',
                'smtp_auth': True,
                'smtpd_auth': True,
                'inet_interfaces': None,
                'mode': '',
                'virtual_mailbox_base': '/var/mail/virtual',
                'mailbox_size_limit': 0,
                'mynetworks': local_networks,
                'mydestination': OrderedDict(),
                'append_dot_mydomain': 'no',
                'relay_domains': OrderedDict(),
                'sasl_passwd': [],
                'transport': [],
                'virtual_map': [],
                'local_dest': 'root',
            }
        )
        if nodetypes_registry['is']['devhost']:
            data['local_dest'] = 'vagrant@localhost'
            data['mode'] = 'localdeliveryonly'
        if data['mode'] in ['redirect']:
            data['virtual_map'].insert(
                0, {'/.*/':  data['local_dest']})
        if data['mode'] in ['localdeliveryonly']:
            data['virtual_map'].insert(
                0, {'/.*/': 'root@localhost'})
        for h in [
            'localhost.local',
            'localhost',
            data['mailname'],
            __grains__['fqdn'],
        ]:
            if data['mode'] == 'relay':
                data['mydestination'] = {}
                if h not in data['relay_domains']:
                    data['relay_domains'][h] = 'OK'
            else:
                if h not in data['mydestination']:
                    data['mydestination'][h] = 'OK'
        if data['inet_interfaces'] is None:
            if data['mode'] in ['localdeliveryonly',
                                'redirect',
                                'relay']:
                data['inet_interfaces'] = '127.0.0.1'
            else:
                data['inet_interfaces'] = 'all'
        return data
    return _settings()



#
