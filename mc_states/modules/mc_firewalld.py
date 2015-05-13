# -*- coding: utf-8 -*-
'''

.. _module_mc_firewalld:

mc_firewalld / firewalld functions
============================================



'''

# Import python libs
import logging
import copy
import mc_states.api
from salt.utils.odict import OrderedDict


__name = 'firewalld'
six = mc_states.api.six
PREFIX = 'makina-states.services.firewall.{0}'.format(__name)
logger = logging.getLogger(__name__)
prefered_ips = mc_states.api.prefered_ips
PUBLIC_ZONES = ['public', 'external']
INTERNAL_ZONES = ['internal', 'dmz', 'home', 'docker', 'lxc', 'virt']
PUBLIC_SERVICES = ['http', 'https', 'smtp', 'dns', 'ssh']
DIRECT_RULESETS = ['passthrough', 'direct']
ZONE_RULESETS = ['rules']
RULESETS = DIRECT_RULESETS[:] + ZONE_RULESETS[:]
FAILOVER_COUNT = 16
DEFAULT_TARGET = 'drop'


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


def fix_data(data=None):
    if data is None:
        data = {}
    data.setdefault('services', {})
    data.setdefault('public_services', [])
    data.setdefault('restricted_services', [])
    data.setdefault('aliased_interfaces', [])
    data.setdefault('banned_networks', [])
    data.setdefault('internal_zones', INTERNAL_ZONES[:])
    data.setdefault('permissive_mode', is_permissive())
    data.setdefault('public_zones', PUBLIC_ZONES[:])
    data.setdefault('trusted_networks', [])
    data.setdefault('trust_internal', True)
    data.setdefault('zones', OrderedDict())
    if data['permissive_mode'] is None:
        data['permissive_mode'] = is_permissive()
    if data['trust_internal'] is None:
        data['trust_internal'] = True
    return data


def get_configured_ifs(data):
    configured_ifs = {}
    for i in data['zones']:
        for f in data['zones'][i].get('interfaces', []):
            if f not in configured_ifs:
                configured_ifs[f] = i
    return configured_ifs


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
        # elif iface.startswith('veth'):
        #     z = 'trusted'
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
    data = fix_data(data)
    public_ifs = []
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


def add_aliased_interfaces(data=None):
    '''
    Mark aliases of interfaces to belong to the same interface
    of the attached interface, by default
    '''
    if data is None:
        data = {}
    zonesn = [z for z in data['zones']]
    data = search_aliased_interfaces(data)
    cfgs = get_configured_ifs(data)
    count = data.setdefault('aliases', FAILOVER_COUNT)
    for i in data['aliased_interfaces']:
        # add eth0:x to the same zone for the FAILOVER_COUNTth
        for c in range(count):
            j = '{0}:{1}'.format(i, c)
            if j in cfgs:
                continue
            for z in zonesn:
                ifs = data['zones'][z].get('interfaces', [])
                if i in ifs and j not in ifs:
                    ifs.append(j)
    return data


def default_settings():
    _s = __salt__
    DEFAULTS = {
        'is_container': __salt__['mc_nodetypes.is_container'](),
        'aliased_interfaces': [],
        'default_zone': None,
        'aliases': FAILOVER_COUNT,
        'banned_networks': [],
        'trusted_networks': [],
        # list of mappings
        'no_cloud_rules': False,
        'no_salt': False,
        'no_ping': False,
        'no_default_alias': False,
        'packages': ['ipset', 'ebtables', 'firewalld'],
        'natted_networks': {'docker1': ['10.7.0.0/16'],
                            'docker0': ['172.17.0.0/24'],
                            'lxcbr1': ['10.5.0.0/16'],
                            'lxcbr0': ['10.0.3.0/24'],
                            'virt': ['192.168.122.0/24', '10.6.0.0/16'],
                            'vibr0': ['192.168.122.0/24', '10.6.0.0/16']},
        'zones': OrderedDict([
            ('block', {}),
            ('drop', {}),
            ('trusted', {'interfaces': ['lo']}),
            ('dmz', {}),
            ('rpn', {}),
            ('virt', {'interfaces': ['virbr0', 'vibr0',
                                     'virbr1', 'vibr1']}),
            ('lxc', {'interfaces': ['lxcbr0', 'lxcbr1']}),
            ('docker', {'interfaces': ['docker0', 'docker1']}),
            ('internal', {'interfaces': ['eth1', 'em1']}),
            ('public', {'interfaces': ['br0', 'eth0', 'em0']}),
            ('external', {}),
            ('home', {}),
            ('work', {})]),
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
            'imaps': {'port': [{'port': '993'}]},
            'http': {'port': [{'port': '80'}]},
            'https': {'port': [{'port': '443'}]}
        },
        #
        'have_rpn': _s['mc_provider.have_rpn'](),
        'have_docker': _s['mc_network.have_docker_if'](),
        'have_vpn': _s['mc_network.have_vpn_if'](),
        'have_lxc': _s['mc_network.have_lxc_if'](),
        #
        'permissive_mode': is_permissive(),
        'trust_internal': None,
        'extra_confs': {
            '/etc/default/firewalld': {},
            '/etc/firewalld.json': {'mode': '644'},
            '/etc/init.d/firewalld': {'mode': '755'},
            '/etc/systemd/system/firewalld.service': {'mode': '644'},
            '/usr/bin/ms_firewalld.py': {'mode': '755'}
        }}
    data = _s['mc_utils.defaults'](PREFIX, DEFAULTS)
    if data['trust_internal'] is None:
        data['trust_internal'] = True
    if data['default_zone'] is None:
        if data['public_zones']:
            data['default_zone'] = data['public_zones'][0]
        else:
            data['default_zone'] = PUBLIC_ZONES[0]
    data = complete_rules(data)
    data = add_real_interfaces(data)
    data = add_aliased_interfaces(data)
    return data


def cached_default_settings(ttl=60):
    cache_key = __name + 'cached_default_settings'
    return __salt__['mc_utils.memoize_cache'](
        default_settings, [], {}, cache_key, ttl)


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


def complete_rules(data):
    for z in [a for a in data['zones']]:
        zdata = data['zones'][z]
        if not isinstance(zdata, dict):
            data['zones'].pop(z, None)

    data.setdefault('rulesets', DIRECT_RULESETS[:])
    for ruleset in data['rulesets']:
        rules = data.setdefault(ruleset, [])
        for i in [
            a for a in data
            if (
                (a.endswith("-"+ruleset) or a.startswith(ruleset+"-")) and
                a not in [ruleset])
        ]:
            val = data[i]
            if isinstance(val, basestring):
                val = [val]
            if isinstance(val, list):
                for i in val:
                    if i not in rules:
                        rules.append(i)

    for z in [a for a in data['zones']]:
        zdata = data['zones'][z]
        zdata.setdefault('rulesets', ZONE_RULESETS[:])
        for ruleset in zdata['rulesets']:
            rules = zdata.setdefault(ruleset, [])
            for i in [
                a for a in zdata
                if (
                    (a.endswith("-"+ruleset) or a.startswith(ruleset+"-")) and
                    a not in [ruleset])
            ]:
                val = zdata[i]
                if isinstance(val, basestring):
                    val = [val]
                if isinstance(val, list):
                    for i in val:
                        if i not in rules:
                            rules.append(i)
    return data


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


def complete_address(address):
    if (
        isinstance(address, six.string_types) and
        address and
        'address=' not in address
    ):
        address = 'address="{0}"'.format(address)
    return address


def get_public_ips(cache=True, ttl=120):
    if not cache:
        ttl = 0

    def _do():
        net = __salt__['mc_network.settings']()
        data = cached_default_settings()
        ifcs = set()
        public_ips = set()
        zones = data.get('zones', {})

        for z in data.get('public_zones', []):
            for ifc in zones.get(z, {}).get('interfaces', []):
                ifcs.add(ifc)

        for ifc, ips in six.iteritems(
            __grains__.get('ip4_interfaces', {})
        ):
            if ifc not in ifcs:
                continue
            for ip in ips:
                public_ips.add(ip)

        # if we are early in privisonning, we get a change to configure
        # the rules via the net settings
        for interfaces in net.get('ointerfaces', []):
            for ifc, odata in six.iteritems(interfaces):
                ifc = ifc.replace('_', ':')
                if ifc not in ifcs:
                    continue
                addr = odata.get('address', '')
                if addr:
                    public_ips.add(addr)
        public_ips.add('192.168.0.1')
        public_ips.add('127.0.0.1')
        public_ips = list(public_ips)

        def _filter_local(ip):
            return __salt__['mc_network.is_public'](ip)

        public_ips = filter(_filter_local, public_ips)
        return public_ips
    cache_key = __name + 'get_public_ips'
    return __salt__['mc_utils.memoize_cache'](
        _do, [], {}, cache_key, ttl)


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
               masquerade=False,
               action='accept',
               public_ips=None,
               protocols=None):
    '''

    public_ips
        firewalld does make special forward rules relying on packet
        marking whenever they macth the port and the source/dest.
        This means that it will remap all traffic from an aforementioned rule
        matching this port on the public zone to be reentrant and goes to the
        destination of the rule instead of the real destination.
        Thus to correctly NAT services without limiting outgoing
        traffic on the same ports from network branches withing the NAT,
        we limit the exposure of the target rules to the public
        facing ips of the underlying host.
        This also means, that logically, as nearly always with natted
        services, network access points from within the NAT
        cant access the services as if they would be outside of the NAT.
        Technically speaking, in case of forward ports, we only apply the rule
        on the public facing address (aka addresses of interfaces which are
        linked to the public zones) by limitating the rule scopes to those
        destinations.

        public_ips is indeed a list of ips, which if empty or None will
        be computed from host network informations.

        To disable destinations restrictions, you can set public_ips to False.

    .. code-block:: python

        rich_rules(forward_port={'port': '12', addr='1.2.3.4'}, port='22')
        rich_rules(forward_port={'port': '12', addr='1.2.3.4'}, port='22'},
                   destination='x.x.x.x')
        rich_rules(masquerade=True, source='x.x.x.x', dest='x.x.x.x')
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
    if public_ips is False:
        public_ips = []
    elif not public_ips:
        # fallback on destinations
        public_ips = destinations[:]
        # if we do not have destination restriction, we
        # try to find any public ip, and if we found some
        # they will be the destination restrictions of the
        # forwarded rules
        if not public_ips:
            public_ips = get_public_ips()
    public_ips = [complete_address(d) for d in public_ips if d]
    destinations = [complete_address(d) for d in destinations if d]
    if not protocols:
        protocols = ['udp', 'tcp']
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
    if not sources:
        sources = []
    sources = sources[:]
    if source and source not in sources:
        sources.append(source)
    if destinations and not sources:
        sources = ['0.0.0.0']

    # forwarded ports defs wins over port defs
    nforward_ports = {}
    for p in forward_ports[:]:
        if 'to_port' not in p and 'port' not in p:
            raise ValueError('"{0}" does not contains port info'.format(p))
        port = None
        if 'to_port' in p and 'port' not in p:
            port = p['to_port']
        if port and isinstance(port, int):
            port = "{0}".format(port)
        if port is not None:
            p['to_port'] = p['port'] = port
        for i in ['port', 'to_port']:
            if isinstance(p.get(i), int):
                p[i] = "{0}".format(p[i])
        p.setdefault('protocols', protocols[:])
        if p['port'] in ports:
            ports.pop(p['port'], None)
        nforward_ports[p['port']] = p
    if (ports or services or forward_ports) and not sources:
        sources = [None]
    sources = [complete_address(d) for d in sources]
    lsources = [a for a in sources if a]
    for fml in families:
        if masquerade:
            mrule = 'rule family="{0}" masquerade'.format(family)
            if lsources and not destinations:
                for s in lsources:
                    smrule = mrule + ' source {0}'.format(s)
                    if smrule not in rules:
                        rules.append(smrule)
            elif lsources and destinations:
                for s in lsources:
                    smrule = mrule + ' source {0}'.format(s)
                    for d in destinations:
                        dsmrule = smrule + ' destination {0}'.format(d)
                        if dsmrule not in rules:
                            rules.append(dsmrule)
            elif not lsources and destinations:
                for d in destinations:
                    dsmrule = mrule + ' destination {0}'.format(d)
                    if dsmrule not in rules:
                        rules.append(dsmrule)
            elif not lsources and not destinations:
                if mrule not in rules:
                    rules.append(mrule)
        for src in sources:
            for portid, fromport in six.iteritems(ports):
                fromp = fromport['port']
                protocols = fromport.get('protocols', protocols[:])
                for protocol in protocols:
                    rule = 'rule'
                    if family:
                        rule += ' family="{0}"'.format(fml)
                    if src and src not in ['address="0.0.0.0"']:
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
            for portid, portdata in six.iteritems(nforward_ports):
                fromp = portdata['port']
                protocols = portdata.get('protocols', protocols[:])
                to_port = portdata.get('to_port')
                to_addr = portdata.get('to_addr')
                for protocol in protocols:
                    rule = 'rule'
                    if family:
                        rule += ' family="{0}"'.format(fml)
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
                    add_dest_rules(public_ips, rules, rule, endrule)
            for svc in services:
                rule = 'rule'
                if family:
                    rule += ' family="{0}"'.format(fml)
                if src and src not in ['address="0.0.0.0"']:
                    rule += ' source {0}'.format(src)
                if svc:
                    rule += ' service name="{0}"'.format(svc)
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
            if (
                (src and protocols) and
                not (ports or services or forward_ports)
            ):
                rule = 'rule'
                if family:
                    rule += ' family="{0}"'.format(fml)
                if src and src not in ['address="0.0.0.0"']:
                    rule += ' source {0}'.format(src)
                for protocol in protocols:
                    prule = rule
                    prule += ' protocol value="{0}"'.format(protocol)
                    endrule = get_endrule(
                        audit=audit,
                        log=log,
                        log_level=log_level,
                        log_prefix=log_prefix,
                        limit=limit)
                    add_dest_rules([],
                                   rules,
                                   prule,
                                   endrule,
                                   action=action)
    return rules


def rich_rule(**kwargs):
    return rich_rules(**kwargs)[0]


def add_rule(data, zones=None, rule=None, rules=None, **kwargs):
    rrules = rich_rules(**kwargs)
    if rules is None:
        rules = []
    if isinstance(rule, six.string_types) and rule not in rules:
        rules.append(rule)
    for i in rules:
        if i not in rrules:
            rrules.append(rule)
    if not zones:
        zones = [z for z in data['zones']]
    for z in zones:
        rules = data['zones'][z].setdefault('rules', [])
        for rule in rrules:
            if rule not in rules:
                rules.append(rule)
    return data


def add_zones_policies(data=None):
    data = fix_data(data)
    zones = data.get('zones', {})
    for z in data['public_zones']:
        zdata = zones.get(z, {})
        t = zdata.get('target', DEFAULT_TARGET)
        if data['permissive_mode']:
            t = 'accept'
        zone = data['zones'].setdefault(z, {})
        zone['target'] = t
    for z in data['internal_zones']:
        zdata = zones.get(z, {})
        t = zdata.get('target', DEFAULT_TARGET)
        if data['trust_internal']:
            t = 'accept'
        zone = data['zones'].setdefault(z, {})
        zone['target'] = t
    if not data.get('no_ping', False):
        rule = 'rule family="ipv4" protocol value="icmp" accept'
        add_rule(data, rule=rule)
    for network in data['banned_networks']:
        add_rule(data, source=network, action='drop')
    for network in data['trusted_networks']:
        add_rule(data, source=network, action='accept')
    return data


def add_natted_networks(data=None):
    '''
    Add nat rules if possible on non
    public zones
    '''
    data = fix_data(data)
    to_nat = set()
    natted = data.get('natted_networks', {})
    for z in data.get('zones', {}):
        if z not in data.get('internal_zones', []):
            continue
        zdata = data['zones'][z]
        for ifc in zdata.get('interfaces', []):
            for network in natted.get(ifc, []):
                to_nat.add(network)
    for network in to_nat:
        add_rule(data=data,
                 masquerade=True,
                 source='address="{0}"'.format(network),
                 destination='not address="{0}"'.format(network))
    return data


def add_services_policies(data=None):
    data = fix_data(data)
    _s = __salt__
    burpsettings = _s['mc_burp.settings']()
    controllers_registry = _s['mc_controllers.registry']()
    for i in ['public_services', 'restricted_services']:
        for s in data[i]:
            data['services'].setdefault(s, {})
    if not data.get('no_salt', False):
        if controllers_registry['is']['salt_master']:
            if 'salt' not in data['public_services']:
                data['public_services'].append('salt')
        if controllers_registry['is']['mastersalt_master']:
            if 'mastersalt' not in data['public_services']:
                data['public_services'].append('mastersalt')
    for z in [a for a in data['zones'] if a != 'trusted']:
        zdata = data['zones'][z]
        services = zdata.setdefault('services', {})
        pservices = zdata.setdefault('public_services', [])
        rservices = zdata.setdefault('restricted_services', [])
        if not services:
            services.update(copy.deepcopy(data['services']))
        if not pservices:
            pservices.extend(copy.deepcopy(data['public_services']))
        if not rservices:
            rservices.extend(copy.deepcopy(data['restricted_services']))
        for i in [rservices, pservices]:
            for s in i:
                services.setdefault(s, {})
        for s in [a for a in data['services'] if a not in services]:
            services[s] = copy.deepcopy(data['services'][s])
        to_add = [a for a in services]

        def order_policies(apservices, arservices):
            def do(a):
                pref = 'z'
                if a in apservices:
                    pref = 'm'
                elif a in arservices:
                    pref = 'a'
                return '{0}_{1}'.format(pref, a)
            return do

        to_add.sort(key=order_policies(pservices, rservices))
        for s in to_add:
            if s not in data['services']:
                data['services'][s] = copy.deepcopy(services[s])
            sources = None
            if s in pservices:
                policy = 'accept'
            elif s in rservices:
                policy = 'drop'
            else:
                policy = None
            if s == 'burp':
                sources = [a for a in burpsettings['clients']]
                if not sources:
                    sources = ['127.0.0.1']
            if not sources:
                sources = []
            sources = _s['mc_utils.uniquify'](prefered_ips(sources))
            if policy and data['permissive_mode'] and policy != 'accept':
                policy = 'accept'
            if s and sources and not policy:
                policy = 'accept'
            if policy:
                policy = policy.lower()
            if not (sources or policy):
                continue
            add_rule(
                data, zones=[z], sources=sources, service=s, action=policy)
    return data


def add_cloud_proxies(data):
    _s = __salt__
    # handle makinastates / compute node redirection ports
    if _s['mc_cloud.is_compute_node']():
        cloud_reg = _s['mc_cloud_compute_node.settings']()
        cloud_rules = cloud_reg.get(
            'reverse_proxies', {}).get('network_mappings', [])
        for port, portdata in six.iteritems(cloud_rules):
            add_rule(data,
                     zones=data['public_zones'],
                     forward_port={'port': portdata['hostPort'],
                                   'to_port': portdata['port'],
                                   'to_addr': portdata['to_addr']})
    return data


def settings():
    '''
    firewalld settings

    makina-states.services.firewalld.enabled
        set to true to activate firewalld

    DESIGN
        all services & forwardport & ports & etc are setted
        via rich rules to allow fine-graines selections of source
        and destination variations.

    GLOBAL SETTINGS

        permissive_mode
            force all traffic to be accepted
        public_interfaces
            internet faced interfaces
        internal_interfaces
            interfaces wired to internal network with no much restriction
        public_services
            services to allow
        restricted_services
            services to block
        <XXX>-direct
            direct rules
        <XXX>-passthrough
            direct/passthrough rules (not implemented yet)
        services
            list of services to deine
        zones
            mapping of zones definitions

    PER ZONE SETTINGS:

    You can configure zone settings via via entries in the zone pillar:
        default_policy
          enforce policy, attention in firewalld world, everything
          is dropped if no match, so no need to force reject.
          Its even harmful as it wont cut any further rich rules
          to have a change to apply !
        interfaces
            interfaces to add to the zone

        XXX-rules
            rich rules

    For exmeple, to Add some rich rules in pillar to a zone, all
    ``makina-states.services.firewall.firewalld.zones.public.rules<id>``
    are merged ::

    .. code-block:: yaml

        makina-states.services.firewall.firewalld.zones.public.rules-foo:
          {% for i in salt['mc_firewalld.rich_rules'](
            port=22, action='drop'
          )- {{i}} {% endfor %}
          {% for i in salt['mc_firewalld.rich_rules'](
            forward_port={'port': 1122, 'to_addr': '1.2.3.4', 'to_port'=22}
          )- {{i}} {% endfor %}
        makina-states.services.firewall.firewalld.zones.public.rules-bar:
          - "rule service name="ftp" log limit value="1/m" audit accept"
          {% for i in salt['mc_firewalld.rich_rules'](
            port=22, destinations=['127.0.0.1'],  action='drop'
          )- {{i}} {% endfor %}
          {% for i in salt['mc_firewalld.rich_rules'](
              port=22, destinations=['not address="127.0.0.2"'],  action='drop'
          )- {{i}} {% endfor %}

    NOTE
       **DO NOT ACTIVATE MASQUERADING, IT IS TOO MUCH CATCHY**
        PLEASE USE APPROPRIATE RESTRICTIVES RICH MASQUERADE RULES

    Whitelist some services

    .. code-block:: yaml

        makina-states.services.firewall.firewalld.public_services-append:
            - smtp

    Change whitelisted services

    .. code-block:: yaml

        makina-states.services.firewall.firewalld.public_services: [http]

    Define a new service

    .. code-block:: yaml

        makina-states.services.firewall.firewalld.services.foo:
            port: [{protocol: tcp, port: 2222}]
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = default_settings()
        data = add_zones_policies(data)
        data = add_natted_networks(data)
        data = add_services_policies(data)
        data = add_cloud_proxies(data)
        return data
    return _settings()
