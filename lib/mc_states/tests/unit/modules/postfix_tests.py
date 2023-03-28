#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base
import mock
from mc_states.api import six


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

    def test_catchall(self):
        func = self._('mc_postfix.select_catchall')
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.registry':
                    mock.MagicMock(return_value={'is': {'devhost': True}}),
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
            ret = func({'catchall': None,
                        'virtual_map': []})
            self.assertEqual(
                ret,
                {'catchall': 'vagrant@localhost',
                 'virtual_map': [{'/.*/': 'vagrant@localhost'}]})

        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.registry':
                    mock.MagicMock(return_value={'is': {'devhost': False}}),
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
            ret = func({'catchall': None,
                        'mode': None,
                        'virtual_map': []})
            self.assertEqual(
                ret,
                {'catchall': None, 'mode': None, 'virtual_map': []})
            ret = func({'catchall': None,
                        'mode': 'localdeliveryonly',
                        'virtual_map': []})
            self.assertEqual(
                ret,
                {'catchall': 'root@localhost',
                 'mode': 'localdeliveryonly',
                 'virtual_map': [{'/.*/': 'root@localhost'}]})

            ret = func({'catchall': False,
                        'mode': 'localdeliveryonly',
                        'virtual_map': []})
            self.assertEqual(
                ret,
                {'catchall': False,
                 'mode': 'localdeliveryonly',
                 'virtual_map': []})

    def test_select_mode(self):
        func = self._('mc_postfix.select_mode')
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.registry':
                    mock.MagicMock(return_value={'is': {'devhost': True}}),
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
            ret = func({'mode': None})
            self.assertEqual(ret,
                             {'mode': 'localdeliveryonly'})
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.registry':
                    mock.MagicMock(return_value={'is': {'devhost': False}}),
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
            for mode, wret in six.iteritems({
                'foo': 'localdeliveryonly',
                None: 'localdeliveryonly',
                'localdeliveryonly': 'localdeliveryonly',
                'relay': 'relay',
                'custom': 'custom',
                'catchall': 'catchall',
                'redirect': 'catchall',
            }):
                ret = func({'mode': mode})
                self.assertEqual(ret, {'mode': wret},
                                 'modetest: {0} {1} != {2}'.format(mode,
                                                                   ret['mode'],
                                                                   wret))

    def test_select_dests_and_relays(self):
        func = self._('mc_postfix.select_dests_and_relays')
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.registry':
                    mock.MagicMock(return_value={'is': {'devhost': True}}),
                    'mc_network.default_net':
                    mock.MagicMock(side_effect=_local_net),
                    'mc_network.settings':
                    mock.MagicMock(side_effect=_local_nets)
                }
            },
            grains={
                'fqdn': 'foo.bar',
                'ip4_interfaces': {'eth0': ['192.168.168.8']},
                'ip_interfaces': {'eth0': ['192.168.168.8', 'fe80::1']}
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret = func({'no_local': True,
                        'mydestination': {'foo.bar': 'bar', 'g': 'g'},
                        'mailname': 'foo',
                        'mode': 'localdeliveryonly',
                        'relay_domains': {},
                        'inet_protocols': [],
                        'local_networks': []})
            self.assertEqual(ret,
                             {'mode': 'localdeliveryonly',
                              'inet_protocols': [],
                              'local_networks': [],
                              'mydestination': {
                                  'foo.bar': 'bar',
                                  'foo': 'OK',
                                  'g': 'g',
                                  'localhost': 'OK',
                                  'localhost.local': 'OK'},
                              'relay_domains': {},
                              'mailname': 'foo',
                              'no_local': True})
            ret = func({'no_local': True,
                        'mailname': 'foo',
                        'mode': 'relay',
                        'mydestination': {'foo': 'bar', 'g': 'g'},
                        'relay_domains': {},
                        'inet_protocols': [],
                        'local_networks': []})
            self.assertEqual(ret,
                             {'mode': 'relay',
                              'inet_protocols': [],
                              'relay_domains': {'foo': 'OK',
                                                'foo.bar': 'OK',
                                                'localhost': 'OK',
                                                'localhost.local': 'OK'},
                              'mydestination': {'g': 'g'},
                              'local_networks': [],
                              'mailname': 'foo',
                              'no_local': True})

    def test_select_interfaces(self):
        func = self._('mc_postfix.select_interfaces')
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.registry':
                    mock.MagicMock(return_value={'is': {'devhost': True}}),
                    'mc_network.default_net':
                    mock.MagicMock(side_effect=_local_net),
                    'mc_network.settings':
                    mock.MagicMock(side_effect=_local_nets)
                }
            },
            grains={
                'ip4_interfaces': {'eth0': ['192.168.168.8']},
                'ip_interfaces': {'eth0': ['192.168.168.8', 'fe80::1']}
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret = func({'inet_interfaces': [],
                        'mode': 'custom'})
            self.assertEqual(ret,
                             {'inet_interfaces': ['all'],
                              'mode': 'custom'})
            ret = func({'inet_interfaces': 'foo',
                        'mode': 'custom'})
            self.assertEqual(ret,
                             {'inet_interfaces': ['foo'],
                              'mode': 'custom'})
            ret = func({'inet_interfaces': 'foo',
                        'mode': 'relay'})
            self.assertEqual(ret,
                             {'inet_interfaces': ['foo'],
                              'mode': 'relay'})
            ret = func({'inet_interfaces': [],
                        'mode': 'relay'})
            self.assertEqual(ret,
                             {'inet_interfaces': ['127.0.0.1'],
                              'mode': 'relay'})

    def test_select_networks(self):
        func = self._('mc_postfix.select_networks')
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.registry':
                    mock.MagicMock(return_value={'is': {'devhost': True}}),
                    'mc_network.default_net':
                    mock.MagicMock(side_effect=_local_net),
                    'mc_network.settings':
                    mock.MagicMock(side_effect=_local_nets)
                }
            },
            grains={
                'ip4_interfaces': {'eth0': ['192.168.168.8']},
                'ip_interfaces': {'eth0': ['192.168.168.8', 'fe80::1']}
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret = func({'mynetworks': None,
                        'no_local': True,
                        'inet_protocols': [],
                        'local_networks': []})
            self.assertEqual(ret,
                             {'mynetworks': [],
                              'inet_protocols': [],
                              'local_networks': [],
                              'no_local': True})
            ret = func({'mynetworks': None,
                        'no_local': False,
                        'inet_protocols': [],
                        'local_networks': []})
            self.assertEqual(ret,
                             {'mynetworks': ['192.168.168.8/32',
                                             '[fe80::1]/128'],
                              'inet_protocols': [],
                              'local_networks': ['192.168.168.8/32',
                                                 'fe80::1'],
                              'no_local': False})
            ret = func({'mynetworks': ['fe80::2/127'],
                        'no_local': False,
                        'inet_protocols': [],
                        'local_networks': [
                            '192.168.168.8/32',
                            'fe80::1'
                        ]})
            self.assertEqual(ret,
                             {'mynetworks': ['[fe80::2]/127',
                                             '192.168.168.8/32',
                                             '[fe80::1]/128'],
                              'inet_protocols': [],
                              'local_networks': ['192.168.168.8/32',
                                                 'fe80::1'],
                              'no_local': False})



    def test_select_certs(self):
        func = self._('mc_postfix.select_certs')
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.registry':
                    mock.MagicMock(return_value={'is': {'devhost': True}}),
                    'mc_ssl.search_matching_certificate':
                    mock.MagicMock(
                        return_value=('BEGIN CERTIFICATE',
                                      'END PRIVATE KEY')),
                    'mc_network.default_net':
                    mock.MagicMock(side_effect=_local_net),
                    'mc_network.settings':
                    mock.MagicMock(side_effect=_local_nets)
                }
            },
            opts={
                'cachedir': ''
            },
            grains={
                'ip4_interfaces': {'eth0': ['192.168.168.8']},
                'ip_interfaces': {'eth0': ['192.168.168.8', 'fe80::1']}
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            ret = func({'cert': 'a', 'cert_key': 'b'})
            self.assertEqual(ret, {'cert': 'a', 'cert_key': 'b'})
            ret1 = func({'domain': 'foo',
                         'cert': 'a',
                         'cert_key': None})
            ret2 = func({'domain': 'foo',
                         'cert': None,
                         'cert_key': 'b'})
            ret3 = func({'domain': 'foo',
                         'cert': None,
                         'cert_key': None})
            self.assertEqual(ret1, ret2)
            self.assertEqual(ret1, ret3)
            self.assertTrue('PRIVATE KEY' in ret3['cert_key'])
            self.assertTrue('CERTIFICATE' in ret3['cert'])


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
