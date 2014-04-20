# -*- coding: utf-8 -*-
'''

.. _module_mc_shorewall:

mc_shorewall / shorewall functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils
from salt.utils.odict import OrderedDict

__name = 'shorewall'

log = logging.getLogger(__name__)


def settings():
    '''
    shorewall settings

    makina-states.services.shorewall.enabled: activate shorewall

    It will also assemble pillar slugs to make powerfull firewalls
    by parsing all **\*-makina-shorewall** pillar entries to load the special shorewall structure:

    All entries are merged in the lexicograpĥical order

    item-makina-shorewall
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

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        services_registry = __salt__['mc_services.registry']()
        controllers_registry = __salt__['mc_controllers.registry']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locs = __salt__['mc_locations.settings']()
        shwIfformat = 'FORMAT 2'
        #if ((grains['os'] not in ['Debian'])
        #   and (grains.get('lsb_distrib_codename') not in ['precise'])):
        if (grains['os'] not in ['Debian']):
            shwIfformat = '?{0}'.format(shwIfformat)
        if grains.get('lsb_distrib_codename') in ['precise']:
            shwIfformat = '#?{0}'.format(shwIfformat)
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.firewall.shorewall', {
                # mapping of list of mappings
                'interfaces': OrderedDict(),
                'params': OrderedDict(),
                'rules': [],
                'policies': [],
                'zones': OrderedDict(),
                'masqs': [],
                'default_params': OrderedDict(),
                'default_masqs': [],
                'default_interfaces': OrderedDict(),
                'default_policies': [],
                'default_rules': [],
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
                'no_invalid': True,
                'no_snmp': True,
                'no_mysql': True,
                'no_salt': True,
                'no_mastersalt': False,
                'no_postgresql': True,
                'no_ftp': True,
                'have_docker': None,
                # backward compat
                'have_rpn':  __salt__['mc_provider.settings']()['have_rpn'],
                'have_lxc': None,
                'no_dns': False,
                'no_ping': False,
                'no_smtp': False,
                'no_ssh': False,
                'no_web': False,
                'no_syslog': False,
                'no_computenode': False,
                'defaultstate': 'new',
                'ifformat': shwIfformat,
                # retro compat
                'enabled': __salt__['mc_utils.get'](
                    'makina-states.services.shorewall.enabled', True),

            })
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
        ifaces = grains['ip_interfaces'].items()
        # search & autodetect for well known network interfaces bridges
        # to activate in case default rules for lxc & docker
        if data['have_lxc'] is None:
            if True in ['lxc' in a[0] for a in ifaces]:
                data['have_lxc'] = True  # must stay none if not found
        if data['have_docker'] is None:
            if True in ['docker' in a[0] for a in ifaces]:
                data['have_docker'] = True  # must stay none if not found

        bridged_opts = 'routeback,bridge,tcpflags,nosmurfs,logmartians'
        phy_opts = ('tcpflags,dhcp,nosmurfs,routefilter,'
                    'logmartians,sourceroute=0')
        iface_opts = {
            'net': phy_opts,
            'rpn': phy_opts,
            'lxc': bridged_opts,
            'dck': bridged_opts,
        }
        # service access restrictions
        # enable all by default, but can by overriden easily in config
        # this will act at shorewall parameters in later rules
        if not data['no_default_params']:
            for p in ['SYSLOG', 'SSH', 'SNMP', 'PING',
                      'MYSQL', 'POSTGRESQL', 'FTP']:
                default = 'all'
                if p in ['SYSLOG']:
                    default = 'fw:127.0.0.1'
                data['default_params'].setdefault(
                    'RESTRICTED_{0}'.format(p), default)
            for r, rdata in data['default_params'].items():
                data['params'].setdefault(r, rdata)

        # if we have no enough information, but shorewall is activated,
        # construct a simple firewall allowing ssh icmp, and web traffic
        if not data['no_default_zones']:
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
                if not z in data['default_interfaces']:
                    data['zones'].setdefault(z, data['default_zones'][z])

        for iface, ips in ifaces:
            if 'lo' in iface:
                continue
            z = 'net'
            # TODO: XXX: find better to mach than em1
            if 'em1' == iface:
                if data['have_rpn']:
                    z = 'rpn'
                else:
                    continue
            if 'docker' in iface:
                if data['have_docker']:
                    z = 'dck'
            if 'lxc' in iface:
                if data['have_lxc']:
                    z = 'lxc'
            data['default_interfaces'].setdefault(z, [])
            data['default_interfaces'][z].append({
                'interface': iface, 'options': iface_opts[z]})

        for z, ifaces in data['default_interfaces'].items():
            for iface in ifaces:
                data['interfaces'].setdefault(z, [])
                if not iface in data['interfaces'][z]:
                    data['interfaces'][z].append(iface)

        default_route = __grains__.get('makina.default_route', OrderedDict())
        # default mode: masquerading on the interface containing
        # the default route for lxc and docker containers
        # later, we will add maybe support for failover ip bridges/ vmac
        default_lxc_docker_mode = 'masq'
        default_if = [a for a in ifaces][0]
        if default_route:
            default_if = default_route['iface']
        if default_lxc_docker_mode == 'masq':
            for z, ifaces in data['interfaces'].items():
                if 'lxc' in z or 'dck' in z:
                    for iface in ifaces:
                        mask = {'interface': default_if,
                                'source': iface['interface']}
                        if not mask in data['default_masqs']:
                            data['default_masqs'].append(mask)

        if not data['no_default_masqs']:
            # fw -> net: auth
            for m in data['default_masqs']:
                if not m in data['masqs']:
                    data['masqs'].append(m)

        if not data['no_default_policies']:
            # fw -> defined zones: auth
            for z in data['zones']:
                data['default_policies'].append({
                    'source': '$FW', 'dest': z, 'policy': 'ACCEPT'})

            # dck -> net: auth
            # dck -> dck: auth
            # lxc -> dck: auth
            # dck -> lxc: auth
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
                    'policy': 'DROP', 'loglevel': 'info'})
                data['default_policies'].append({
                    'source': '$FW', 'dest': 'rpn', 'policy': 'ACCEPT'})

            # drop all traffic by default
            data['default_policies'].append({
                'source': 'all', 'dest': 'all',
                'policy': 'REJECT', 'loglevel': 'info'})
            data['default_policies'].append({
                'source': 'net', 'dest': 'all',
                'policy': 'DROP', 'loglevel': 'info'})

        # ATTENTION WE MERGE, so reverse order to append at begin
        data['default_policies'].reverse()
        for rdata in data['default_policies']:
            if not rdata in data['policies']:
                data['policies'].insert(0, rdata)

        if not data['no_default_rules']:
            data['default_rules'].append({'comment': 'invalid traffic'})
            if data['no_invalid']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append({
                'action': 'Invalid({0})'.format(action),
                'source': 'net', 'dest': 'all'})

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
            data['default_rules'].append(
                {'comment': '(Master)Salt on localhost'})
            data['default_rules'].append({'action': 'ACCEPT',
                                          'source': "$FW", 'dest': "$FW",
                                          'proto': 'tcp,udp',
                                          'dport': '4505,4506,4605,4606'})
            if data['have_lxc']:
                data['default_rules'].append(
                    {'comment': '(Master)Salt on lxc'})
                data['default_rules'].append({'action': 'ACCEPT',
                                              'source': "lxc", 'dest': "$FW",
                                              'proto': 'tcp,udp',
                                              'dport': '4505,4506,4605,4606'})
            if data['have_docker']:
                data['default_rules'].append(
                    {'comment': '(Master)Salt on dockers'})
                data['default_rules'].append({'action': 'ACCEPT',
                                              'source': "dck", 'dest': "$FW",
                                              'proto': 'tcp,udp',
                                              'dport': '4505,4506,4605,4606'})

            # enable compute node redirection port ange if any
            # XXX: this is far from perfect, now we open a port range which
            # will be avalaible for connection and the controller will use that
            cloud_c_settings = __salt__['mc_cloud_compute_node.settings']()
            is_compute_node = __salt__['mc_cloud_compute_node.is_compute_node']()
            if is_compute_node and not data['no_computenode']:
                cstart, cend = (
                    cloud_c_settings['ssh_port_range_start'],
                    cloud_c_settings['ssh_port_range_end'],
                )
                data['default_rules'].append(
                    {'comment': 'corpus computenode'})
                data['default_rules'].append({'action': 'ACCEPT',
                                              'source': 'all', 'dest': 'fw',
                                              'proto': 'tcp,udp',
                                              'dport': (
                                                  '{0}:{1}'
                                              ).format(cstart, cend)})
            # enable mastersalt traffic if any
            if (
                controllers_registry['is']['mastersalt_master']
                and not data['no_mastersalt']
            ):
                data['default_rules'].append({'comment': 'mastersalt'})
                data['default_rules'].append({'action': 'ACCEPT',
                                              'source': 'all', 'dest': 'fw',
                                              'proto': 'tcp,udp',
                                              'dport': '4605,4606'})
            # enable salt traffic if any
            if (
                controllers_registry['is']['salt_master']
                and not data['no_salt']
            ):
                    data['default_rules'].append({'comment': 'salt'})
                    data['default_rules'].append({'action': 'ACCEPT',
                                                  'source': 'all',
                                                  'dest': 'fw',
                                                  'proto': 'tcp,udp',
                                                  'dport': '4505,4506'})

            data['default_rules'].append({'comment': 'dns'})
            if data['no_dns']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append({'action': 'DNS({0})'.format(action),
                                          'source': 'all', 'dest': 'all'})

            data['default_rules'].append({'comment': 'web'})
            if data['no_web']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append({'action': 'Web({0})'.format(action),
                                          'source': 'all', 'dest': 'all'})

            data['default_rules'].append({'comment': 'ssh'})
            if data['no_ssh']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append({'action': 'SSH({0})'.format(action),
                                          'source': '$SALT_RESTRICTED_SSH',
                                          'dest': 'all'})
            data['default_rules'].append({'comment': 'syslog'})
            if data['no_syslog']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append({'action': 'Syslog({0})'.format(action),
                                          'source': '$SALT_RESTRICTED_SYSLOG',
                                          'dest': 'all'})

            data['default_rules'].append({'comment': 'ping'})
            # restricting ping is really a awkard bad idea
            # for ping, we drop and only accept from restricted (default: all)
            # data['default_rules'].append({
            #     'action': 'Ping(DROP)'.format(action),
            #     'source': 'net', 'dest': '$FW'})
            # if data['no_ping']:
            #     action = 'DROP'
            # else:
            #     action = 'ACCEPT'
            # data['default_rules'].append({'action': 'Ping({0})'.format(action),
            #                               'source': '$SALT_RESTRICTED_PING',
            #                               'dest': '$FW'})
            # limiting ping
            # for ping, we drop and only accept from restricted (default: all)
            data['default_rules'].append({
                'action': 'Ping(ACCEPT)'.format(action),
                'source': 'net',
                'dest': '$FW',
                'rate': 's:10/min:10'})
            for z in [a for a in data['zones'] if not a in ['net']]:
                data['default_rules'].append({
                    'action': 'Ping(ACCEPT)'.format(action),
                    'source': z,
                    'dest': '$FW'})

            data['default_rules'].append({'comment': 'smtp'})
            if data['no_smtp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append({'action': 'Mail({0})'.format(action),
                                          'source': 'all', 'dest': 'all'})

            data['default_rules'].append({'comment': 'snmp'})
            if data['no_snmp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append(
                {'action': 'SNMP({0})'.format(action),
                 'source': '$SALT_RESTRICTED_SNMP', 'dest': 'all'})

            data['default_rules'].append({'comment': 'ftp'})
            if data['no_ftp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append(
                {'action': 'FTP({0})'.format(action),
                 'source': '$SALT_RESTRICTED_FTP', 'dest': 'all'})

            data['default_rules'].append({'comment': 'postgresql'})
            if data['no_postgresql']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append({
                'action': 'PostgreSQL({0})'.format(action),
                'source': '$SALT_RESTRICTED_POSTGRESQL', 'dest': 'all'})

            data['default_rules'].append({'comment': 'mysql'})
            if data['no_mysql']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            data['default_rules'].append({
                'action': 'MySQL({0})'.format(action),
                'source': '$SALT_RESTRICTED_MYSQL', 'dest': 'all'})
        # ATTENTION WE MERGE, so reverse order to append at begin
        data['default_rules'].reverse()
        for rdata in data['default_rules']:
            if not rdata in data['rules']:
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
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
