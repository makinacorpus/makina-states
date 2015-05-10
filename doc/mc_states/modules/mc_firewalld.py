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
    for fml in families:
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
                    add_dest_rules([], rules, rule, endrule)
            for svc in services:
                rule = 'rule'
                if family:
                    rule += ' family="{0}"'.format(fml)
                if src and src not in ['address="0.0.0.0"']:
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
            if src and not (ports or services):
                rule = 'rule'
                if family:
                    rule += ' family="{0}"'.format(fml)
                if src and src not in ['address="0.0.0.0"']:
                    rule += ' source {0}'.format(src)
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
    count = data.setdefault('aliases', 100)
    for i in data['aliased_interfaces']:
        # add eth0:x to the same zone for the 100th
        for c in range(count):
            j = '{0}:{1}'.format(i, c)
            if j in cfgs:
                continue
            for z in zonesn:
                ifs = data['zones'][z].get('interfaces', [])
                if i in ifs and j not in ifs:
                    ifs.append(j)
    return data


def add_zones_policies(data=None):
    data = fix_data(data)
    for z in data['public_zones']:
        if data['permissive_mode']:
            t = 'ACCEPT'
        else:
            t = 'REJECT'
        zone = data['zones'].setdefault(z, {})
        zone.setdefault('target', t)
    for z in data['internal_zones']:
        if data['trust_internal']:
            t = 'ACCEPT'
        else:
            t = 'REJECT'
        zone = data['zones'].setdefault(z, {})
        zone.setdefault('target', t)
    for network in data['banned_networks']:
        add_rule(data, source=network, action='drop')
    for network in data['trusted_networks']:
        add_rule(data, source=network, action='accept')
    return data


def add_services_policies(data=None):
    data = fix_data(data)
    _s = __salt__
    burpsettings = _s['mc_burp.settings']()
    for i in ['public_services', 'restricted_services']:
        for s in data[i]:
            data['services'].setdefault(s, {})
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
                policy = policy.upper()
            if not (sources or policy):
                continue
            add_rule(
                data, zones=[z], sources=sources, service=s, action=policy)
    return data


def complete_rules(data):
    for z in [a for a in data['zones']]:
        zdata = data['zones'][z]
        if not isinstance(zdata, dict):
            data['zones'].pop(z, None)
    for z in [a for a in data['zones']]:
        zdata = data['zones'][z]
        rules = zdata.setdefault('rules', [])
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
    DEFAULTS = {
        'is_container': __salt__['mc_nodetypes.is_container'](),
        'aliased_interfaces': [],
        'default_zone': None,
        'aliases': 100,
        'banned_networks': [],
        'trusted_networks': [],
        # list of mappings
        'no_cloud_rules': False,
        'no_default_alias': False,
        'packages': ['ipset', 'ebtables', 'firewalld'],
        'zones': OrderedDict([
            ('block', {}),
            ('drop', {}),
            ('trusted', {'interfaces': ['lo']}),
            ('dmz', {'target': 'ACCEPT'}),
            ('rpn', {'target': 'ACCEPT'}),
            ('virt', {'target': 'ACCEPT',
                      'interfaces': ['virbr0', 'vibr0',
                                     'virbr1', 'vibr1']}),
            ('lxc', {'target': 'ACCEPT',
                     'interfaces': ['lxcbr0', 'lxcbr1']}),
            ('docker', {'target': 'ACCEPT',
                        'interfaces': ['docker0', 'docker1']}),
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
            'imaps': {'port': [{'port': '993'}]}
        },
        #
        'have_rpn': _s['mc_provider.have_rpn'](),
        'have_docker': _s['mc_network.have_docker_if'](),
        'have_vpn': _s['mc_network.have_vpn_if'](),
        'have_lxc': _s['mc_network.have_lxc_if'](),
        #
        'permissive_mode': is_permissive(),
        'trust_internal': None,
        'extra_confs': {'/etc/default/firewalld': {}},
        # retro compat
        'enabled': _s['mc_utils.get'](
            'makina-states.services.firewalld.enabled', True)}
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


def add_cloud_proxies(data):
    _s = __salt__
    # handle makinastates / compute node redirection ports
    if _s['mc_cloud.is_compute_node']():
        cloud_reg = _s['mc_cloud_compute_node.settings']()
        cloud_rules = cloud_reg.get(
            'reverse_proxies', {}).get('network_mappings', [])
        for portdata in cloud_rules:
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

    Add some rich rules in pillar to a zone, all
    ``makina-states.services.firewall.firewalld.zones.public.rules<id>``
    are merged ::

    .. code-block:: yaml

        makina-states.services.firewall.firewalld.zones.public.rules-foo:
          {% for i in salt['mc_firewalld.rich_rules'](
            port=22, action='drop'
          )- {{i}} {% endfor %}
          {% for i in salt['mc_firewalld.rich_rules'](
            forward_port={'port': 1122, 'addr': '1.2.3.4'}, 'port'=22
          )- {{i}} {% endfor %}
        makina-states.services.firewall.firewalld.zones.public.rules-bar:
          - "rule service name="ftp" log limit value="1/m" audit accept"
          {% for i in salt['mc_firewalld.rich_rules'](
            port=22, destinations=['127.0.0.1'],  action='drop'
          )- {{i}} {% endfor %}
          {% for i in salt['mc_firewalld.rich_rules'](
              port=22, destinations=['not address="127.0.0.2"'],  action='drop'
          )- {{i}} {% endfor %}

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
        data = add_services_policies(data)
        data = add_cloud_proxies(data)
        return data
    return _settings()
