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
LOCAL_NETS = ['10.0.0.0/8',
              '192.168.0.0/16',
              '172.16.0.0/12']


def prefered_ips(ips, ttl=60, *args, **kw):
    def _do(*a, **k):
            return mc_states.api.prefered_ips(*a, **k)
    cache_key = __name + '.prefered_ips{0}'.format(ips)
    return __salt__['mc_utils.memoize_cache'](
        _do, [ips], {}, cache_key, ttl)


def is_allow_local():
    _s = __salt__
    data_net = _s['mc_network.default_net']()
    default_route = data_net['default_route']
    local_mode = False
    if __salt__['mc_nodetypes.is_container']():
        # be local on the firewall side only if we are
        # routing via the host only network and going
        # outside througth NAT
        # IOW
        # if we have multiple interfaces and the default route is not on
        # eth0, we certainly have a directly internet addressable lxc
        # BE NOT local
        local_mode = True
    return local_mode


def is_permissive():
    _s = __salt__
    data_net = _s['mc_network.default_net']()
    default_route = data_net['default_route']
    permissive_mode = False
    if __salt__['mc_nodetypes.is_container']():
        # be local on the firewall side only if we are
        # routing via the host only network and going
        # outside througth NAT
        # IOW
        # if we have multiple interfaces and the default route is not on
        # eth0, we certainly have a directly internet addressable lxc
        # BE NOT local
        rif = default_route.get('iface', 'eth0')
        if rif == 'eth0':
            permissive_mode = True
    return permissive_mode


def fix_data(data=None):
    if data is None:
        data = {}
    data.setdefault('local_networks', LOCAL_NETS[:])
    data.setdefault('services', {})
    data.setdefault('public_services', [])
    data.setdefault('restricted_services', [])
    data.setdefault('aliased_interfaces', [])
    data.setdefault('banned_networks', [])
    data.setdefault('internal_zones', INTERNAL_ZONES[:])
    data.setdefault('permissive_mode', is_permissive())
    data.setdefault('allow_local', is_allow_local())
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


def is_eth(ifc):
    return ifc.startswith('eth') or ifc.startswith('em')


def test_container(data=None):
    if not data:
        data = {}
    return data.setdefault('is_container',
                           __salt__['mc_nodetypes.is_container']())


def test_rpn(data, iface, ems=None):
    if not ems:
        ems = []
    realrpn = False
    if data.get('have_rpn', False) and (
        not test_container(data)
    ) and (
        iface in ['eth1'] or iface in ems
    ):
        if iface in ems:
            if iface == ems[-1]:
                realrpn = True
        else:
            realrpn = True
    return realrpn


def add_real_interfaces(data=None):
    _s = __salt__
    if data is None:
        data = {}
    fzones = data.setdefault('zones', OrderedDict())
    is_container = test_container(data)
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
        if (is_container and is_eth(iface)) or iface == default_if:
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
        elif test_rpn(data, iface, ems):
            z = 'rpn'
        elif iface in ['br0', 'eth0', 'em0']:
            z = dz
        elif iface.startswith('eth') or iface.startswith('em'):
            z = 'internal'
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
        'aliased_interfaces': [],
        'default_zone': None,
        'aliases': FAILOVER_COUNT,
        'banned_networks': [],
        'trusted_networks': [],
        # list of mappings
        'local_networks': LOCAL_NETS[:],
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
            ('internal', {'interfaces': []}),
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
            'mongodb': {'port': [{'port': '27017'}]},
            # ftp on containers wont use conntrack
            'ftpnc': {'port': [{'port': '21'}]},
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
        'allow_local': is_allow_local(),
        'trust_internal': None,
        'extra_confs': {
            '/etc/default/firewalld': {},
            '/etc/firewalld.json': {'mode': '644'},
            '/etc/init.d/firewalld': {'mode': '755'},
            '/etc/systemd/system/firewalld.service': {'mode': '644'},
            '/usr/bin/ms_firewalld.py': {'mode': '755'}
        }}
    test_container(DEFAULTS)
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


def has_action(rule):
    ret = (
        ('service' in rule) or
        (' port ' in rule) or
        (' protocol ' in rule) or
        ('icmp-block' in rule) or
        ('masquerade' in rule) or
        ('forward-port' in rule)
    )
    return ret


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


def action_allowed(rule):
    ret = not (
        ('masquerade' in rule) or
        ('forward-port' in rule) or
        ('icmp-block' in rule)
    )
    return ret


def source_allowed(rule):
    return ' source ' not in rule


def destination_allowed(rule):
    return (
        (' destination' not in rule)
    )


def complete_rich_rules(rules=None,
                        rule=None,
                        family=None,
                        destinations=None,
                        icmp_block=None,
                        masquerade=None,
                        sources=None,
                        protocols=None,
                        ports=None,
                        forward_ports=None,
                        services=None,
                        endrule=None,
                        audit=None,
                        log=None,
                        log_prefix=None,
                        log_level=None,
                        limit=None,
                        action=None):
    '''
    Subroutine of the rich rule helper
    '''
    if not (
        family and (
            masquerade or
            has_action(endrule or '') or
            ports or
            forward_ports or
            icmp_block or
            (sources or destinations)
        )
    ):
        raise ValueError('invalid invocation')
    else:
        if rules is None:
            rules = []
        if not rule:
            rule = 'rule'

    to_add_rules = [rule]

    if family:
        buffer_rules = []
        for rule in to_add_rules:
            if 'family' in rule:
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            else:
                prule = rule
                prule += ' family="{0}"'.format(family)
                if prule not in to_add_rules:
                    buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if masquerade:
        buffer_rules = []
        for rule in to_add_rules:
            if has_action(rule):
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            else:
                prule = rule
                prule += ' masquerade'
                if prule not in buffer_rules:
                    buffer_rules.append(prule)
        to_add_rules = buffer_rules
        # never masquerade a single source to itself
        if len(sources) == 1 and not destinations:
            source = sources[0]
            destination = source
            if not source.startswith('not '):
                destination = 'not {0}'.format(destination)
            destinations = [destination]

    if icmp_block:
        buffer_rules = []
        if isinstance(icmp_block, six.string_types):
            icmp_block = [icmp_block]
        elif not isinstance(icmp_block, list):
            icmp_block = ['']
        prules = []
        for i in icmp_block:
            rule = 'icmp-block'
            if i:
                rule += ' name="{0}"'.format(i)
            if rule not in prules:
                prules.append(rule)
        for rule in to_add_rules:
            if has_action(rule):
                continue
            for prule in prules:
                prule = '{0} {1}'.format(rule, prule)
                if prule not in buffer_rules:
                    buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if sources:
        buffer_rules = []
        for rule in to_add_rules:
            if not source_allowed(rule):
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            for p in sources:
                prule = rule
                prule += ' source {0}'.format(p)
                if prule not in buffer_rules:
                    buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if destinations:
        buffer_rules = []
        for rule in to_add_rules:
            if not destination_allowed(rule):
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            for p in destinations:
                prule = rule
                if 'ipv4' in rule and ':' in p:
                    continue
                if 'ipv6' in rule and '.' in p:
                    continue
                prule += ' destination {0}'.format(p)
                if prule not in buffer_rules:
                    buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if ports:
        buffer_rules = []
        pprotocols = protocols
        if not pprotocols:
            pprotocols = ['tcp', 'udp']
        for rule in to_add_rules:
            if has_action(rule):
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            for portid, fromport in six.iteritems(ports):
                fromp = fromport['port']
                protocols = fromport.get('protocols', pprotocols[:])
                for protocol in protocols:
                    prule = rule
                    prule += ' port port="{0}" protocol="{1}"'.format(
                        fromp, protocol)
                    if prule not in buffer_rules:
                        buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if forward_ports:
        buffer_rules = []
        pprotocols = protocols
        if not pprotocols:
            pprotocols = ['tcp', 'udp']
        for rule in to_add_rules:
            if has_action(rule):
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            for portid, portdata in six.iteritems(forward_ports):
                fromp = portdata['port']
                protocols = portdata.get('protocols', pprotocols[:])
                to_port = portdata.get('to_port')
                to_addr = portdata.get('to_addr')
                for protocol in protocols:
                    prule = rule
                    prule += (
                        ' forward-port port="{0}" protocol="{1}"'
                    ).format(fromp, protocol)
                    if to_port:
                        prule += ' to-port="{0}"'.format(to_port)
                    if to_addr:
                        prule += ' to-addr="{0}"'.format(to_addr)
                    if prule not in buffer_rules:
                        buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if services:
        buffer_rules = []
        for rule in to_add_rules:
            if has_action(rule):
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            for svc in services:
                prule = rule
                prule += ' service name="{0}"'.format(svc)
                if prule not in buffer_rules:
                    buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if protocols:
        buffer_rules = []
        for rule in to_add_rules:
            if not (
                ('source ' in rule) or
                ('destination ' in rule)
            ) or (
                has_action(rule)
            ):
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            for protocol in protocols:
                prule = rule
                prule += ' protocol value="{0}"'.format(protocol)
                if prule not in buffer_rules:
                    buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if endrule:
        buffer_rules = []
        for rule in to_add_rules:
            if has_action(endrule) and has_action(rule):
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            prule = rule
            prule += ' {0}'.format(endrule)
            if prule not in buffer_rules:
                buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if log:
        buffer_rules = []
        logrule = ' log'
        if log_level:
            logrule += ' level="{0}"'.format(log_level)
        if log_prefix:
            logrule += ' prefix="{0}"'.format(log_prefix)
        for rule in to_add_rules:
            prule = rule
            prule += ' {0}'.format(logrule)
            if prule not in buffer_rules:
                buffer_rules.append(prule)
        to_add_rules = buffer_rules
    elif audit:
        buffer_rules = []
        logrule += ' audit'
        if isinstance(audit, basestring):
            logrule += ' {0}'.format(audit)
        for rule in to_add_rules:
            prule = rule
            prule += ' {0}'.format(logrule)
            if prule not in buffer_rules:
                buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if limit and (log or audit):
        buffer_rules = []
        logrule = ' limit value="{0}"'.format(limit)
        for rule in to_add_rules:
            prule = rule
            prule += ' {0}'.format(logrule)
            if prule not in buffer_rules:
                buffer_rules.append(prule)
        to_add_rules = buffer_rules

    if action:
        buffer_rules = []
        for rule in to_add_rules:
            if not action_allowed(rule):
                if rule not in buffer_rules:
                    buffer_rules.append(rule)
                continue
            prule = rule
            prule += ' {0}'.format(action)
            if prule not in buffer_rules:
                buffer_rules.append(prule)
        to_add_rules = buffer_rules

    for rule in to_add_rules:
        if (
            rule.strip() and
            rule not in rules and
            rule not in ['rule']
        ):
            rules.append(rule)

    return rules


def complete_address(address):
    if (
        isinstance(address, six.string_types) and
        address and
        'address=' not in address
    ):
        address = 'address="{0}"'.format(address)
    return address


def get_public_ips(cache=True, data=None, ttl=120):
    if not cache:
        ttl = 0

    def _do(data):
        if not data:
            data = cached_default_settings()
        running_net = __salt__['mc_network.default_net']()
        net = __salt__['mc_network.settings']()
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
        for iface, ips in running_net.get('gifaces', []):
            if ifc not in ifcs:
                continue
            for addr in ips:
                if addr:
                    public_ips.add(addr)
        for interfaces in net.get('ointerfaces', []):
            for ifc, odata in six.iteritems(interfaces):
                ifc = ifc.replace('_', ':')
                if ifc not in ifcs:
                    continue
                addr = odata.get('address', '')
                if addr:
                    public_ips.add(addr)
        public_ips = list(public_ips)

        def _filter_local(is_public):
            def do(ip):
                if is_public:
                    return __salt__['mc_network.is_public'](ip)
                else:
                    return not __salt__['mc_network.is_loopback'](ip)
            return do

        # filter public_ips only if if have at least one public ip*
        # this enable to work on private only networks
        is_public = False
        for i in public_ips[:]:
            if __salt__['mc_network.is_public'](i):
                is_public = True
                break
        # if containers, we assume that all ips are dealed the same way.
        if test_container(data):
            is_public = False
        public_ips = filter(_filter_local(is_public), public_ips)
        return public_ips
    cache_key = __name + 'get_public_ips'
    return __salt__['mc_utils.memoize_cache'](
        _do, [data], {}, cache_key, ttl)


def rich_rules(family='ipv4',
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
               icmp_block=None,
               masquerade=False,
               action='accept',
               public_ips=None,
               protocols=None):
    '''
    Helper to generate rich rules compatibles with firewalld

    see firewalld.richlanguage(5) (man)

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

    address_protocols = protocols
    if not address_protocols:
        address_protocols = []

    if not protocols:
        protocols = ['udp', 'tcp']
    if not forward_ports:
        forward_ports = []

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

    forward_ports = forward_ports[:]
    if forward_port and forward_port not in forward_ports:
        forward_ports.append(forward_port)
    forward_ports = [a for a in forward_ports if isinstance(a, dict)]

    if not services:
        services = []
    services = services[:]
    if service and service not in services:
        services.append(service)
    services = [a for a in services if a]

    if not family:
        family = 'ipv4'

    if not sources:
        sources = []
    sources = sources[:]
    if source and source not in sources:
        sources.append(source)

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

    sources = [complete_address(d) for d in sources]
    lsources = [a for a in sources if a]

    if not family:
        raise ValueError(
            'At least one network family must be selected')

    # masquerade is a special beast, and only masquerading rules
    # can be comined in one call
    if masquerade:
        rules = complete_rich_rules(rules,
                                    family=family,
                                    masquerade=masquerade,
                                    sources=lsources,
                                    destinations=destinations,
                                    log=log,
                                    log_level=log_level,
                                    log_prefix=log_prefix,
                                    limit=limit)
        return rules

    # icmp_block is a special beast, and only icmp_block rules
    # can be comined in one call
    if icmp_block:
        rules = complete_rich_rules(rules,
                                    family=family,
                                    icmp_block=icmp_block,
                                    sources=lsources,
                                    destinations=destinations,
                                    log=log,
                                    log_level=log_level,
                                    log_prefix=log_prefix,
                                    limit=limit)
        return rules

    # ports based rules
    if ports:
        rules = complete_rich_rules(rules,
                                    family=family,
                                    sources=sources,
                                    destinations=public_ips,
                                    audit=audit,
                                    ports=ports,
                                    log=log,
                                    log_level=log_level,
                                    log_prefix=log_prefix,
                                    limit=limit,
                                    action=action)

        # forward ports based rules
    if forward_ports:
        rules = complete_rich_rules(rules,
                                    family=family,
                                    sources=sources,
                                    destinations=public_ips,
                                    audit=audit,
                                    forward_ports=nforward_ports,
                                    log=log,
                                    log_level=log_level,
                                    log_prefix=log_prefix,
                                    limit=limit,
                                    action=action)

    # services based rules
    if services:
        rules = complete_rich_rules(rules,
                                    family=family,
                                    sources=sources,
                                    destinations=public_ips,
                                    audit=audit,
                                    services=services,
                                    log=log,
                                    log_level=log_level,
                                    log_prefix=log_prefix,
                                    limit=limit,
                                    action=action)

    # source or dest only based rules
    if (
        ((sources or destinations) and protocols) and
        not (masquerade or
             ports or
             services or
             forward_ports)
    ):
        rules = complete_rich_rules(rules,
                                    family=family,
                                    sources=sources,
                                    destinations=destinations,
                                    audit=audit,
                                    log=log,
                                    log_level=log_level,
                                    log_prefix=log_prefix,
                                    limit=limit,
                                    protocols=address_protocols,
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
    notinternal = []
    for z in data.get('zones', {}):
        if z not in data.get('internal_zones', []):
            notinternal.append(z)
            continue
        zdata = data['zones'][z]
        for ifc in zdata.get('interfaces', []):
            for network in natted.get(ifc, []):
                to_nat.add(network)
    if not notinternal:
        notinternal = None

    # do not automatically nat networks on containers
    # users will have to setup rules manually
    # but instead, we allow each local network, if ...
    # it is local to connect, bindly.
    if data['allow_local']:
        for network in data['local_networks']:
            nw = network.split('/')[0]
            if __salt__['mc_network.is_public'](nw):
                continue
            add_rule(data=data,
                     zones=notinternal,
                     source='address="{0}"'.format(network),
                     action='accept')
    if not test_container(data):
        for network in to_nat:
            add_rule(data=data,
                     zones=notinternal,
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
        allow_local
            force all traffic from rfc1918 to be accepted
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

    PER ZONE SETTINGS

    You can configure zone settings via via entries in the zone pillar

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
    are merged

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


    Whitelist some services:

        .. code-block:: yaml

            makina-states.services.firewall.firewalld.public_services-append:
                - smtp

    Change whitelisted services:

        .. code-block:: yaml

            makina-states.services.firewall.firewalld.public_services: [http]

    Define a new service:

        .. code-block:: yaml

            makina-states.services.firewall.firewalld.services.foo:
                port: [{protocol: tcp, port: 2222}]

    NOTE
       **DO NOT ACTIVATE MASQUERADING, IT IS TOO MUCH CATCHY**
        PLEASE USE APPROPRIATE RESTRICTIVES RICH MASQUERADE RULES
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
