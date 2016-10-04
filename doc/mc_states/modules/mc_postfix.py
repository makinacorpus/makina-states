# -*- coding: utf-8 -*-
'''
.. _module_mc_postfix:

mc_postfix / postfix functions
============================================
'''

# Import python libs
import logging
import mc_states.api

from salt.utils.odict import OrderedDict

__name = 'postfix'
PREFIX = 'makina-states.services.mail.{0}'.format(__name)
six = mc_states.api.six
log = logging.getLogger(__name__)



def select_networks(data=None):
    _g = __grains__
    data = mc_states.api.param_as_list(data, 'mynetworks')
    data = mc_states.api.param_as_list(data, 'inet_protocols')
    data = mc_states.api.param_as_list(data, 'local_networks')
    protos = data['inet_protocols']
    local_networks = data['local_networks']
    if not data['no_local']:
        for iface, ips in _g['ip_interfaces'].items():
            for ip in ips:
                net = ip
                if '/' not in net:
                    net = __salt__['mc_network.append_netmask'](net)
                if net not in local_networks:
                    local_networks.append(net)
        if (
            'ipv6' in protos or 'any' in protos
        ):
            local_networks.append(
                ['[::ffff:127.0.0.0]/104',
                 '[::1]/128'])
        data['mynetworks'].extend(data['local_networks'])
    data['mynetworks'] = __salt__['mc_utils.uniquify'](data['mynetworks'])
    for ix, i in enumerate(data['mynetworks'][:]):
        if ':' in i and '[' not in i:
            ip = '[{0}]'.format(i)
            if '/' in i:
                ip, netm = i.split('/', 2)
                ip = '[{0}]'.format(ip)
            else:
                netm = '128'
            data['mynetworks'][ix] = '{0}/{1}'.format(ip, netm)
    return data


def select_mode(data):
    nodetypes_registry = __salt__['mc_nodetypes.registry']()
    if __salt__['mc_nodetypes.is_devhost']() and not data['mode']:
        data['mode'] = 'localdeliveryonly'
    data['mode'] = {
        'localdeliveryonly': 'localdeliveryonly',
        'relay': 'relay',
        'custom': 'custom',
        'catchall': 'catchall',
        'redirect': 'catchall'}.get(data['mode'], 'localdeliveryonly')
    return data


def select_catchall(data):
    nodetypes_registry = __salt__['mc_nodetypes.registry']()
    if data['catchall'] is None:
        if __salt__['mc_nodetypes.is_devhost']():
            data['catchall'] = 'vagrant@localhost'
        elif data['mode'] in ['localdeliveryonly']:
            data['catchall'] = 'root@localhost'
    if data['catchall']:
        data['virtual_map'].insert(0, {'/.*/':  data['catchall']})
    return data


def select_interfaces(data):
    if not data['inet_interfaces']:
        data['inet_interfaces'] = []
    if isinstance(data['inet_interfaces'], six.string_types):
        data['inet_interfaces'] = data['inet_interfaces'].split()
    if not data['inet_interfaces']:
        if data['mode'] in ['localdeliveryonly', 'redirect', 'relay']:
            data['inet_interfaces'] = ['127.0.0.1']
        else:
            data['inet_interfaces'] = ['all']
    data['inet_interfaces'] = __salt__['mc_utils.uniquify'](
        data['inet_interfaces'])
    return data


def select_dests_and_relays(data):
    _g = __grains__
    for h in [
        'localhost.local',
        'localhost',
        data['mailname'],
        _g['fqdn'],
    ]:
        if data['mode'] == 'relay':
            if h not in data['relay_domains']:
                data['relay_domains'][h] = 'OK'
        else:
            if h not in data['mydestination']:
                data['mydestination'][h] = 'OK'
    if data['mode'] == 'relay':
        for i in data['relay_domains']:
            if i in data['mydestination']:
                data['mydestination'].pop(i, None)
    return data


def select_certs(data):
    if not data['cert'] or not data['cert_key']:
        lcert, lkey, lchain = __salt__[
            'mc_ssl.get_configured_cert'](data['domain'],
                                          gen=True,
                                          selfsigned=True)
        data['cert'] = "{0}\n{1}\n".format(lcert, lchain or '')
        data['cert_key'] = lkey
    return data


def settings():
    '''
    postfix settings

    mode

        custom
            custom mode, specific explictly all your options
        relay
            satellite mode
        localdeliveryonly
            mails are only delivered locally, no email
            are sent on the network (default)

    catchall
        redirect all mail to this user if set
        if localdelivery is enabled, all mail are redirected to one user
        user is root, guest or nobody
        if catchall is False, no catchall will happen
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
    cert
        ssl certificate content including all the chain of certification
        Will use mc_ssl based on mailname instead
    cert_key
        ssl certificate key
        Will use mc_ssl based on mailname instead
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
        _s = __salt__
        _g = __grains__
        domain = _s['mc_network.settings']()['fqdn']
        data = _s['mc_utils.defaults'](
            PREFIX, {
                'use_tls': 'yes',
                'domain': domain,
                'no_local': False,
                # 'check_policy_service': 'inet:127.0.0.1:10023',
                'check_policy_service': None,
                'conf_dir': '/etc',
                'mailname': '{domain}',
                'hashtables': ['virtual_alias_maps', 'networks',
                               'sasl_passwd', 'relay_domains',
                               'recipient_access',
                               'transport', 'destinations'],
                'extra_confs': {
                    '/usr/bin/ms_resetpostfixperms.sh': {
                        'user': 'root', 'group': 'root',
                        'mode': '750'},
                    '/etc/postfix/virtual_alias_maps': {
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/networks': {
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/recipient_access': {
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/recipient_access.local': {
                        'user': 'root', 'group': 'postfix',
                        'source': '',
                        'mode': '640'},
                    '/etc/postfix/sasl_passwd': {
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/relay_domains': {
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/transport': {
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/destinations': {
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/virtual_alias_maps.local': {
                        'source': '',
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/networks.local': {
                        'user': 'root', 'group': 'postfix',
                        'source': '',
                        'mode': '640'},
                    '/etc/postfix/sasl_passwd.local': {
                        'user': 'root', 'group': 'postfix',
                        'source': '',
                        'mode': '640'},
                    '/etc/postfix/relay_domains.local': {
                        'user': 'root', 'group': 'postfix',
                        'source': '',
                        'mode': '640'},
                    '/etc/postfix/transport.local': {
                        'user': 'root', 'group': 'postfix',
                        'source': '',
                        'mode': '640'},

                    '/etc/postfix/certificate.pub': {
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/certificate.key': {
                        'user': 'root', 'group': 'postfix',
                        'mode': '640'},
                    '/etc/postfix/destinations.local': {
                        'user': 'root', 'group': 'postfix',
                        'source': '',
                        'mode': '640'},
                },
                'mydestination_param': (
                    'hash:/etc/postfix/destinations,'
                    'hash:/etc/postfix/destinations.local'),
                'relay_domains_param': (
                    'hash:/etc/postfix/relay_domains,'
                    'hash:/etc/postfix/relay_domains.local'),
                'mynetworks_param': (
                    'cidr:/etc/postfix/networks,'
                    'cidr:/etc/postfix/networks.local'),
                'transport_maps_param': (
                    'hash:/etc/postfix/transport,'
                    'hash:/etc/postfix/transport.local'),
                'local_recipient_maps_param': None,
                'cert': None,
                'cert_key': None,
                'smtp_auth': True,
                'smtpd_auth': True,
                'inet_interfaces': [],
                'inet_protocols': ['ipv4'],
                'mode': None,
                'recipient_access': None,
                'virtual_mailbox_base': '/var/mail/virtual',
                'mailbox_size_limit': 0,
                'local_networks': ['127.0.0.0/8'],
                'mynetworks': None,
                'mydestination': OrderedDict(),
                'append_dot_mydomain': 'no',
                'relay_domains': OrderedDict(),
                'sasl_passwd': [],
                'owner_request_special': 'yes',
                'transport': [],
                'virtual_map': [],
                'catchall': None})
        if data['recipient_access'] is None:
            data['recipient_access'] = [{'/.*/': 'smtpd_permissive'}]
        data = select_mode(data)
        data = select_catchall(data)
        data = select_networks(data)
        data = select_certs(data)
        data = select_dests_and_relays(data)
        data = select_interfaces(data)
        return data
    return _settings()
