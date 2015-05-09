# -*- coding: utf-8 -*-
'''

.. _module_mc_firewalld:

mc_firewalld / firewalld functions
============================================



'''

# Import python libs
import logging
import traceback
import mc_states.api
from salt.utils.odict import OrderedDict


__name = 'firewalld'
PREFIX = 'makina-states.services.firewall.{0}'.format(__name)
log = logging.getLogger(__name__)
prefered_ips = mc_states.api.prefered_ips


def get_configured_ifs(data):
    configured_ifs = {}
    for i in data['zones']:
        for f in data['zones'][i].get('interfaces', []):
            if f not in configured_ifs:
                configured_ifs[f] = i
    return configured_ifs


def get_endrule(audit, limit, log, log_level, log_prefix):
    endrule = ' '
    if log:
        endrule += ' log'
        if log_level:
            endrule += ' level="{0}"'.format(log_level)
        if log_prefix:
            endrule += ' prefix="{0}"'.format(log_prefix)
    elif audit:
        endrule += ' audit'
        if isinstance(audit, basestring):
            endrule += ' {0}'.format(audit)
    if limit and (log or audit):
        endrule += ' limit value="{0}"'.format(limit)
    return endrule


def add_dest_rules(destinations, rules, rule, endrule, action=None):
    if action:
        endrule += ' {0}'.format(action)
    if not destinations:
        rule = rule + endrule
        if rule not in rules:
            rules.append(rule)
    else:
        for d in destinations:
            crule = '{0} destination {1} {2}'.format(rule, d, endrule)
            if crule not in rules:
                rules.append(crule)
    return rules


def rich_rules(families=None,
               family='ipv4',
               sources=None,
               source=None,
               destinations=None,
               destination=None,
               services=None,
               service=None,
               ports=None,
               port=None,
               audit=None,
               log=None,
               log_prefix=None,
               log_level=None,
               forward_ports=None,
               forward_port=None,
               limit=None,
               action='accept'):
    '''

    >>> rich_rules(forward_port='1222', to_addr='1.2.3.4', to_port='22')
    >>> rich_rules(source='address="1.2.3.4"', port='22', action='drop')
    >>> rich_rules(
    ...  destination='address="1.2.3.4"', port='22', audit=True, action='drop')
    >>> rich_rules(
    ...  destination='address="1.2.3.4"', port='22', audit=True, action='drop')
    '''
    rules = []
    if not destinations:
        destinations = []
    destinations = destinations[:]
    if destination not in destinations:
        destinations.append(destination)
    if not sources:
        sources = []
    sources = sources[:]
    if source not in sources:
        sources.append(source)
    if not forward_ports:
        forward_ports = []
    forward_ports = forward_ports[:]
    if forward_port not in forward_ports:
        forward_ports.append(forward_port)
    forward_ports = [a for a in forward_ports if isinstance(a, dict)]
    if not ports:
        ports = []
    ports = ports[:]
    if port not in ports:
        ports.append(port)
    ports = [a for a in ports if isinstance(a, dict)]
    if not services:
        services = []
    services = services[:]
    if service not in services:
        services.append(service)
    if not families:
        families = []
    families = families[:]
    if family not in families:
        families.append(family)
    if destinations and not sources:
        sources = ['0.0.0.0']
    if (ports or services or forward_ports) and not sources:
        sources = [None]
    for fml in families:
        for src in sources:
            for port in forward_ports:
                fromp = port['port']
                protocols = port.get('protocols', ['tcp', 'udp'])
                to_port = port.get('to_port')
                to_addr = port.get('to_addr')
                for protocol in protocols:
                    rule = 'rule '
                    if family:
                        rule += ' family={0}'.format(fml)
                    if source:
                        rule += ' source {0}'.format(src)
                    rule += ' forward-port port="{0}" protocol="{1}"'.format(
                        fromp, protocol)
                    if to_port:
                        rule += ' to-port="{0}"'.format(to_port)
                    if to_addr:
                        rule += ' to-addr="{0}"'.format(to_addr)
                    endrule = get_endrule(
                        audit, limit, log, log_level, log_prefix)
                    add_dest_rules(destinations, rules, rule, endrule,
                                   action=action)
            for port in ports:
                fromp = port['port']
                protocols = port.get('protocols', ['tcp', 'udp'])
                for protocol in protocols:
                    rule = 'rule '
                    if family:
                        rule += ' family={0}'.format(fml)
                    if source:
                        rule += ' source {0}'.format(src)
                    rule += ' port port="{0}" protocol="{1}"'.format(
                        fromp, protocol)
                    endrule = get_endrule(
                        audit, limit, log, log_level, log_prefix)
                    add_dest_rules(destinations, rules, rule, endrule,
                                   action=action)
            for svc in services:
                rule = 'rule '
                if family:
                    rule += ' family={0}'.format(fml)
                if source:
                    rule += ' source {0}'.format(src)
                if svc:
                    rule += ' to service name="{0}"'.format(svc)
                endrule = get_endrule(
                    audit, limit, log, log_level, log_prefix,
                    action=action)
                add_dest_rules(destinations, rules, rule, endrule)
    return rules


def rich_rule(**kwargs):
    return rich_rules(**kwargs)[0]


def is_permissive():
    _s = __salt__
    data_net = _s['mc_network.default_net']()
    default_route = data_net['default_route']
    nodetypes_registry = _s['mc_nodetypes.registry']()
    permissive_mode = False
    if __salt__['mc_nodetypes.is_container']():
        # be permissive on the firewall side only if we are
        # routing via the host only network and going
        # outside througth NAT
        # IOW
        # if we have multiple interfaces and the default route is not on
        # eth0, we certainly have a directly internet addressable lxc
        # BE NOT permissive
        rif = default_route.get('iface', 'eth0')
        if rif == 'eth0':
            permissive_mode = True
    return permissive_mode


def add_real_interfaces(data):
    _s = __salt__
    data_net = _s['mc_network.default_net']()
    gifaces = data_net['gifaces']
    default_if = data_net['default_if']
    # handle aliased interfaces, in form "IFNAME:{INDEX}"
    ems = [i for i, ips in gifaces
           if i.startswith('em') and len(i) in [3, 4]]
    configured_ifs = get_configured_ifs(data)
    for iface, ips in gifaces:
        z = None
        if iface in configured_ifs:
            continue
        elif iface == default_if:
            z = data['default_zone']
        elif iface.startswith('veth'):
            z = 'trusted'
        elif 'lo' in iface:
            z = 'trusted'
        elif iface.startswith('tun'):
            z = 'vpn'
        elif 'docker' in iface:
            z = 'dck'
        elif 'lxc' in iface:
            z = 'lxc'
        elif iface in ['eth1'] or iface in ems:
            if data['have_rpn']:
                realrpn = False
                if iface in ems:
                    if iface == ems[-1]:
                        realrpn = True
                else:
                    realrpn = True
                if realrpn:
                    z = 'rpn'
        elif iface in ['br0', 'eth0', 'em0']:
            z = data['default_zone']
        if z:
            ifs = data['zones'][z].setdefault('interfaces', [])
            if iface not in ifs:
                ifs.append(iface)
    return data


def search_aliased_interfaces(data):
    '''
    Add public interfaces as candidates for aliased zones
    to support common IP Failover scenarii
    '''
    for i in data['zones']['public']['interfaces']:
        if i not in data['aliased_interfaces']:
            data['aliased_interfaces'].append(i)
        if i not in data['zones']['public']['interfaces']:
            data['zones']['public']['interfaces'].append(i)
    return data


def add_rule(data, zones=None, **kwargs):
    rrules = rich_rules(**kwargs)
    if not zones:
        zones = [z for z in data['zones']]
    for z in zones:
        rules = data['zones'][z].setdefault('rules', [])
        for rule in rrules:
            if rule not in rules:
                rules.append(rule)
    return data


def add_zones_policies(data):
    for z in data['public_zones']:
        if data['permissive_mode']:
            t = 'ACCEPT'
        else:
            t = 'REJECT'
        data['zopes'][z].setdefault('target', t)
    for network in data['banned_networks']:
        add_rule(data, source=network, action='drop')
    for network in data['trusted_networks']:
        add_rule(data, source=network, action='accept')
    return data


def add_aliased_interfaces(data):
    '''
    Mark aliases of interfaces to belong to the same interface
    of the attached interface, by default
    '''
    zonesn = [z for z in data['zones']]
    data = search_aliased_interfaces(data)
    cfgs = get_configured_ifs(data)
    for i in data['aliased_interfaces']:
        # add eth0:x to the same zone for the 100th
        for i in range(100):
            j = '{0}:i'.format(i)
            if j in cfgs:
                continue
            for z in zonesn:
                ifs = data['zones'][z]['interfaces']
                if i in ifs and j not in ifs:
                    ifs.append(j)
    return data


def add_services_policies(data):
    _s = __salt__
    burpsettings = _s['mc_burp.settings']()
    for s in [a for a in data['services']]:
        sources = None
        if s in data['public_services']:
            policy = 'accept'
            zones = data['public_zones'][:]
        elif s in data['restricted_services']:
            policy = 'drop'
            zones = data['public_zones'][:]
        else:
            policy = None
            zones = [a for a in data['zones'] if a != 'trusted']
        if s == 'burp':
            sources = []
            for s in prefered_ips(burpsettings['clients']):
                if a not in sources:
                    sources.append(s)
            if not sources:
                sources.append('127.0.0.1')
        if sources and not policy:
            policy = 'accept'
        if policy and data['permissive_mode'] and policy != 'accept':
            policy = 'accept'
        if not (sources or policy):
            continue
        for r in rich_rules(source=sources, service=s, action=policy):
            for z in zones:
                rules = data['zones'][z].setdefault('rules', [])
                if r not in rules:
                    rules.append(r)
    return data


def default_settings():
    _s = __salt__
    defaults = {
        'is_container': __salt__['mc_nodetypes.is_container'](),
        'aliased_interfaces': [],
        'default_zone': 'public',
        'banned_networks': [],
        'trusted_networks': [],
        # list of mappings
        'no_cloud_rules': False,
        'no_default_alias': False,
        'packages': ['ipset', 'ebtables', 'firewalld'],
        'zones': OrderedDict([
            ('block',  {}),
            ('drop',  {}),
            ('trusted',  {'interfaces': ['lo']}),
            ('dmz', {'target': 'ACCEPT'}),
            ('rpn', {'target': 'ACCEPT'}),
            ('virt', {'target': 'ACCEPT',
                      'interfaces':  ['virbr0', 'vibr0',
                                      'virbr1', 'vibr1']}),
            ('lxc', {'target': 'ACCEPT',
                     'interfaces':  ['lxcbr0', 'lxcbr1']}),
            ('docker', {'target': 'ACCEPT',
                        'interfaces':  ['docker0', 'docker1']}),
            ('internal',  {'interfaces',  ['eth1', 'em1']}),
            ('public',  {'interfaces',  ['br0', 'eth0', 'em0']}),
            ('external',  {}),
            ('home',  {}),
            ('work',  {})]),
        'internal_zones': [
            'internal', 'dmz', 'home', 'docker', 'lxc', 'virt'],
        'public_zones': ['external', 'public', 'home'],
        'public_services': ['http', 'https', 'smtp', 'dns'],
        'restricted_services': ['snmp'],
        'services': {
            'burp': {'port': [{'port': '4971-4974'}]},
            'dhcp': {'port': [{'port': '67-68'}]},
            'mastersalt': {'port': [{'port': '4605-4606'}]},
            'mongodb': {'port': [{'port': '27017'}]},
            'mumble': {'port': [{'port': '64738'}]},
            'mysql': {'port': [{'port': '3306'}]},
            'postgresql': {'port': [{'port': '5432'}]},
            'rabbitmq': {'port': [{'port': '15672'},
                                  {'port': '25672'}]},
            'redis': {'port': [{'port': '6379'}]},
            'salt': {'port': [{'port': '4505-4506'}]},
            'smtps': {'port': [{'port': '465'}]},
            'imap': {'port': [{'port': '143'}]},
            'imaps': {'port': [{'port': '993'}]}
        },
        #
        'have_rpn': _s['mc_provider.have_rpn'](),
        'have_docker': _s['mc_network.have_docker_if'](),
        'have_vpn': _s['mc_network.have_vpn_if'](),
        'have_lxc': _s['mc_network.have_lxc_if'](),
        #
        'permissive_mode': is_permissive(),
        'extra_confs': {'/etc/default/firewalld': {}},
        # retro compat
        'enabled': _s['mc_utils.get'](
            'makina-states.services.firewalld.enabled', True)}
    data = _s['mc_utils.defaults'](PREFIX, defaults)
    return data


def add_cloud_proxies(data):
    _s = __salt__
    # handle makinastates / compute node redirection ports
    if _s['mc_cloud.is_compute_node']():
        cloud_reg = _s['mc_cloud_compute_node.settings']()
        cloud_rules = cloud_reg.get(
            'reverse_proxies', {}).get('network_mappings', [])
        for portdata in cloud_rules:
            rules = []
            for r in rich_rules(
                forward_port=portdata['hostPort'],
                to_addr='address={ip}'.format(**portdata),
                to_port=portdata['port']
            ):
                if r not in rules:
                    rules.append(r)
    return data


def settings():
    '''
    firewalld settings

    makina-states.services.firewalld.enabled: activate firewalld

    DESIGN
        all services & forwardport & ports & etc are setted
        via rich rules to allow selection of source and destination
        variations.

    Add some rich rules in pillar to a zone::

        makina-states.services.firewalld.zones.public.rules-append:
          {% for i in salt['mc_firewalld.rich_rules'](
            port=22, action='drop'
          )- {{i}} {% endfor %}
          {% for i in salt['mc_firewalld.rich_rules'](
              forward_port=1122, to_addr='1.2.3.4', 'to_port'=22
          )- {{i}} {% endfor %}
          - "rule service name="ftp" log limit value="1/m" audit accept"

    Whitelist some services::

        makina-states.services.firewalld.public_services-append:
            - smtp

    Change whitelisted services::

        makina-states.services.firewalld.public_services: [http, https]
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = default_settings()
        data = add_real_interfaces(data)
        data = add_aliased_interfaces(data)
        data = add_zones_policies(data)
        data = add_services_policies(data)
        data = add_cloud_proxies(data)
        return data
    return _settings()
