# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
import unittest
from .. import base
import mc_states.api
from salt.utils.odict import OrderedDict
import mock

six = mc_states.api.six


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

    def test_add_dest_rules(self):
        self.assertEqual(
            self._('mc_firewalld.add_dest_rules')(
                [], [], 'foo', 'bar'),
            ['foo bar'])
        self.assertEqual(
            self._('mc_firewalld.add_dest_rules')(
                [], [], 'foo', 'bar', 'drop'),
            ['foo bar drop'])
        self.assertEqual(
            self._('mc_firewalld.add_dest_rules')(
                ['address="1.2.3.4"'], [], 'foo', 'bar', 'drop'),
            ['foo destination address="1.2.3.4" bar drop'])

    def test_1arich_rules(self):
        rules = self._('mc_firewalld.rich_rules')(
                port=2222,
                services=['http', 'dns'],
                destination='address="1.2.3.5"',
                action='drop')
        self.assertEqual(
            rules,
            ['rule family=ipv4 port port="2222" protocol="udp"'
             ' destination address="1.2.3.5" drop',
             'rule family=ipv4 port port="2222" protocol="tcp"'
             ' destination address="1.2.3.5" drop',
             'rule family=ipv4 to service name="http" drop',
             'rule family=ipv4 to service name="dns" drop']
        )
        rules = self._('mc_firewalld.rich_rule')(
                port=2222,
                services=['http', 'dns'],
                destination='address="1.2.3.5"',
                action='drop')
        self.assertEqual(
            rules,
            'rule family=ipv4 port port="2222" protocol="udp"'
            ' destination address="1.2.3.5" drop'
        )
        self.assertEqual(
            self._('mc_firewalld.rich_rules')(
                port=2222,
                destination='address="1.2.3.5"',
                action='drop'),
            ['rule family=ipv4 port port="2222" protocol="udp"'
             ' destination address="1.2.3.5" drop',
             'rule family=ipv4 port port="2222" protocol="tcp"'
             ' destination address="1.2.3.5" drop']
        )
        self.assertEqual(
            self._('mc_firewalld.rich_rules')(
                service='http',
                forward_port={'port': 22, 'addr': '1.2.3.4'}),
            []
        )
        self.assertEqual(
            self._('mc_firewalld.rich_rules')(
                port=2222,
                destination='address="1.2.3.5"',
                forward_port={'port': 22, 'addr': '1.2.3.4'}),
            ['rule family=ipv4 forward-port port="2222" '
             'protocol="udp" to-port="22" to-addr="1.2.3.4" '
             'destination address="1.2.3.5" accept',
             'rule family=ipv4 forward-port port="2222" protocol="tcp"'
             ' to-port="22" to-addr="1.2.3.4" destination '
             'address="1.2.3.5" accept']
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
                    ('veth1', ['1.2.3.4']),
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
                 'lxc': {'interfaces': ['lxcbr0', 'lxcbr1']},
                 'public': {'interfaces': ['eth0', 'br0']},
                 'trusted': {'interfaces': ['lo', 'veth1']},
                 'vpn': {'interfaces': ['tun1']}})
            data = self._('mc_firewalld.add_real_interfaces')(
                {'have_rpn': True})
            self.assertEqual(
                dict(data["zones"]),
                {'dck': {'interfaces': ['docker0', 'docker1']},
                 'lxc': {'interfaces': ['lxcbr0', 'lxcbr1']},
                 'rpn': {'interfaces': ['em3', 'eth1']},
                 'public': {'interfaces': ['eth0', 'br0']},
                 'trusted': {'interfaces': ['lo', 'veth1']},
                 'vpn': {'interfaces': ['tun1']}})

    def test_is_permissive(self):
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
                self.assertTrue(self._('mc_firewalld.is_permissive')())

    def test_is_permissiveb(self):
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
                self.assertFalse(self._('mc_firewalld.is_permissive')())

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
                self.assertFalse(self._('mc_firewalld.is_permissive')())

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
        self.assertEqual(
            self._('mc_firewalld.search_aliased_interfaces')(
                {'public_zones': ['foo', 'bar'],
                 'zones': {'bar': {'interfaces': ['eth1']}}}),
            {'aliased_interfaces': ['eth1'],
             'public_zones': ['foo', 'bar'],
             'banned_networks': [],
             'trust_internal': True,
             'trusted_networks': [],
             'internal_zones': ['internal', 'dmz', 'home',
                                'docker', 'lxc', 'virt'],
             'permissive_mode': True,

             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': []}}}
        )
        self.assertEqual(
            self._('mc_firewalld.search_aliased_interfaces')(
                {'public_zones': ['foo', 'bar'],
                 'aliased_interfaces': ['eth0'],
                 'zones': {'bar': {'interfaces': ['eth1']}}}),
            {'aliased_interfaces': ['eth0', 'eth1'],
             'public_zones': ['foo', 'bar'],
             'banned_networks': [],
             'permissive_mode': True,
             'trust_internal': True,
             'trusted_networks': [],
             'internal_zones': ['internal', 'dmz', 'home',
                                'docker', 'lxc', 'virt'],
             'zones': {'bar': {'interfaces': ['eth1', 'eth0']},
                       'foo': {'interfaces': ['eth0']}}}
        )

    def test_add_aliased_interfaces(self):
        data = self._('mc_firewalld.add_aliased_interfaces')(
            {'aliased_interfaces': ['eth0', 'eth1'],
             'public_zones': ['foo', 'bar'],
             'zones': {'bar': {'interfaces': ['eth1', 'eth0']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(len(data['zones']['foo']['interfaces']), 101)
        self.assertEqual(data['zones']['foo']['interfaces'][:3],
                         ['eth0', 'eth0:0', 'eth0:1'])
        self.assertEqual(data['zones']['bar']['interfaces'][-3:],
                         ['eth1:97', 'eth1:98', 'eth1:99'])

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
        self.assertEqual(
            data['zones']['bar']['rules'],
            ['rule family=ipv4 source address="1.2.4.2" drop',
             'rule family=ipv4 source address="1.2.4.3" accept'])
        self.assertEqual(
            data['zones']['foo']['rules'],
            ['rule family=ipv4 source address="1.2.4.2" drop',
             'rule family=ipv4 source address="1.2.4.3" accept'])
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'permissive_mode': False,
             'internal_zones': ['bar'],
             'trust_internal': True,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['bar']['target'], 'ACCEPT')
        self.assertEqual(data['zones']['foo']['target'], 'REJECT')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': True,
             'trust_internal': True,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'ACCEPT')
        self.assertEqual(data['zones']['bar']['target'], 'ACCEPT')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': False,
             'trust_internal': False,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'REJECT')
        self.assertEqual(data['zones']['bar']['target'], 'REJECT')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': True,
             'trust_internal': False,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'ACCEPT')
        self.assertEqual(data['zones']['bar']['target'], 'REJECT')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': True,
             'trust_internal': None,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'ACCEPT')
        self.assertEqual(data['zones']['bar']['target'], 'ACCEPT')
        data = self._('mc_firewalld.add_zones_policies')(
            {'aliased_interfaces': [],
             'public_zones': ['foo'],
             'internal_zones': ['bar'],
             'permissive_mode': False,
             'trust_internal': None,
             'zones': {'bar': {'interfaces': ['eth1']},
                       'foo': {'interfaces': ['eth0']}}})
        self.assertEqual(data['zones']['foo']['target'], 'REJECT')
        self.assertEqual(data['zones']['bar']['target'], 'ACCEPT')


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
