# -*- coding: utf-8 -*-
'''

.. _module_mc_ms_iptables:

mc_ms_iptables / iptables functions
============================================



'''

# Import python libs
import logging
import copy
import mc_states.api


__name = 'ms_iptables'
six = mc_states.api.six
PREFIX = 'makina-states.services.firewall.{0}'.format(__name)
logger = logging.getLogger(__name__)
LOCAL_NETS = ['10.0.0.0/8', '192.168.0.0/16', '172.16.0.0/12']


def prefered_ips(ips, ttl=60, *args, **kw):
    def _do(*a, **k):
        return mc_states.api.prefered_ips(*a, **k)
    cache_key = __name + '.prefered_ips{0}'.format(ips)
    return __salt__['mc_utils.memoize_cache'](
        _do, [ips], {}, cache_key, ttl)


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


def default_settings():
    _s = __salt__
    DEFAULTS = {
        'config': {
            'ipv6': True,
            'load_default_open_policies': True,
            'load_default_hard_policies': True,
            'load_default_flush_rules': True,
            'load_default_rules': True,
            'policy': 'hard',
            'open_policies': [],
            'hard_policies': [],
            'flush_rules': [],
            'rules': [],
        },
        #
        'have_rpn': _s['mc_provider.have_rpn'](),
        'have_docker': _s['mc_network.have_docker_if'](),
        'have_vpn': _s['mc_network.have_vpn_if'](),
        'packages': ['iptables'],
        'have_lxc': _s['mc_network.have_lxc_if'](),
        'no_salt': False,
        'no_burp': False,
        'no_cloud': False,
        'no_slapd': True,
        'no_bind': False,
        #
        'public_interfaces': ['eth0', 'br0'],
        'permissive_mode': is_permissive(),
        'is_container': __salt__['mc_nodetypes.is_container'](),
        'disabled': False,
        'extra_confs': {
            '/etc/default/ms_iptables': {},
            '/etc/ms_iptables.json': {'mode': '644'},
            '/etc/init.d/ms_iptables': {'mode': '755'},
            '/etc/systemd/system/ms_iptables.service': {'mode': '644'},
            '/usr/bin/ms_iptables.py': {'mode': '755', 'template': False}
        }
    }
    data = _s['mc_utils.defaults'](PREFIX, DEFAULTS)
    if data['permissive_mode']:
        data['config']['policy'] = 'open'
        data['config']['load_default_rules'] = False
    return data


def get_public_ips(cache=True, data=None, ttl=120):
    if not cache:
        ttl = 0

    def _do(data):
        if not data:
            data = default_settings()
        running_net = __salt__['mc_network.default_net']()
        net = __salt__['mc_network.settings']()
        ifcs = set()
        public_ips = set()

        for ifc in data['public_interfaces']:
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
                if ':' in ip:
                    return False
                elif is_public:
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
        if data['is_container']:
            is_public = False
        public_ips = filter(_filter_local(is_public), public_ips)
        return public_ips
    cache_key = __name + 'get_public_ips'
    return __salt__['mc_utils.memoize_cache'](
        _do, [data], {}, cache_key, ttl)


def add_nat(port_s,
            to_addr,
            to_port=None,
            binaries=None,
            insert=False,
            protocols=None,
            source=None,
            destination=None,
            policy='ACCEPT',
            add_forward=True,
            rules=None):
    to_dest = '--to {0}'.format(to_addr)
    if isinstance(port_s, (float, int)):
        port_s = str(port_s)
    if isinstance(to_port, (float, int)):
        to_port = str(to_port)
    if to_port and (
        (':' in port_s or ',' in port_s) and
        (':' not in to_port)
    ):
        to_port = None
    if to_port:
        to_dest += ':{0}'.format(to_port.replace(':', '-'))
    if insert:
        insert = 'I'
    else:
        insert = 'A'
    if rules is None:
        rules = []
    if not protocols:
        protocols = ['tcp']
    if isinstance(protocols, six.string_types):
        protocols = protocols.split(',')
    if not binaries:
        binaries = ['iptables']
    for binary in binaries:
        for proto in protocols:
            if not source:
                source = ''
            if not destination:
                destination = ''
            if source and ('-s' not in source):
                source = '-s {0}'.format(source)
            if destination and ('-d' not in destination):
                destination = '-d {0}'.format(destination)
            rule = ('{binary} -w -t nat'
                    ' -{insert} PREROUTING'
                    ' -p {proto} --dport {port_s}'
                    ' {source} {destination}'
                    ' -j DNAT {to_dest}').format(**locals())
            if rule not in rules:
                rules.append(rule)
            if add_forward:
                add_ports(port_s, chain='FORWARD',
                          protocols=protocols,
                          destination=to_addr,
                          rules=rules)
    return rules


def add_ports(port_s,
              binaries=None,
              insert=True,
              protocols=None,
              table='filter',
              chain='INPUT',
              source=None,
              destination=None,
              policy='ACCEPT',
              rules=None):
    if isinstance(port_s, (float, int)):
        port_s = str(port_s)
    if insert:
        insert = 'I'
    else:
        insert = 'A'
    if rules is None:
        rules = []
    if not protocols:
        protocols = ['tcp']
    if isinstance(protocols, six.string_types):
        protocols = protocols.split(',')
    if not binaries:
        binaries = ['iptables']
    for binary in binaries:
        for proto in protocols:
            if not source:
                source = ''
            if not destination:
                destination = ''
            if source and ('-s' not in source):
                source = '-s {0}'.format(source)
            if destination and ('-d' not in destination):
                destination = '-d {0}'.format(destination)
            rule = ('{binary} -w -t {table}'
                    ' -{insert} {chain}'
                    ' -m state --state new'
                    ' {source} {destination}'
                    ' -m multiport -p {proto}'
                    ' --dports {port_s}'
                    ' -j {policy}'
                    '').format(**locals())
            if rule not in rules:
                rules.append(rule)
    return rules


def add_services_policies(data=None):
    _s = __salt__
    if data is None:
        data = default_settings()
    burpsettings = _s['mc_burp.settings']()
    controllers_registry = _s['mc_controllers.registry']()
    services_registry = _s['mc_services.registry']()
    rules = data['config']['rules']
    if not data.get('no_slapd', False):
        if services_registry['is']['dns.slapd']:
            add_ports('389,636', rules=rules)
    if not data.get('no_bind', False):
        if services_registry['is']['dns.bind']:
            add_ports('53', protocols=['tcp', 'udp'], rules=rules)
    if not data.get('no_burp', False):
        if services_registry['is']['backup.burp.server']:
            sources = [a for a in burpsettings['clients']]
            sources += [a for a in burpsettings.get(
                'whitelist', [])]
            if not sources:
                sources = ['127.0.0.1']
            if not sources:
                sources = []
            sources = _s['mc_utils.uniquify'](prefered_ips(sources))
            for s in sources:
                add_ports('4971:4974', source=s, rules=rules)
    return data


def add_cloud_proxies(data):
    _s = __salt__
    if data is None:
        data = default_settings()
    # handle makinastates / compute node redirection ports
    if _s['mc_cloud.is_compute_node']():
        cloud_reg = _s['mc_cloud_compute_node.settings']()
        cloud_rules = cloud_reg.get(
            'reverse_proxies', {}).get('network_mappings', [])
        for port, portdata in six.iteritems(cloud_rules):
            if portdata.get('portRange', None):
                hport = portdata['hostPortRange']
                kw = {'to_addr': portdata['to_addr'],
                      'to_port': portdata['portRange'],
                      'protocols': [portdata['protocol']],
                      'rules': data['config']['rules']}
            else:
                kw = {'to_addr': portdata['to_addr'],
                      'to_port': portdata['port'],
                      'protocols': [portdata['protocol']],
                      'rules': data['config']['rules']}
                hport = portdata['hostPort']
            # on hosted nodes, do not blindly map the target port
            # to an host port if not destination has been explicitly
            # be chosen
            if data['public_ips']:
                for ip in data['public_ips']:
                    dkw = copy.deepcopy(kw)
                    dkw['rules'] = data['config']['rules']
                    dkw['destination'] = ip
                    add_nat(hport, **dkw)
            else:
                add_nat(hport, **kw)
    return data


def settings():
    '''
    iptables simple firewall based  settings
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = default_settings()
        data['public_ips'] = get_public_ips(data=data)
        data = add_services_policies(data)
        data = add_cloud_proxies(data)
        return data
    return _settings()
