# -*- coding: utf-8 -*-
'''
.. _module_mc_postfix:

mc_postfix / postfix functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

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
    mynetworks
        which network to use (local_networks)
    auth
        If true, enable SMTPD authentication via
        virtual map (relay mode) (False)
    auth_user
        auth user for smtpd authentication
    auth_password':
        auth password for smtpd authentication
    relay_host
        relay host if any
    relay_port
        relay host port if any
    virtual_map
        dict of key/value pair to feed the virtual table
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locs = __salt__['mc_locations.settings']()
        local_networks = ['127.0.0.0/8',
                          '[::ffff:127.0.0.0]/104',
                          '[::1]/128',
                          '{{ local_networks }}']
        for iface, ips in grains['ip_interfaces'].items():
            for ip in ips:
                net = '.'.join(ip.split('.')[:3]) + '.0/24'
                if not net in local_networks:
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.mail.postfix', {
                'use_tls': 'yes',
                'inet_protocols': 'ipv4',
                #'check_policy_service': 'inet:127.0.0.1:10023',
                'check_policy_service': None,
                'inet_interfaces': '127.0.0.1',
                'conf_dir': locs['conf_dir'],
                'mailname': __salt__['mc_network.settings']()['fqdn'],
                'cert_file': '{conf_dir}/ssl/certs/ssl-cert-snakeoil.pem',
                'cert_key': '{conf_dir}/ssl/private/ssl-cert-snakeoil.key',
                'inet_interfaces': 'all',
                'mode': 'localdeliveryonly',
                'mailbox_size_limit': 0,
                'mynetworks': local_networks,
                'mydestination': OrderedDict(),
                'auth': False,
                'auth_user': 'foo',
                'auth_password': 'secret',
                'append_dot_mydomain': 'no',
                'relay_domains': OrderedDict(),
                'sasl_passwd ': [],
                'transport': [],
                'virtual_map': OrderedDict(),
                'local_dest': 'root@localhost',
            }
        )
        if nodetypes_registry['is']['devhost']:
            data['local_dest'] = 'vagrant@localhost'
        if data['mode'] in ['localdeliveryonly']:
            data['virtual_map']['/.*/'] = data['local_dest']
        for h in [
            'localhost.local',
            'localhost',
            data['mailname']
            __grains__['fqdn'],
        ]:
            if data['mode'] == 'relay':
                data['mydestinations'] = {}
                if h not in data['relay_domains']:
                    data['relay_domains'][h] = 'OK'
            else:
                if h not in data['mydestinations']:
                    data['mydestinations'][h] = 'OK'
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
