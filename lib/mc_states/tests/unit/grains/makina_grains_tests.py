#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import division
import copy
import textwrap
import subprocess
import sys
import os
import unittest
import StringIO
import mc_states.api
from .. import base
import contextlib


from mock import MagicMock, patch, mock_open

rt1 = textwrap.dedent('''
Kernel IP routing table
Destination     Gateway         Genmask         Flags   MSS Window  irtt Iface
0.0.0.0         125.124.124.1   0.0.0.0         UG        0 0          0 br0
10.0.3.0        0.0.0.0         255.255.255.0   U         0 0          0 lxcbr0
10.5.0.0        0.0.0.0         255.255.0.0     U         0 0          0 lxcbr1
10.90.0.0       10.90.48.65     255.254.0.0     UG        0 0          0 eth1
10.90.48.64     0.0.0.0         255.255.255.192 U         0 0          0 eth1
192.168.122.0   0.0.0.0         255.255.255.0   U         0 0          0 virbr0
125.124.124.0   0.0.0.0         255.255.255.0   U         0 0          0 br0
''')


class TestCase(base.GrainsCase):

    def docker(self):
        return self.get_private('makina_grains._is_docker')()

    @property
    def grains(self):
        return self._('makina_grains.get_makina_grains')()

    def test_pg(self):
        with contextlib.nested(
            patch(
                'os.path.exists', MagicMock(return_value=False)
            ),
            patch(
                'os.listdir', MagicMock(return_value=0)
            )
        ):
            fun = self.get_private('makina_grains._pgsql_vers')
            ret = fun()
            self.assertEquals(ret['details'], {})
            self.assertEquals(ret['global'], {})

        def do_(path):
            if path in [
                '/var/lib/postgresql/9.0/main/postmaster.pid'
            ]:
                return True
            return False

        with contextlib.nested(
            patch(
                'os.path.exists', MagicMock(side_effect=do_)
            ),
            patch(
                'os.listdir', MagicMock(return_value=0)
            )
        ):
            fun = self.get_private('makina_grains._pgsql_vers')
            ret = fun()
            self.assertEquals(ret['global'], {'9.0': True})
            self.assertEquals(ret['details'],
                              {'9.0': {'has_data': False, 'running': True}})

        def do_(path):
            if path in [
                '/var/lib/postgresql/9.0/main/postmaster.pid',
                '/var/lib/postgresql/9.0/main/base',
                '/var/lib/postgresql/9.0/main/globalbase'
            ]:
                return True
            return False

        with contextlib.nested(
            patch(
                'os.path.exists', MagicMock(side_effect=do_)
            ),
            patch(
                'os.listdir', MagicMock(return_value=0)
            )
        ):
            fun = self.get_private('makina_grains._pgsql_vers')
            ret = fun()
            self.assertEquals(ret['global'], {'9.0': True})
            self.assertEquals(ret['details'],
                              {'9.0': {'has_data': False, 'running': True}})

        def do_(path):
            if path in [
                '/var/lib/postgresql/9.0/main/postmaster.pid',
                '/var/lib/postgresql/9.0/main/base',
                '/var/lib/postgresql/9.0/main/globalbase'
            ]:
                return True
            return False

        with contextlib.nested(
            patch(
                'os.path.exists', MagicMock(side_effect=do_)
            ),
            patch(
                'os.listdir', MagicMock(return_value=3)
            )
        ):
            fun = self.get_private('makina_grains._pgsql_vers')
            ret = fun()
            self.assertEquals(ret['global'], {'9.0': True})
            self.assertEquals(ret['details'],
                              {'9.0': {'has_data': True, 'running': True}})

    def test_devhostnum(self):
        fun = self.get_private('makina_grains._devhost_num')
        self.assertEqual(fun(), '')

    def test_is_systemd(self):
        fun = self.get_private('makina_grains._is_systemd')
        with patch(
            'os.path.exists', MagicMock(return_value=False)
        ):
            with patch(
                'os.readlink', MagicMock(return_value='foo')
            ):
                self.assertFalse(fun())
            with patch(
                'os.readlink', MagicMock(return_value='/lib/systemd/systemd')
            ):
                self.assertTrue(fun())
        with patch(
            'os.readlink', MagicMock(return_value='foo')
        ):
            with patch(
                'os.path.exists', MagicMock(return_value=True)
            ):
                with patch(
                    'os.listdir', MagicMock(return_value=[1, 2, 3, 4, 5])
                ):
                    self.assertTrue(fun())
                with patch(
                    'os.listdir', MagicMock(return_value=[1, 2, 3])
                ):
                    self.assertFalse(fun())
        with patch(
            'os.path.exists', MagicMock(side_effect=OSError)
        ):
            with patch(
                'os.readlink', MagicMock(side_effect=OSError)
            ):
                self.assertTrue(fun() is False)

    def test_is_devhost(self):
        fun = self.get_private('makina_grains._is_devhost')
        mod = sys.modules[fun.__module__]
        with patch.object(
            mod, '_devhost_num', MagicMock(return_value='')
        ):
            self.assertFalse(fun())
        with patch.object(
            mod, '_devhost_num', MagicMock(return_value='2')
        ):
            self.assertTrue(fun())

    def test_is_docker(self):

        def raise_(*a):
            raise IOError()

        wopen = mock_open(read_data='foo')
        gopen = mock_open(read_data='docker')
        noopen = MagicMock(side_effect=raise_)
        with self.patch(
            grains={'makina.docker': False},
            filtered=['mc.*'],
            kinds=['grains', 'modules']
        ):
            with patch('__builtin__.open',  noopen):
                with patch("os.path.exists", return_value=False):
                    ret4 = copy.deepcopy(self.docker())
                with patch(
                    "os.path.exists", return_value=True
                ):
                    ret5 = copy.deepcopy(self.docker())
            with patch('__builtin__.open', gopen):
                ret3 = copy.deepcopy(self.docker())
            with patch('__builtin__.open', wopen):
                ret6 = copy.deepcopy(self.docker())
        with self.patch(
            grains={'makina.docker': True},
            filtered=['mc.*'],
            kinds=['grains', 'modules']
        ):
            ret1 = copy.deepcopy(self.docker())
        self.assertFalse(ret4)
        self.assertTrue(ret5)
        self.assertFalse(ret6)
        self.assertTrue(ret3)
        self.assertTrue(ret1)

    def test_is_container(self):
        fun = self.get_private('makina_grains._is_container')
        mod = sys.modules[fun.__module__]
        with contextlib.nested(
            patch.object(
                mod, '_is_docker', MagicMock(return_value=True)
            ),
            patch.object(
                mod, '_is_lxc', MagicMock(return_value=True)
            )
        ):
            self.assertTrue(fun())
        with contextlib.nested(
            patch.object(
                mod, '_is_docker', MagicMock(return_value=False)
            ),
            patch.object(
                mod, '_is_lxc', MagicMock(return_value=True)
            )
        ):
            self.assertTrue(fun())
        with contextlib.nested(
            patch.object(
                mod, '_is_docker', MagicMock(return_value=True)
            ),
            patch.object(
                mod, '_is_lxc', MagicMock(return_value=False)
            )
        ):
            self.assertTrue(fun())
        with contextlib.nested(
            patch.object(
                mod, '_is_docker', MagicMock(return_value=False)
            ),
            patch.object(
                mod, '_is_lxc', MagicMock(return_value=False)
            )
        ):
            self.assertFalse(fun())

    def test_routes(self):
        class obj:
            stdout = StringIO.StringIO(rt1)
        with patch.object(subprocess, 'Popen', return_value=obj):
            fun = self.get_private('makina_grains._routes')
            ret = fun()
            self.assertEqual(
                ret,
                ([{'flags': 'UG',
                   'gateway': '125.124.124.1',
                   'genmask': '0.0.0.0',
                   'iface': 'br0',
                   'irtt': '0',
                   'mss': '0',
                   'window': '0'},
                  {'flags': 'U',
                   'gateway': '0.0.0.0',
                   'genmask': '255.255.255.0',
                   'iface': 'lxcbr0',
                   'irtt': '0',
                   'mss': '0',
                   'window': '0'},
                  {'flags': 'U',
                   'gateway': '0.0.0.0',
                   'genmask': '255.255.0.0',
                   'iface': 'lxcbr1',
                   'irtt': '0',
                   'mss': '0',
                   'window': '0'},
                  {'flags': 'UG',
                   'gateway': '10.90.48.65',
                   'genmask': '255.254.0.0',
                   'iface': 'eth1',
                   'irtt': '0',
                   'mss': '0',
                   'window': '0'},
                  {'flags': 'U',
                   'gateway': '0.0.0.0',
                   'genmask': '255.255.255.192',
                   'iface': 'eth1',
                   'irtt': '0',
                   'mss': '0',
                   'window': '0'},
                  {'flags': 'U',
                   'gateway': '0.0.0.0',
                   'genmask': '255.255.255.0',
                   'iface': 'virbr0',
                   'irtt': '0',
                   'mss': '0',
                   'window': '0'},
                  {'flags': 'U',
                   'gateway': '0.0.0.0',
                   'genmask': '255.255.255.0',
                   'iface': 'br0',
                   'irtt': '0',
                   'mss': '0',
                   'window': '0'}],
                 {'flags': 'UG',
                  'gateway': '125.124.124.1',
                  'genmask': '0.0.0.0',
                  'iface': 'br0',
                  'irtt': '0',
                  'mss': '0',
                  'window': '0'},
                 '125.124.124.1'))

    def test_is_lxc(self):

        def raise_(*a):
            raise IOError()

        wopen = mock_open(read_data='foo')
        gopen = mock_open(read_data=':cpu:/a')
        g1open = mock_open(read_data=':cpuset:/a')
        agopen = mock_open(read_data=':cpu:/')
        ag1open = mock_open(read_data=':cpuset:/')
        noopen = MagicMock(side_effect=raise_)
        fun = self.get_private('makina_grains._is_lxc')
        mod = sys.modules[fun.__module__]

        with self.patch(
            grains={'makina.lxc': None},
            filtered=['mc.*'],
            kinds=['grains', 'modules']
        ):
            with patch.object(
                mod, '_is_docker', MagicMock(return_value=True)
            ):
                ret4 = fun()
                with patch('__builtin__.open', wopen):
                    reta = fun()
                with patch('__builtin__.open', gopen):
                    retb = fun()
            with patch.object(
                mod, '_is_docker', MagicMock(return_value=False)
            ):
                with patch('__builtin__.open', wopen):
                    ret5 = fun()
                with patch('__builtin__.open', noopen):
                    ret6 = fun()
                with patch('__builtin__.open', g1open):
                    ret7 = fun()
                with patch('__builtin__.open', gopen):
                    ret8 = fun()
                with patch('__builtin__.open', ag1open):
                    ret11 = fun()
                with patch('__builtin__.open', agopen):
                    ret12 = fun()
            with self.patch(
                grains={'makina.lxc': True},
                filtered=['mc.*'],
                kinds=['grains', 'modules']
            ):
                ret1 = copy.deepcopy(self.grains)
        with self.patch(
            grains={'makina.lxc': True},
            filtered=['mc.*'],
            kinds=['grains', 'modules']
        ):
            with patch.object(
                mod, '_is_docker', MagicMock(return_value=False)
            ):
                ret14 = fun()
        with self.patch(
            grains={'makina.lxc': False},
            filtered=['mc.*'],
            kinds=['grains', 'modules']
        ):
            with patch.object(
                mod, '_is_docker', MagicMock(return_value=False)
            ):
                ret15 = fun()
        self.assertFalse(ret4)
        self.assertFalse(ret5)
        self.assertFalse(ret6)
        self.assertFalse(ret11)
        self.assertFalse(ret12)
        self.assertFalse(ret15)
        self.assertTrue(ret1)
        self.assertTrue(ret7)
        self.assertTrue(ret8)
        self.assertFalse(reta)
        self.assertFalse(retb)
        self.assertTrue(ret14)


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
