# -*- coding: utf-8 -*-
'''

.. _module_mc_shorewall:

mc_shorewall / shorewall functions
============================================



'''

# Import python libs
import socket
import logging
import traceback
from distutils.version import LooseVersion
import mc_states.api
import ipaddr
from salt.utils.odict import OrderedDict

__name = 'shorewall'

log = logging.getLogger(__name__)
prefered_ips = mc_states.api.prefered_ips


def guess_shorewall_ver():
    ver = __salt__['cmd.run']('shorewall version', python_shell=True)
    for i in ['3' '4', '5']:
        if i in ver:
            return ver
    if __grains__['os'] in ['Debian']:
        if __grains__['osrelease'][0] < '6':
            osver = 'old_deb'
        else:
            osver = 'deb'
    else:
        osver = 'ubuntu'
    if __grains__.get('lsb_distrib_codename') in ['precise']:
        osver = 'precise'
    ver = {
        'old_deb': '4.0.15',
        'deb': '4.5.0',
        'precise': '4.4.26',
        'ubuntu': '4.5.17',
    }.get(osver, '4.5.17')
    return ver


def get_macro(name, action, immediate=True):
    if guess_shorewall_ver() < '4.5.10':
        fmt = '{name}/{action}'
    else:
        fmt = '{name}({action})'
    return fmt.format(name=name, action=action)


def append_rules_for_zones(default_rules, rules, zones=None):
    if not isinstance(rules, list):
        rules = [rules]
    if not zones:
        zones = ['all']
    for rule in rules:
        if 'comment' in rule:
            default_rules.append(rule)
        else:
            for zone in zones:
                crule = rule.copy()
                crule['dest'] = zone
                default_rules.append(crule)


def settings():
    '''
    shorewall settings

    makina-states.services.shorewall.enabled: activate shorewall

    It will also assemble pillar slugs to make powerfull firewalls
    by parsing all **\*-makina-shorewall** pillar entries to load the special shorewall structure:

    All entries are merged in the lexicograpĥical order

    makina-states.services.firewall.shorewall:
        interfaces
            TBD
        rules
            TBD
        params
            TBD
        policies
            TBD
        zones
            TBD
        masqs
            TBD
        proxyarp
            TBD
        nat
            TBD

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        protos = ['tcp', 'udp']
        _g = __grains__
        pillar = __pillar__
        data_net = _s['mc_network.default_net']()
        netsettings = _s['mc_network.settings']()
        default_netmask = data_net['default_netmask']
        gifaces = data_net['gifaces']
        default_if = data_net['default_if']
        default_route = data_net['default_route']
        default_net = data_net['default_net']
        services_registry = _s['mc_services.registry']()
        controllers_registry = _s['mc_controllers.registry']()
        nodetypes_registry = _s['mc_nodetypes.registry']()
        locs = _s['mc_locations.settings']()
        providers = _s['mc_provider.settings']()
        have_rpn = providers['have_rpn']
        ulogd = False
        if nodetypes_registry['is']['lxccontainer']:
            ulogd = True

        sw_ver = guess_shorewall_ver()
        shwIfformat = '?FORMAT 2'
        if LooseVersion('4.5.10') >= LooseVersion(sw_ver):
            shwIfformat = '?FORMAT 2'
        if LooseVersion('4.5.10') > LooseVersion(sw_ver) > LooseVersion('4.1'):
            # shwIfformat = 'FORMAT 2'
            shwIfformat = ''
        elif LooseVersion(sw_ver) <= LooseVersion('4.1'):
            shwIfformat = '#?{0}'.format(shwIfformat)
        permissive_mode = False
        if nodetypes_registry['is']['lxccontainer']:
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
        data = _s['mc_utils.defaults'](
            'makina-states.services.firewall.shorewall', {
                # mapping of list of mappings
                'interfaces': OrderedDict(),
                'params': OrderedDict(),
                'rules': [],
                'nat': [],
                'proxyarp': [],
                'policies': [],
                'zones': OrderedDict(),
                'masqs': [],
                'sw_ver': sw_ver,
                'default_params': OrderedDict(),
                'default_masqs': [],
                'default_interfaces': OrderedDict(),
                'default_policies': [],
                'default_rules': [],
                'banned_networks': [],
                'trusted_networks': [],
                'internal_zones': [],
                'default_zones': {'net': OrderedDict(),
                                  'fw': {'type': 'firewall'}},
                'no_default_masqs': False,
                'no_default_params': False,
                'no_default_interfaces': False,
                'no_default_policies': False,
                'no_default_rules': False,
                'no_default_zones': False,
                # list of mappings
                # dict of section/rule mappings parsed from rules
                '_rules': OrderedDict(),
                'no_default_net_bridge': False,
                'no_invalid': True,
                'no_snmp': False,
                'no_mongodb': False,
                'no_mysql': False,
                'no_salt': False,
                'no_postgresql': False,
                'have_docker': None,
                'have_vpn': None,
                # backward compat
                'have_rpn': have_rpn,
                'have_lxc': None,
                'no_dns': False,
                'no_ping': False,
                'no_smtp': False,
                'no_redis': False,
                'no_ssh': False,
                'no_ntp': False,
                'no_web': False,
                'no_ldap': False,
                'no_rabbitmq': False,
                'no_ftp': False,
                'no_burp': False,
                'no_mumble': False,
                'no_syslog': False,
                'no_computenode': False,
                'defaultstate': 'new',
                'permissive_mode': permissive_mode,
                'ifformat': shwIfformat,
                'ulogd': ulogd,
                'configs': {'/etc/shorewall/interfaces': {"mode": "0700"},
                            '/etc/shorewall/masq': {"mode": "0700"},
                            '/etc/shorewall/nat': {"mode": "0700"},
                            '/etc/shorewall/proxyarp': {"mode": "0700"},
                            '/etc/shorewall/params': {"mode": "0700"},
                            '/etc/shorewall/policy': {"mode": "0700"},
                            '/etc/rc.local.d/shorewall.sh': {"makedirs": True,
                                                             "mode": "0755"},
                            '/etc/init.d/shorewall': {"makedirs": True,
                                                      "mode": "0755"},
                            '/etc/init.d/shorewall6': {"makedirs": True,
                                                       "mode": "0755"},
                            '/etc/shorewall/rules': {"mode": "0700"},
                            '/etc/shorewall/shorewall.conf': {"mode": "0700"},
                            '/etc/shorewall/zones': {"mode": "0700"}},
                # retro compat
                'enabled': _s['mc_utils.get'](
                    'makina-states.services.shorewall.enabled', True),

            })
        shareds = ['macro.mongodb']
        if _g['os'] in ['Debian']:
            shareds.extend(['macro.PostgreSQL', 'macro.Mail'])
        for i in shareds:
            data['configs']['/usr/share/shorewall/' + i] = {'mode': "0700"}
        info_loglevel = 'info'
        if data['ulogd']:
            info_loglevel = 'NFLOG'
        # alias for retrocompat
        data['shwInterfaces'] = data['interfaces']
        data['shwPolicies'] = data['policies']
        data['shwParams'] = data['params']
        data['shwZones'] = data['zones']
        data['shwMasqs'] = data['masqs']
        data['shwIfformat'] = data['ifformat']
        data['shwRules'] = data['rules']
        data['shwDefaultState'] = data['defaultstate']
        data['shwEnabled'] = data['enabled']
        data['shw_interfaces'] = data['interfaces']
        data['shw_policies'] = data['policies']
        data['shw_params'] = data['params']
        data['shw_zones'] = data['zones']
        data['shw_masqs'] = data['masqs']
        data['shw_rules'] = data['rules']
        data['shw_defaultState'] = data['defaultstate']
        data['shw_enabled'] = data['enabled']
        # search & autodetect for well known network interfaces bridges
        # to activate in case default rules for lxc & docker
        if data['have_lxc'] is None:
            if True in ['lxc' in a[0] for a in gifaces]:
                data['have_lxc'] = True  # must stay none if not found
        if data['have_docker'] is None:
            if True in ['docker' in a[0] for a in gifaces]:
                data['have_docker'] = True  # must stay none if not found
        if data['have_vpn'] is None:
            if True in [a[0].startswith('tun') for a in gifaces]:
                data['have_vpn'] = True  # must stay none if not found

        opts_45 = ',sourceroute=0'
        bridged_opts = 'routeback,bridge,tcpflags,nosmurfs'
        bridged_net_opts = (
            'bridge,tcpflags,dhcp,nosmurfs,routefilter')
        phy_opts = 'tcpflags,dhcp,nosmurfs,routefilter'
        if sw_ver >= '4.4':
            phy_opts += opts_45
            bridged_net_opts += opts_45
        iface_opts = {
            'vpn': '',
            'net': phy_opts,
            'lan': phy_opts,
            'rpn': phy_opts,
            'brnet': bridged_net_opts,
            'lxc': bridged_opts,
            'dck': bridged_opts,
        }
        # service access restrictions
        # enable all by default, but can by overriden easily in config
        # this will act at shorewall parameters in later rules
        burpsettings = _s['mc_burp.settings']()

        if not data['no_default_params']:
            for p in ['SYSLOG', 'SSH', 'SNMP', 'PING', 'LDAP', 'SALT',
                      'NTP', 'MUMBLE', 'DNS', 'WEB', 'MONGODB', 'RABBITMQ',
                      'BURP', 'MYSQL', 'REDIS', 'POSTGRESQL', 'FTP']:
                default = 'fw:127.0.0.1'
                if p in ['SSH', 'DNS', 'PING', 'WEB', 'MUMBLE']:
                    default = 'all'
                if p == 'BURP':
                    bclients = prefered_ips(burpsettings['clients'])
                    if bclients:
                        default = 'net:'
                        default += ','.join(bclients)
                data['default_params'].setdefault(
                    'RESTRICTED_{0}'.format(p), default)
            for r, rdata in data['default_params'].items():
                data['params'].setdefault(r, rdata)

        # if we have no enough information, but shorewall is activated,
        # construct a simple firewall allowing ssh icmp, and web traffic
        if not data['no_default_zones']:
            if data['have_vpn']:
                data['default_zones']['vpn'] = OrderedDict()
            if data['have_lxc']:
                data['default_zones']['lxc'] = OrderedDict()
            if data['have_docker']:
                data['default_zones']['dck'] = OrderedDict()
            if data['have_rpn']:
                data['default_zones']['rpn'] = OrderedDict()
            for z, zdata in data['default_zones'].copy().items():
                if not zdata:
                    zdata = {'type': 'ipv4'}
                data['default_zones'][z] = zdata
                if z not in data['default_interfaces']:
                    data['zones'].setdefault(z, data['default_zones'][z])

        ems = [i
               for i, ips in gifaces
               if i.startswith('em') and len(i) in [3, 4]]

        has_br0 = 'br0' in [a[0] for a in gifaces]
        # add br0 to the net network even if it does not
        # exists to facilitate switchs from wired nic
        # to bridged nics
        if not data['no_default_net_bridge'] and not has_br0:
            gifaces.append(('br0', []))

        configuredifs = []
        if data['interfaces']:
            for a in data['interfaces'].values():
                for ifc in a:
                    ifcc = ifc.get('interface', None)
                    if ifcc and ifcc not in configuredifs:
                        configuredifs.append(ifcc)
        for iface, ips in gifaces:
            if iface in configuredifs:
                continue
            if iface.startswith('veth'):
                continue
            if 'lo' in iface:
                continue
            z = 'net'
            # TODO: XXX: find better to mach than em1
            if iface.startswith('tun'):
                z = 'vpn'
                data['have_vpn'] = True
            if (
                iface in ['eth1']
                or iface in ems
            ):
                if have_rpn:
                    realrpn = False
                    if iface in ems:
                        if iface == ems[-1]:
                            realrpn = True
                    else:
                        realrpn = True
                    if not providers['is']['online']:
                        realrpn = False
                    if realrpn:
                        z = 'rpn'
            if 'docker' in iface:
                if data['have_docker']:
                    z = 'dck'
            if iface == 'br0':
                z = 'brnet'
            if 'lxc' in iface:
                if data['have_lxc']:
                    z = 'lxc'
            zz = {'brnet': 'net'}.get(z, z)
            data['default_interfaces'].setdefault(zz, [])
            data['default_interfaces'][zz].append({
                'interface': iface, 'options': iface_opts[z]})
        for z, ifaces in data['default_interfaces'].items():
            for iface in ifaces:
                data['interfaces'].setdefault(z, [])
                if iface not in data['interfaces'][z]:
                    data['interfaces'][z].append(iface)
        default_lxc_docker_mode = 'masq'
        if default_lxc_docker_mode == 'masq':
            for z, ifaces in data['interfaces'].items():
                if 'lxc' in z or 'dck' in z:
                    for iface in ifaces:
                        mask = {'interface': default_if,
                                'source': iface['interface']}
                        if mask not in data['default_masqs']:
                            data['default_masqs'].append(mask)

        if not data['no_default_masqs']:
            # fw -> net: auth
            for m in data['default_masqs']:
                if m not in data['masqs']:
                    data['masqs'].append(m)
        end_policies = []
        if not data['no_default_policies']:
            # fw -> defined zones: auth
            for z in data['zones']:
                data['default_policies'].append({
                    'source': '$FW', 'dest': z, 'policy': 'ACCEPT'})

            for z in ['fw'] + [a for a in data['zones']]:
                if z not in data['internal_zones'] and z not in ['net']:
                    data['internal_zones'].append(z)

            # dck -> net: auth
            # dck -> dck: auth
            # lxc -> dck: auth
            # dck -> lxc: auth
            if data['have_vpn']:
                data['default_policies'].append({
                    'source': 'vpn', 'dest': '$FW', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': '$FW', 'dest': 'vpn', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': 'vpn', 'dest': 'all', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': 'all', 'dest': 'vpn', 'policy': 'ACCEPT'})
            if data['have_docker']:
                data['default_policies'].append({
                    'source': 'dck', 'dest': 'net', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': 'dck', 'dest': 'dck', 'policy': 'ACCEPT'})
            if data['have_docker'] and data['have_lxc']:
                data['default_policies'].append({
                    'source': 'dck', 'dest': 'lxc', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': 'lxc', 'dest': 'dck', 'policy': 'ACCEPT'})

            # fw -> lxc: auth
            # lxc -> net: auth
            if data['have_lxc']:
                data['default_policies'].append({
                    'source': 'lxc', 'dest': 'net', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': '$FW', 'dest': 'lxc', 'policy': 'ACCEPT'})

            # rpn -> all: drop
            # fw -> rpn: auth
            if data['have_rpn']:
                data['default_policies'].append({
                    'source': 'rpn', 'dest': 'all',
                    'policy': 'DROP', 'loglevel': info_loglevel})
                data['default_policies'].append({
                    'source': '$FW', 'dest': 'rpn', 'policy': 'ACCEPT'})


            # drop all traffic by default if not in permissive_mode
            if not data['permissive_mode']:
                end_policies.append({
                    'source': 'all', 'dest': 'all',
                    'policy': 'REJECT', 'loglevel': info_loglevel})
                end_policies.append({
                    'source': 'net', 'dest': 'all',
                    'policy': 'DROP', 'loglevel': info_loglevel})
            else:
                end_policies.append({
                    'source': 'all', 'dest': 'all', 'policy': 'ACCEPT'})
                end_policies.append({
                    'source': 'net', 'dest': 'all', 'policy': 'ACCEPT'})

        # ATTENTION WE MERGE, so reverse order to append at begin
        data['default_policies'].reverse()
        end_policies.reverse()
        for rdata in data['default_policies']:
            if rdata not in data['policies']:
                data['policies'].insert(0, rdata)
        data['policies'].extend(end_policies)

        # snmp should be filtered even in permissive mode
        if not data['no_default_rules']:
            data['default_rules'].append({'comment': 'snmp'})
            if data['permissive_mode']:
                if data['no_snmp']:
                    action = 'DROP'
                else:
                    action = 'ACCEPT'
                data['default_rules'].append(
                    {'action': 'ACCEPT!',
                     'source': '$SALT_RESTRICTED_SNMP', 'dest': 'fw',
                     'proto': 'udp', 'dport': '161'})
                data['default_rules'].append(
                    {'action': 'DROP!',
                     'source': 'all', 'dest': 'fw',
                     'proto': 'udp', 'dport': '161'})
            else:
                if data['no_snmp']:
                    action = 'DROP'
                else:
                    action = 'ACCEPT'
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': get_macro('SNMP', action),
                     'source': '$SALT_RESTRICTED_SNMP', 'dest': 'all'},
                    zones=data['internal_zones'])

        if not data['no_default_rules']:
            if nodetypes_registry['is']['lxccontainer']:
                if not data['trusted_networks']:
                    data['trusted_networks'].append('net:{0}/{1}'.format(
                        default_net, default_netmask))
            for network in data['banned_networks']:
                data['default_rules'].insert(
                    0, {'action': 'DROP!', 'source': network, 'dest': 'fw'})
            for network in data['trusted_networks']:
                data['default_rules'].insert(
                    0, {'action': 'ACCEPT!', 'source': network, 'dest': 'fw'})
            data['default_rules'].insert(0, {'comment': 'inter lxc traffic'})
            if sw_ver >= '4.5':
                data['default_rules'].append({'comment': 'invalid traffic'})
                if data['no_invalid']:
                    action = 'DROP'
                else:
                    action = 'ACCEPT'
                append_rules_for_zones(data['default_rules'], {
                    'action': get_macro('Invalid', action),
                    'source': 'net', 'dest': 'all'},
                    zones=data['internal_zones'])

        if not data['no_default_rules'] and not data['permissive_mode']:
            data['default_rules'].append({'comment': 'lxc dhcp traffic'})
            if data['have_lxc']:
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': 'lxc', 'dest': 'fw',
                     'proto': 'udp', 'dport': '67:68'})
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': 'fw', 'dest': 'lxc',
                     'proto': 'udp', 'dport': '67:68'})

            data['default_rules'].append({'comment': 'docker dhcp traffic'})
            if data['have_docker']:
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': 'dck', 'dest': 'fw',
                     'proto': 'udp', 'dport': '67:68'})
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': 'fw', 'dest': 'dck',
                     'proto': 'udp', 'dport': '67:68'})

            # salt/master traffic if any
            append_rules_for_zones(
                data['default_rules'],
                {'comment': '(Master)Salt on localhost'})
            for proto in protos:
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': "$FW", 'dest': "$FW",
                     'proto': proto,
                     'dport': '4505,4506,4605,4606'})
            if data['have_lxc']:
                append_rules_for_zones(data['default_rules'],
                                       {'comment': '(Master)Salt on lxc'})
                for proto in protos:
                    data['default_rules'].append(
                        {'action': 'ACCEPT',
                         'source': "lxc", 'dest': "$FW",
                         'proto': proto,
                         'dport': '4505,4506,4605,4606'})
            if data['have_docker']:
                append_rules_for_zones(data['default_rules'],
                                       {'comment': '(Master)Salt on dockers'})
                for proto in protos:
                    data['default_rules'].append(
                        {'action': 'ACCEPT',
                         'source': "dck", 'dest': "$FW",
                         'proto': proto,
                         'dport': '4505,4506,4605,4606'})
            # DNATed external sources ips
            # force ip
            source_ips = [netsettings.get('main_ip', '-')]
            # search ip failover
            for sifc, sdata in netsettings['interfaces'].items():
                if (
                    ':' in sifc
                    and (sifc.startswith('br') or sifc.startswith('eth'))
                ):
                    addr = sdata.get('address', None)
                    try:
                        # filter on ipv4 and non rfc1918
                        if not ':' in addr:
                            is_private = ipaddr.IPAddress(addr).is_private
                    except Exception:
                        is_private = False
                    if addr and not is_private and not (addr in source_ips):
                        source_ips.append(addr)

            # enable compute node redirection port ange if any
            # XXX: this is far from perfect, now we open a port range which
            # will be avalaible for connection and the controller will use that
            is_compute_node = _s['mc_cloud.is_compute_node']()
            if is_compute_node and not data['no_computenode']:
                try:
                    cloud_rules = []
                    try:
                        cloud_reg = _s['mc_cloud_compute_node.settings']()
                        cloud_rules = cloud_reg.get(
                            'reverse_proxies', {}).get('sw_proxies', [])
                    except Exception:
                        cloud_rules = []
                    if not cloud_rules:
                        # before refactor transition
                        lcloud_reg = _s['mc_cloud_compute_node.cn_settings']()
                        cloud_rules = lcloud_reg.get(
                            'cnSettings', {}).get(
                                'rp', {}).get(
                                    'reverse_proxies', {}).get(
                                        'sw_proxies', [])
                    for r in cloud_rules:
                        rules = []
                        # replace all DNAT rules to use each external ip
                        if ':' in r.get('dest', ''):
                            z = r['dest'].split(':')[0]
                            rr = r.copy()
                            for sip in source_ips:
                                rr['odest'] = sip
                                for i in data['zones']:
                                    if i not in [z, 'fw']:
                                        target_r = rr.copy()
                                        target_r['source'] = i
                                        rules.append(target_r)
                        else:
                            rules.append(r)
                        data['default_rules'].extend(rules)
                except:
                    log.error("ERROR IN CLOUD SHOREWALL RULES")
                    log.error(traceback.format_exc())

            data['default_rules'].append({'comment': 'dns'})
            if data['no_dns']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('DNS', action),
                 'source': 'all', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'web'})
            if data['no_web']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': get_macro('Web', action),
                     'source': '$SALT_RESTRICTED_WEB', 'dest': 'all'},
                    zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ntp'})
            if data['no_ntp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('NTP', action),
                 'source': '$SALT_RESTRICTED_NTP', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ssh'})
            if data['no_ssh']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('SSH', action),
                 'source': '$SALT_RESTRICTED_SSH',
                 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'syslog'})
            if data['no_syslog']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(data[
                'default_rules'],
                {'action': get_macro('Syslog', action),
                 'source': '$SALT_RESTRICTED_SYSLOG',
                 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ping'})
            # restricting ping is really a awkard bad idea
            # for ping, we drop and only accept from restricted (default: all)
            # append_rules_for_zones(data['default_rules'], {
            #     'action': 'Ping(DROP)'.format(action),
            #     'source': 'net', 'dest': '$FW'})
            # if data['no_ping']:
            #     action = 'DROP'
            # else:
            #     action = 'ACCEPT'
            # append_rules_for_zones(data['default_rules'], {'action': 'Ping({0})'.format(action),
            #                               'source': '$SALT_RESTRICTED_PING',
            #                               'dest': '$FW'})
            # limiting ping
            # for ping, we drop and only accept from restricted (default: all)
            rate = 's:10/min:10'
            if sw_ver < '4.4':
                rate = '-'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('Ping', 'ACCEPT'),
                 'source': 'net',
                 'dest': '$FW'},
                zones=data['internal_zones'])

            for z in [a for a in data['zones'] if a not in ['net']]:
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': get_macro('Ping', 'ACCEPT'),
                     'source': z,
                     'dest': '$FW'},
                    zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'smtp'})
            if data['no_smtp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('Mail', action),
                 'source': 'all', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ftp'})
            if data['no_ftp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('FTP', action),
                 'source': '$SALT_RESTRICTED_FTP', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'redis'})
            if data['no_redis']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            for proto in protos:
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': action,
                     'source': '$SALT_RESTRICTED_REDIS',
                     'dest': 'fw',
                     'proto': proto,
                     'dport': '6379'},
                    zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'postgresql'})
            if data['no_postgresql']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('PostgreSQL', action),
                 'source': '$SALT_RESTRICTED_POSTGRESQL', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'mongodb'})
            if data['no_mongodb']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('mongodb', action),
                 'source': '$SALT_RESTRICTED_MONGODB', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'mysql'})
            if data['no_mysql']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('MySQL', action),
                 'source': '$SALT_RESTRICTED_MYSQL', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'rabbitmq'})
            if data['no_rabbitmq']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            for proto in protos:
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': action,
                     'source': '$SALT_RESTRICTED_RABBITMQ',
                     'dest': 'fw',
                     'proto': proto,
                     'dport': '15672'},
                    zones=data['internal_zones'])
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': action,
                     'source': '$SALT_RESTRICTED_RABBITMQ',
                     'dest': 'fw',
                     'proto': proto,
                     'dport': '25672'},
                    zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'mumble'})
            if data['no_mumble']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            for proto in protos:
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': action,
                     'source': '$SALT_RESTRICTED_MUMBLE',
                     'dest': 'fw',
                     'proto': proto,
                     'dport': '64738'},
                    zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ldap'})
            if data['no_ldap']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('LDAP', action),
                 'source': '$SALT_RESTRICTED_LDAP', 'dest': 'all'},
                zones=data['internal_zones'])
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('LDAPS', action),
                 'source': '$SALT_RESTRICTED_LDAP', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'burp'})
            if data['no_burp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            for proto in protos:
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': action,
                     'source': 'fw:127.0.0.1',
                     'dest': "all",
                     'proto': proto,
                     'dport': '4971,4972,4973,4974'},
                    zones=data['internal_zones'])
            for proto in protos:
                for i in ['lxc', 'kvm', 'docker']:
                    if i in data['zones']:
                        append_rules_for_zones(
                            data['default_rules'],
                            {'action': action,
                             'source': i,
                             'dest': "all",
                             'proto': proto,
                             'dport': '4971,4972,4973,4974'},
                            zones=data['internal_zones'])
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': action,
                     'source': '$SALT_RESTRICTED_BURP',
                     'dest': "all",
                     'proto': proto,
                     'dport': '4971,4972,4973,4974'},
                    zones=data['internal_zones'])
            # also accept configured hosts
            burpsettings = _s['mc_burp.settings']()
            clist = prefered_ips(burpsettings['clients'])
            if clist:
                clients = 'net:{0}'.format(','.join(clist))
                for proto in protos:
                    append_rules_for_zones(
                        data['default_rules'], {'action': action,
                                                'source': clients,
                                                'dest': "all",
                                                'proto': proto,
                                                'dport': '4971,4972'},
                        zones=data['internal_zones'])
        # ATTENTION WE MERGE, so reverse order to append at begin
        data['default_rules'].reverse()
        for rdata in data['default_rules']:
            if rdata not in data['rules']:
                data['rules'].insert(0, rdata)

        for i in data['rules']:
            section = i.get('section', data['defaultstate']).upper()
            if section not in data['_rules']:
                data['_rules'].update({section: []})
            data['_rules'][section].append(i)
        # prefix params with salt as it is shell
        params = data['params'].copy()
        data['params'] = OrderedDict()
        for p, value in params.items():
            data['params']['{0}_{1}'.format('SALT', p)] = value
        data['params_keys'] = [a for a in data['params']]
        data['params_keys'].sort()

        return data
    return _settings()
