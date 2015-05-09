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
six = mc_states.api.six
PREFIX = 'makina-states.services.firewall.{0}'.format(__name)
log = logging.getLogger(__name__)
prefered_ips = mc_states.api.prefered_ips
PUBLIC_ZONES = ['public', 'external']
INTERNAL_ZONES = ['internal', 'dmz', 'home', 'docker', 'lxc', 'virt']
PUBLIC_SERVICES = ['http', 'https', 'smtp', 'dns']


def get_configured_ifs(data):
    configured_ifs = {}
    for i in data['zones']:
        for f in data['zones'][i].get('interfaces', []):
            if f not in configured_ifs:
                configured_ifs[f] = i
    return configured_ifs


def get_endrule(audit=None,
                log=None,
                log_level=None,
                log_prefix=None,
                limit=None):
    endrule = ''
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
    sep = ''
    if endrule and not endrule.startswith(' '):
        sep = ' '
    if not destinations:
        rule = rule + sep + endrule
        if rule not in rules:
            rules.append(rule)
    else:
        for d in destinations:
            crule = '{0} destination {1}{3}{2}'.format(rule, d, endrule, sep)
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
               action='accept',
               protocols=None):
    '''

    .. code-block:: python

        rich_rules(forward_port={'port': '12', addr='1.2.3.4'}, port='22')
        rich_rules(source='address="1.2.3.4"', port='22', action='drop')
        rich_rules(destination='address="1.2.3.4"',
                   port='22',
                   audit=True,
                   action='drop')
        rich_rules(destination='address="1.2.3.4"',
                   port={'port': '22', 'protocol': 'tcp'})
        rich_rules(destination='address="1.2.3.4"', port='22',
                   audit=True, action='drop')
    '''
    rules = []
    if not destinations:
        destinations = []
    destinations = destinations[:]
    if destination and destination not in destinations:
        destinations.append(destination)
    if not protocols:
        protocols = ['udp', 'tcp']
    if not sources:
        sources = []
    sources = sources[:]
    if source and source not in sources:
        sources.append(source)
    if not forward_ports:
        forward_ports = []
    forward_ports = forward_ports[:]
    if forward_port and forward_port not in forward_ports:
        forward_ports.append(forward_port)
    forward_ports = [a for a in forward_ports if isinstance(a, dict)]
    if not ports:
        ports = []
    ports = ports[:]
    if port and port not in ports:
        ports.append(port)
    nports = {}
    for port in ports:
        if isinstance(port, (int,)):
            port = "{0}".format(port)
        if isinstance(port, (six.string_types)):
            port = {'port': port, 'protocols': protocols[:]}
        if isinstance(port, dict):
            protos = port.setdefault('protocols', protocols[:])
            nport = nports.setdefault(port['port'], port)
            nport['port'] = port['port']
            for p in protos:
                if p not in nport['protocols']:
                    nport['protocols'].append(p)
        else:
            raise ValueError('\'{0}\' is not a dict'.format(port))
    ports = nports
    if not services:
        services = []
    services = services[:]
    if service and service not in services:
        services.append(service)
    if not families:
        families = []
    families = families[:]
    if family and family not in families:
        families.append(family)
    if destinations and not sources:
        sources = ['0.0.0.0']
    if (ports or services or forward_ports) and not sources:
        sources = [None]
    for fml in families:
        for src in sources:
            for portid, fromport in six.iteritems(ports):
                for to_portd in forward_ports:
                    fromp = fromport['port']
                    protocols = fromport.get('protocols', protocols[:])
                    to_port = to_portd.get('port')
                    to_addr = to_portd.get('addr')
                    for protocol in protocols:
                        rule = 'rule'
                        if family:
                            rule += ' family={0}'.format(fml)
                        if source:
                            rule += ' source {0}'.format(src)
                        rule += (
                            ' forward-port port="{0}" protocol="{1}"'
                        ).format(fromp, protocol)
                        if to_port:
                            rule += ' to-port="{0}"'.format(to_port)
                        if to_addr:
                            rule += ' to-addr="{0}"'.format(to_addr)
                        endrule = get_endrule(
                            audit=audit,
                            log=log,
                            log_level=log_level,
                            log_prefix=log_prefix,
                            limit=limit)
                        add_dest_rules(destinations, rules, rule, endrule,
                                       action=action)
            if not forward_ports:
                for portid, port in six.iteritems(ports):
                    fromp = port['port']
                    protocols = port.get('protocols', protocols[:])
                    for protocol in protocols:
                        rule = 'rule'
                        if family:
                            rule += ' family={0}'.format(fml)
                        if source:
                            rule += ' source {0}'.format(src)
                        rule += ' port port="{0}" protocol="{1}"'.format(
                            fromp, protocol)
                        endrule = get_endrule(
                            audit=audit,
                            log=log,
                            log_level=log_level,
                            log_prefix=log_prefix,
                            limit=limit)
                        add_dest_rules(destinations,
                                       rules,
                                       rule,
                                       endrule,
                                       action=action)
                for svc in services:
                    rule = 'rule'
                    if family:
                        rule += ' family={0}'.format(fml)
                    if source:
                        rule += ' source {0}'.format(src)
                    if svc:
                        rule += ' to service name="{0}"'.format(svc)
                    endrule = get_endrule(
                        audit=audit,
                        log=log,
                        log_level=log_level,
                        log_prefix=log_prefix,
                        limit=limit)
                    add_dest_rules([],
                                   rules,
                                   rule,
                                   endrule,
                                   action=action)
    return rules


def rich_rule(**kwargs):
    return rich_rules(**kwargs)[0]


def is_permissive():
    _s = __salt__
    data_net = _s['mc_network.default_net']()
    default_route = data_net['default_route']
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


def add_real_interfaces(data=None):
    _s = __salt__
    if data is None:
        data = {}
    fzones = data.setdefault('zones', OrderedDict())
    data_net = _s['mc_network.default_net']()
    gifaces = data_net['gifaces']
    default_if = data_net['default_if']
    # handle aliased interfaces, in form "IFNAME:{INDEX}"
    ems = [i for i, ips in gifaces
           if i.startswith('em') and len(i) in [3, 4]]
    configured_ifs = get_configured_ifs(data)
    dz = data.get('default_zone', 'public')
    for iface, ips in gifaces:
        z = None
        if iface in configured_ifs:
            continue
        elif iface == default_if:
            z = dz
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
            if data.get('have_rpn', False):
                realrpn = False
                if iface in ems:
                    if iface == ems[-1]:
                        realrpn = True
                else:
                    realrpn = True
                if realrpn:
                    z = 'rpn'
        elif iface in ['br0', 'eth0', 'em0']:
            z = dz
        if z:
            zone = fzones.setdefault(z, {})
            ifs = zone.setdefault('interfaces', [])
            if iface not in ifs:
                ifs.append(iface)
    return data


def search_aliased_interfaces(data=None):
    '''
    Add public interfaces as candidates for aliased zones
    to support common IP Failover scenarii
    '''
    if data is None:
        data = {}
    public_ifs = []
    data.setdefault('public_zones', PUBLIC_ZONES[:])
    data.setdefault('zones', OrderedDict())
    data.setdefault('aliased_interfaces', [])
    for z in data['public_zones']:
        zone = data['zones'].setdefault(z, {})
        zone.setdefault('interfaces', [])
        for i in zone['interfaces']:
            public_ifs.append(i)
        for i in zone['interfaces']:
            if i not in data['aliased_interfaces']:
                data['aliased_interfaces'].append(i)
    for ifc in data['aliased_interfaces']:
        if ifc not in public_ifs:
            for z in data['public_zones']:
                zdata = data['zones'].setdefault(z, {})
                ifcs = zdata.setdefault('interfaces', [])
                if ifc not in ifcs:
                    ifcs.append(ifc)
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
                ifs = data['zones'][z].get('interfaces', [])
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


def complete_rules(data):
    for z in [a for a in data['zones']]:
        zdata = data['zones'][z]
        if not isinstance(zdata, dict):
            data['zones'].pop(z, None)
    for z in [a for a in data['zones']]:
        zdata = data['zones'][z]
        rules = zdata.setdefault('rules',  [])
        for i in [
            a for a in zdata
            if (
                (a.endswith('rules') or a.startswith('rules')) and
                a not in ['rules'])
        ]:
            val = zdata[i]
            if isinstance(val, basestring):
                val = [val]
            if isinstance(val, list):
                for i in val:
                    if i not in rules:
                        rules.append(i)
    return data


def default_settings():
    _s = __salt__
    defaults = {
        'is_container': __salt__['mc_nodetypes.is_container'](),
        'aliased_interfaces': [],
        'default_zone': None,
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
            ('internal',  {'interfaces':  ['eth1', 'em1']}),
            ('public',  {'interfaces':  ['br0', 'eth0', 'em0']}),
            ('external',  {}),
            ('home',  {}),
            ('work',  {})]),
        'internal_zones': INTERNAL_ZONES[:],
        'public_zones': PUBLIC_ZONES[:],
        'public_services': PUBLIC_SERVICES[:],
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
    if data['default_zone'] is None:
        if data['public_zones']:
            data['default_zone'] = data['public_zones'][0]
        else:
            data['default_zone'] = PUBLIC_ZONES[0]
    data = complete_rules(data)
    data = add_real_interfaces(data)
    data = add_aliased_interfaces(data)
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
                port=portdata['hostPort'],
                forward_port={'port': portdata['port'],
                              'addr': portdata['to_addr']}
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

    Add some rich rules in pillar to a zone, all
    ``makina-states.services.firewall.firewalld.zones.public.rules<id>``
    are merged::

        makina-states.services.firewall.firewalld.zones.public.rules-foo:
          {% for i in salt['mc_firewalld.rich_rules'](
            port=22, action='drop'
          )- {{i}} {% endfor %}
          {% for i in salt['mc_firewalld.rich_rules'](
            forward_port={'port': 1122, 'addr': '1.2.3.4'}, 'port'=22
          )- {{i}} {% endfor %}
        makina-states.services.firewall.firewalld.zones.public.rules-bar:
          - "rule service name="ftp" log limit value="1/m" audit accept"

    Whitelist some services::

        makina-states.services.firewall.firewalld.public_services-append:
            - smtp

    Change whitelisted services::

        makina-states.services.firewall.firewalld.public_services: [http, https]
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = default_settings()
        data = add_zones_policies(data)
        data = add_services_policies(data)
        data = add_cloud_proxies(data)
        return data
    return _settings()
