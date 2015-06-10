# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
import unittest
from .. import base
import mc_states.api
from salt.utils.odict import OrderedDict
import mock

six = mc_states.api.six


def _snets():
    return {
        'main_ip': '1.2.3.6',
        'interfaces': {
            'eth0': {'address': '1.2.3.6'},
        },
        'ointerfaces': [
            {'eth0': {'address': '1.2.3.6'}},
        ],
    }


def _snet():
    return {
        'default_if': 'eth0br0',
        'default_route': '1.2.3.1',
        'gifaces': (
            ('eth0', ['1.2.3.6']),
        )
    }


def _nets():
    return {
        'main_ip': '1.2.3.6',
        'interfaces': {
            'eth0': {'address': '1.2.3.6'},
            'eth0_0': {'address': '1.2.3.8'}
        },
        'ointerfaces': [
            {'eth0': {'address': '1.2.3.6'}},
            {'eth0_0': {'address': '1.2.3.8'}},
        ],
    }


def _net():
    return {
        'default_if': 'br0',
        'default_route': '1.2.3.1',
        'gifaces': (
            ('em0', ['1.2.3.4']),
            ('em1', ['1.2.3.4']),
            ('em2', ['1.2.3.4']),
            ('em3', ['1.2.3.4']),
            ('eth0_666', ['1.2.3.7',
                          '127.0.0.1',
                          '10.1.1.1',
                          '192.168.1.1',
                          '172.16.1.1']),
            ('eth0_0', ['1.2.3.5']),
            ('eth0', ['1.2.3.4']),
            ('eth1', ['1.2.3.4']),
            ('br0', ['1.2.3.4']),
            ('br0,0', ['1.2.3.4']),
            ('docker0', ['1.2.3.4']),
            ('docker1', ['1.2.3.4']),
            ('lxcbr0', ['1.2.3.4']),
            ('lxcbr1', ['1.2.3.4']),
            ('xenbr0', ['1.2.3.4']),
            ('xenbr1', ['1.2.3.4']),
            ('virt0', ['1.2.3.4']),
            ('virt1', ['1.2.3.4']),
            ('vibr0', ['1.2.3.4']),
            ('vibr1', ['1.2.3.4']),
            ('lo', ['1.2.3.4']),
            # ('veth1', ['1.2.3.4']),
            ('tun1', ['1.2.3.4']),
            ('tap1', ['1.2.3.4'])
        )
    }


def _local_nets():
    return {
        'main_ip': '192.168.0.6',
        'interfaces': {
            'eth0': {'address': '192.168.0.6'},
            'eth0_0': {'address': '192.168.0.8'}
        },
        'ointerfaces': [
            {'eth0': {'address': '192.168.0.6'}},
            {'eth0_0': {'address': '192.168.0.8'}},
        ],
    }


def _local_net():
    return {
        'default_if': 'br0',
        'default_route': '192.168.0.1',
        'gifaces': (
            ('em0', ['192.168.0.4']),
            ('em1', ['192.168.0.4']),
            ('em2', ['192.168.0.4']),
            ('em3', ['192.168.0.4']),
            ('eth0_666', ['192.168.0.7',
                          '127.0.0.1',
                          '10.1.1.1',
                          '192.168.1.1',
                          '172.16.1.1']),
            ('eth0_0', ['192.168.0.5']),
            ('eth0', ['192.168.0.4']),
            ('eth1', ['192.168.0.4']),
            ('br0', ['192.168.0.4']),
            ('br0,0', ['192.168.0.4']),
            ('docker0', ['192.168.0.4']),
            ('docker1', ['192.168.0.4']),
            ('lxcbr0', ['192.168.0.4']),
            ('lxcbr1', ['192.168.0.4']),
            ('xenbr0', ['192.168.0.4']),
            ('xenbr1', ['192.168.0.4']),
            ('virt0', ['192.168.0.4']),
            ('virt1', ['192.168.0.4']),
            ('vibr0', ['192.168.0.4']),
            ('vibr1', ['192.168.0.4']),
            ('lo', ['192.168.0.4']),
            # ('veth1', ['192.168.0.4']),
            ('tun1', ['192.168.0.4']),
            ('tap1', ['192.168.0.4'])
        )
    }


class TestCase(base.ModuleCase):

    def test_configured_ifs(self):
        self.assertEqual(
            self._('mc_firewalld.get_configured_ifs')(
                {'zones': {
                    'private': {'interfaces': ['eth1']},
                    'public': {'interfaces': ['eth0']}
                }}),
            {'eth1': 'private', 'eth0': 'public'})

    def test_get_endrule(self):
        self.assertEqual(
            self._('mc_firewalld.get_endrule')(
                audit=None, limit='1/M', log=True, log_prefix='tata'),
            ' log prefix="tata" limit value="1/M"')
        self.assertEqual(
            self._('mc_firewalld.get_endrule')(
                audit=True, limit='1/M', log=True, log_prefix='tata'),
            ' log prefix="tata" limit value="1/M"')
        self.assertEqual(
            self._('mc_firewalld.get_endrule')(
                audit=True, limit='1/M', log_prefix='tata'),
            ' audit limit value="1/M"')
        self.assertEqual(
            self._('mc_firewalld.get_endrule')(
                audit=False, log=False, limit='1/M'),
            '')

    def test_get_public_ips(self):
        with self.patch(
            funcs={
                'modules': {
                    'mc_network.default_net': mock.MagicMock(side_effect=_net),
                    'mc_network.settings': mock.MagicMock(side_effect=_nets)
                }
            },
            grains={
                'ip4_interfaces': {'eth0': ['1.2.3.9']}
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            settings = self._('mc_firewalld.default_settings')()
            settings['zones']['public']['interfaces'].append('eth0:666')
            ips = self._('mc_firewalld.get_public_ips')(settings)
            self.assertEqual(ips,
                             ['1.2.3.9', '1.2.3.8', '1.2.3.5', '1.2.3.4',
                              '1.2.3.7', '1.2.3.6'])

    def test_get_lpublic_ips(self):
        with self.patch(
            funcs={
                'modules': {
                    'mc_network.default_net':
                    mock.MagicMock(side_effect=_local_net),
                    'mc_network.settings':
                    mock.MagicMock(side_effect=_local_nets)
                }
            },
            grains={
                'ip4_interfaces': {'eth0': ['192.168.168.8']}
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            settings = self._('mc_firewalld.default_settings')()
            settings['zones']['public']['interfaces'].append('eth0:666')
            ips = self._('mc_firewalld.get_public_ips')(settings)
            self.assertEqual(ips,
                             ['192.168.0.4', '192.168.168.8',
                              '172.16.1.1', '192.168.0.6', '192.168.0.7',
                              '192.168.1.1', '192.168.0.5',
                              '10.1.1.1', '192.168.0.8'])

    def test_rich_rules(self):
        with self.patch(
            funcs={
                'modules': {
                    'mc_firewalld.get_public_ips': mock.MagicMock(
                        side_effect=lambda: ['1.1.1.1']),
                    'mc_network.default_net': mock.MagicMock(side_effect=_net)
                }
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):

            data = self._('mc_firewalld.rich_rules')(
                masquerade=True,
                source='10.5.0.0/16')
            self.assertEqual(
                data,
                ['rule family="ipv4" masquerade'
                 ' source address="10.5.0.0/16"'
                 ' destination not address="10.5.0.0/16"'])
            data = self._('mc_firewalld.rich_rules')(
                service='http',
                forward_port={'port': 22, 'to_addr': '1.2.3.4'})
            self.assertEqual(
                data,
                ['rule family="ipv4"'
                 ' destination address="1.1.1.1"'
                 ' forward-port port="22"'
                 ' protocol="udp" to-addr="1.2.3.4"'
                 '',
                 'rule family="ipv4"'
                 ' destination address="1.1.1.1"'
                 ' forward-port port="22"'
                 ' protocol="tcp" to-addr="1.2.3.4"',
                 'rule family="ipv4"'
                 ' destination address="1.1.1.1"'
                 ' service name="http" accept']
            )
            rules = self._('mc_firewalld.rich_rules')(
                    port=2222,
                    services=['http', 'dns'],
                    destination='address="1.2.3.5"',
                    action='drop')
            self.assertEqual(
                rules,
                ['rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' port port="2222" protocol="udp"'
                 ' drop',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' port port="2222" protocol="tcp"'
                 ' drop',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' service name="http"'
                 ' drop',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' service name="dns"'
                 ' drop']
            )
            rules = self._('mc_firewalld.rich_rule')(
                    port=2222,
                    services=['http', 'dns'],
                    destination='address="1.2.3.5"',
                    action='drop')
            self.assertEqual(
                rules,
                'rule family="ipv4"'
                ' destination address="1.2.3.5"'
                ' port port="2222" protocol="udp"'
                ' drop'
            )
            self.assertEqual(
                self._('mc_firewalld.rich_rules')(
                    port=2222,
                    destination='address="1.2.3.5"',
                    action='drop'),
                ['rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' port port="2222" protocol="udp"'
                 ' drop',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' port port="2222" protocol="tcp"'
                 ' drop']
            )
            data = self._('mc_firewalld.rich_rules')(
                    ports=[43, 44],
                    destination='address="1.2.3.5"',
                    forward_ports=[
                        {'port': 22, 'to_addr': '1.2.3.4'},
                        {'port': 43, 'to_port': 44, 'to_addr': '1.2.3.4'},
                        {'port': 45, 'to_port': 46}
                    ])
            self.assertEqual(
                ['rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' port port="44" protocol="udp"'
                 ' accept',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' port port="44" protocol="tcp"'
                 ' accept',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' forward-port port="45"'
                 ' protocol="udp" to-port="46"'
                 '',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' forward-port port="45"'
                 ' protocol="tcp" to-port="46"'
                 '',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' forward-port port="43"'
                 ' protocol="udp" to-port="44" to-addr="1.2.3.4"'
                 '',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' forward-port port="43"'
                 ' protocol="tcp" to-port="44" to-addr="1.2.3.4"'
                 '',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' forward-port port="22" protocol="udp"'
                 ' to-addr="1.2.3.4"'
                 '',
                 'rule family="ipv4"'
                 ' destination address="1.2.3.5"'
                 ' forward-port port="22" protocol="tcp"'
                 ' to-addr="1.2.3.4"'
                 ''],
                data
            )
            data = self._('mc_firewalld.rich_rules')(
                destination='address="1.2.3.5"')
            self.assertEqual(
                data,
                ['rule family="ipv4" destination address="1.2.3.5"'
                 ' accept']
            )
            data = self._('mc_firewalld.rich_rules')(
                source='address="1.2.3.5"')
            self.assertEqual(
                data,
                ['rule family="ipv4" source address="1.2.3.5"'
                 ' accept']
            )
            data = self._('mc_firewalld.rich_rules')(
                source='address="1.2.3.4"',
                destination='address="1.2.3.5"')
            self.assertEqual(
                data,
                ['rule family="ipv4"'
                 ' source address="1.2.3.4"'
                 ' destination address="1.2.3.5"'
                 ' accept']
            )
            data = self._('mc_firewalld.rich_rules')(
                icmp_block=True,
                destination='address="1.2.3.5"')
            self.assertEqual(
                data,
                ['rule family="ipv4" icmp-block destination address="1.2.3.5"']

            )
            data = self._('mc_firewalld.rich_rules')(
                icmp_block=[9],
                destination='address="1.2.3.5"')
            self.assertEqual(
                data,
                ['rule family="ipv4" icmp-block name="9"'
                 ' destination address="1.2.3.5"']
            )

    def test_add_real_interfaces(self):

        def _do():
            return {
                'default_if': 'br0',
                'gifaces': (
                    ('em0', ['1.2.3.4']),
                    ('em1', ['1.2.3.4']),
                    ('em2', ['1.2.3.4']),
                    ('em3', ['1.2.3.4']),
                    ('eth0', ['1.2.3.4']),
                    ('eth1', ['1.2.3.4']),
                    ('br0', ['1.2.3.4']),
                    ('br0,0', ['1.2.3.4']),
                    ('docker0', ['1.2.3.4']),
                    ('docker1', ['1.2.3.4']),
                    ('lxcbr0', ['1.2.3.4']),
                    ('lxcbr1', ['1.2.3.4']),
                    ('xenbr0', ['1.2.3.4']),
                    ('xenbr1', ['1.2.3.4']),
                    ('virt0', ['1.2.3.4']),
                    ('virt1', ['1.2.3.4']),
                    ('vibr0', ['1.2.3.4']),
                    ('vibr1', ['1.2.3.4']),
                    ('lo', ['1.2.3.4']),
                    # ('veth1', ['1.2.3.4']),
                    ('tun1', ['1.2.3.4']),
                    ('tap1', ['1.2.3.4'])
                )
            }
        with self.patch(
            funcs={
                'modules': {
                    'mc_network.default_net': mock.MagicMock(side_effect=_do)
                }
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            data = self._('mc_firewalld.add_real_interfaces')({})
            self.assertEqual(
                dict(data["zones"]),
                {'dck': {'interfaces': ['docker0', 'docker1']},
                 'internal': {'interfaces': ['em1', 'em2', 'em3', 'eth1']},
                 'lxc': {'interfaces': ['lxcbr0', 'lxcbr1']},
                 'public': {'interfaces': ['em0', 'eth0', 'br0']},
                 'trusted': {'interfaces': ['lo']},
                 'vpn': {'interfaces': ['tun1']}})
            data = self._('mc_firewalld.add_real_interfaces')(
                {'have_rpn': True})
            self.assertEqual(
                dict(data["zones"]),
                {'dck': {'interfaces': ['docker0', 'docker1']},
                 'lxc': {'interfaces': ['lxcbr0', 'lxcbr1']},
                 'internal': {'interfaces': ['em1', 'em2']},
                 'rpn': {'interfaces': ['em3', 'eth1']},
                 'public': {'interfaces': ['em0', 'eth0', 'br0']},
                 'trusted': {'interfaces': ['lo']},
                 'vpn': {'interfaces': ['tun1']}})

    def test_is_allow_local(self):
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.is_container': mock.MagicMock(
                        side_effect=lambda: True)
                }
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            def _do():
                return {
                    'default_if': 'br0',
                    'default_route': {'iface': 'br0'},
                    'gifaces': (
                        ('eth0', ['1.2.3.4']),
                        ('eth1', ['1.2.3.4']),
                        ('br0', ['1.2.3.4']),
                        ('br0,0', ['1.2.3.4']))}
            with self.patch(
                funcs={
                    'modules': {
                        'mc_network.default_net': mock.MagicMock(
                            side_effect=_do),
                    }
                },
                filtered=['mc.*'],
                kinds=['modules']
            ):
                self.assertTrue(self._('mc_firewalld.is_allow_local')())
                self.assertFalse(self._('mc_firewalld.is_permissive')())

        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.is_container': mock.MagicMock(
                        side_effect=lambda: True)
                }
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):

            def _do():
                return {
                    'default_if': 'br0',
                    'default_route': {'iface': 'eth0'},
                    'gifaces': (
                        ('eth0', ['1.2.3.4']),
                        ('eth1', ['1.2.3.4']),
                        ('br0', ['1.2.3.4']),
                        ('br0,0', ['1.2.3.4']))}
            with self.patch(
                funcs={
                    'modules': {
                        'mc_network.default_net': mock.MagicMock(
                            side_effect=_do),
                    }
                },
                filtered=['mc.*'],
                kinds=['modules']
            ):
                self.assertTrue(self._('mc_firewalld.is_allow_local')())
                self.assertTrue(self._('mc_firewalld.is_permissive')())

    def test_is_allow_localb(self):
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.is_container': mock.MagicMock(
                        side_effect=lambda: False)
                }
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            def _do():
                return {
                    'default_if': 'br0',
                    'default_route': {'iface': 'br0'},
                    'gifaces': (
                        ('eth0', ['1.2.3.4']),
                        ('eth1', ['1.2.3.4']),
                        ('br0', ['1.2.3.4']),
                        ('br0,0', ['1.2.3.4']))}
            with self.patch(
                funcs={
                    'modules': {
                        'mc_network.default_net': mock.MagicMock(
                            side_effect=_do),
                    }
                },
                filtered=['mc.*'],
                kinds=['modules']
            ):
                self.assertFalse(self._('mc_firewalld.is_allow_local')())

        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.is_container': mock.MagicMock(
                        side_effect=lambda: False)
                }
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            def _do():
                return {
                    'default_if': 'br0',
                    'default_route': {'iface': 'eth0'},
                    'gifaces': (
                        ('eth0', ['1.2.3.4']),
                        ('eth1', ['1.2.3.4']),
                        ('br0', ['1.2.3.4']),
                        ('br0,0', ['1.2.3.4']))}
            with self.patch(
                funcs={
                    'modules': {
                        'mc_network.default_net': mock.MagicMock(
                            side_effect=_do),
                    }
                },
                filtered=['mc.*'],
                kinds=['modules']
            ):
                self.assertFalse(self._('mc_firewalld.is_allow_local')())

    def test_default_settings(self):
        p = 'makina-states.services.firewall.firewalld.zones.public.'
        with self.patch(
            filtered=['mc.*'],
            kinds=['modules'],
            pillar=OrderedDict([
                (p + 'rules-bar', 'rule service name="ftp" log'),
                (p + 'rules-moo', 'rule service name="ftp2" log')
            ])
        ):
            data = self._('mc_firewalld.default_settings')()
            self.assertTrue(isinstance(data, dict))
            self.assertTrue(isinstance(data['permissive_mode'], bool))
            self.assertTrue(isinstance(data['is_container'], bool))
            self.assertEqual(data['default_zone'], 'public')
            for i in [
                'rule service name="ftp2" log',
                'rule service name="ftp" log'
            ]:
                self.assertTrue(i in data['zones']['public']['rules'])

    def test_search_aliased_interfaces(self):

        data = self._('mc_firewalld.search_aliased_interfaces')(
            {'public_zones': ['foo', 'bar'],
             'zones': {'bar': {'interfaces': ['eth1']}}})
        self.assertEqual(
            data['aliased_interfaces'],
            ['eth1'])
        self.assertEqual(
            data['zones']['bar']['interfaces'],
            ['eth1'])
        data = self._('mc_firewalld.search_aliased_interfaces')(
            {'public_zones': ['foo', 'bar'],
             'aliased_interfaces': ['eth0'],
             'zones': {'bar': {'interfaces': ['eth1']}}})
        self.assertEqual(
            data['aliased_interfaces'],
            ['eth0', 'eth1'])
        self.assertEqual(
            data['zones']['bar']['interfaces'],
            ['eth1', 'eth0'])
        self.assertEqual(
            data['zones']['foo']['interfaces'],
            ['eth0'])

    def test_add_aliased_interfaces(self):
        data = self._('mc_firewalld.add_aliased_interfaces')(
            {'aliased_interfaces': ['eth0', 'eth1'],
             'public_zones': ['foo', 'bar'],
             'zones': {'bar': {'interfaces': ['eth1', 'eth0']},
                       'foo': {'interfaces': ['eth0']}}})
        count = self._('mc_firewalld.default_settings')()['aliases']
        self.assertEqual(len(data['zones']['foo']['interfaces']), count + 1)
        self.assertEqual(data['zones']['foo']['interfaces'][:3],
                         ['eth0', 'eth0:0', 'eth0:1'])
        self.assertEqual(data['zones']['bar']['interfaces'][-3:],
                         ['eth1:{0}'.format(count-3),
                          'eth1:{0}'.format(count-2),
                          'eth1:{0}'.format(count-1)])

    def test_add_zone_policices(self):
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'permissive_mode': False,
             'internal_zones': ['bar'],
             'trusted_networks': ['1.2.4.3'],
             'banned_networks': ['1.2.4.2'],
             'trust_internal': True,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})

        subset = ['rule family="ipv4" source address="1.2.4.2"'
                  ' drop',
                  'rule family="ipv4" source address="1.2.4.3"'
                  ' accept']
        self.assertEqual(
            [a for a in data['zones']['bar']['rules'] if 'icmp' not in a],
            subset)
        subset = ['rule family="ipv4" source address="1.2.4.2"'
                  ' drop',
                  'rule family="ipv4" source address="1.2.4.3"'
                  ' accept']
        self.assertEqual(
            [a for a in data['zones']['foo']['rules'] if 'icmp' not in a],
            subset)
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'permissive_mode': False,
             'internal_zones': ['bar'],
             'trust_internal': True,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['bar']['target'], 'accept')
        self.assertEqual(data['zones']['foo']['target'], 'drop')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': True,
             'trust_internal': True,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'accept')
        self.assertEqual(data['zones']['bar']['target'], 'accept')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': False,
             'trust_internal': False,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'drop')
        self.assertEqual(data['zones']['bar']['target'], 'drop')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': True,
             'trust_internal': False,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'accept')
        self.assertEqual(data['zones']['bar']['target'], 'drop')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': True,
             'trust_internal': None,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'accept')
        self.assertEqual(data['zones']['bar']['target'], 'accept')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': False,
             'trust_internal': None,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'drop')
        self.assertEqual(data['zones']['bar']['target'], 'accept')

    def test_1anatted_networks(self):
        def _do():
            return {'clients': ['localhost']}

        with self.patch(
            funcs={
                'modules': {
                    'mc_network.default_net':
                    mock.MagicMock(side_effect=_snet),
                    'mc_network.settings':
                    mock.MagicMock(side_effect=_snets),
                    'mc_burp.settings': mock.MagicMock(
                        side_effect=_do),
                }
            },
            grains={
                'ip4_interfaces': {'eth0': ['1.2.3.6']}
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            data = self._('mc_firewalld.add_natted_networks')(
                {'aliased_interfaces': [],
                 'public_services': ['a'],
                 'restricted_services': ['b'],
                 'services': {'c': {}},
                 'public_zones': ['foo'],
                 'permissive_mode': False,
                 'internal_zones': ['bar', 'foo'],
                 'public_zones': ['mar'],
                 'natted_networks': {
                     'eth1': ['10.1.1.0/24', '192.168.1.0/24'],
                     'eth0': ['10.1.2.0/24', '192.168.2.0/24'],
                 },
                 'internal_zones': ['bar', 'foo'],
                 'trusted_networks': [],
                 'banned_networks': [],
                 'trust_internal': True,
                 'zones': {'bar': {'interfaces': ['eth1']},
                           'mar': {'interfaces': ['eth2'],
                                   'public_services': ['f'],
                                   'restricted_services': ['e'],
                                   'services': {'d': {}}},
                           'foo': {'interfaces': ['eth0']}}})
            self.assertEqual(
                data['zones']['foo'].get('rules', []),
                [])
            self.assertEqual(
                data['zones']['bar'].get('rules', []),
                [])
            self.assertEqual(
                data['zones']['mar']['rules'],
                ['rule family="ipv4" masquerade'
                 ' source address="10.1.2.0/24"'
                 ' destination not address="10.1.2.0/24"',
                 'rule family="ipv4" masquerade'
                 ' source address="192.168.2.0/24"'
                 ' destination not address="192.168.2.0/24"',
                 'rule family="ipv4" masquerade'
                 ' source address="192.168.1.0/24"'
                 ' destination not address="192.168.1.0/24"',
                 'rule family="ipv4" masquerade'
                 ' source address="10.1.1.0/24"'
                 ' destination not address="10.1.1.0/24"'])

    def test_service_policies(self):
        def _do():
            return {'clients': ['localhost']}

        with self.patch(
            funcs={
                'modules': {
                    'mc_network.default_net':
                    mock.MagicMock(side_effect=_snet),
                    'mc_network.settings':
                    mock.MagicMock(side_effect=_snets),
                    'mc_burp.settings': mock.MagicMock(
                        side_effect=_do),
                }
            },
            grains={
                'ip4_interfaces': {'eth0': ['1.2.3.6']}
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            data = self._('mc_firewalld.add_services_policies')(
                {'aliased_interfaces': [],
                 'public_services': ['a'],
                 'restricted_services': ['b'],
                 'services': {'c': {}},
                 'public_zones': ['foo'],
                 'permissive_mode': False,
                 'internal_zones': ['bar'],
                 'trusted_networks': [],
                 'banned_networks': [],
                 'trust_internal': True,
                 'zones': {'bar': {'interfaces': ['eth1']},
                           'mar': {'interfaces': ['eth2'],
                                   'public_services': ['f'],
                                   'restricted_services': ['e'],
                                   'services': {'d': {}}},
                           'foo': {'interfaces': ['eth0']}}})

            self.assertEqual(
                 data['services'],
                 {'a': {}, 'b': {}, 'c': {}, 'd': {}, 'e': {}, 'f': {}})
            self.assertEqual(
                 data['zones']['bar']['services'],
                 {'a': {}, 'b': {}, 'c': {}, 'd': {}, 'e': {}, 'f': {}})
            self.assertEqual(
                 data['zones']['mar']['services'],
                 {'a': {}, 'b': {}, 'c': {}, 'd': {}, 'e': {}, 'f': {}})
            self.assertEqual(
                 data['zones']['foo']['services'],
                 {'a': {}, 'b': {}, 'c': {}, 'd': {}, 'e': {}, 'f': {}})
            self.assertEqual(
                data['zones']['bar']['public_services'],
                ['a'])
            self.assertEqual(
                data['zones']['foo']['public_services'],
                ['a'])
            self.assertEqual(
                data['zones']['mar']['public_services'],
                ['f'])
            self.assertEqual(
                data['zones']['bar']['restricted_services'],
                ['b'])
            self.assertEqual(
                data['zones']['foo']['restricted_services'],
                ['b'])
            self.assertEqual(
                data['zones']['mar']['restricted_services'],
                ['e'])
            self.assertEqual(
                data['public_services'],
                ['a'])
            self.assertEqual(
                data['restricted_services'],
                ['b'])
            self.assertEqual(
                data['zones']['foo']['rules'],
                ['rule family="ipv4" destination address="1.2.3.6"'
                 ' service name="b" drop',
                 'rule family="ipv4" destination address="1.2.3.6"'
                 ' service name="a" accept']
            )
            self.assertEqual(
                data['zones']['bar']['rules'],
                ['rule family="ipv4" destination address="1.2.3.6"'
                 ' service name="b" drop',
                 'rule family="ipv4" destination address="1.2.3.6"'
                 ' service name="a" accept']
            )
            self.assertEqual(
                data['zones']['mar']['rules'],
                ['rule family="ipv4" destination address="1.2.3.6" '
                 'service name="e" drop',
                 'rule family="ipv4" destination address="1.2.3.6" '
                 'service name="f" accept']
            )

if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
