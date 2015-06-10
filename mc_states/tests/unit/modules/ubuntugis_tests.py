#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base
import mock
from mc_states.api import six
import mc_states.api


class TestCase(base.ModuleCase):

    def test_settings(self):
        func = self._('mc_ubuntugis.settings')
        with self.patch(
            funcs={
                'modules': {
                    'mc_pkgs.settings':
                    mock.MagicMock(return_value={
                        'udist': 'doo',
                        'ubuntu_lts': 'boo'
                    })
                }
            },
            grains={
                'os_family': 'Debian',
                'os': 'Debian',
                'osrelease': 'jessie',
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            mc_states.api.invalidate_memoize_cache('localreg_ubuntugis_settings')
            ret = func()
            self.assertEqual(dict(ret),
                             {'ppa': 'stable',
                              'pkgs': ['libgeos-dev'],
                              'dist': 'boo', 'ubuntu_ppa': 'ppa'})
        with self.patch(
            funcs={
                'modules': {
                    'mc_pkgs.settings':
                    mock.MagicMock(return_value={
                        'udist': 'doo',
                        'ubuntu_lts': 'boo'
                    })
                }
            },
            grains={
                'os_family': 'Debian',
                'os': 'Ubuntu',
                'osrelease': '12.04',
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            mc_states.api.invalidate_memoize_cache('localreg_ubuntugis_settings')
            ret = func()
            self.assertEqual(dict(ret),
                             {'ppa': 'stable',
                              'pkgs': ['libgeos-dev'],
                              'dist': 'doo', 'ubuntu_ppa': 'ppa'})
        with self.patch(
            funcs={
                'modules': {
                    'mc_pkgs.settings':
                    mock.MagicMock(return_value={
                        'udist': 'doo',
                        'ubuntu_lts': 'boo'
                    })
                }
            },
            grains={
                'os_family': 'Debian',
                'os': 'Ubuntu',
                'osrelease': '14.04',
            },
            filtered=['mc.*'],
            kinds=['modules']
        ):
            mc_states.api.invalidate_memoize_cache('localreg_ubuntugis_settings')
            ret = func()
            self.assertEqual(dict(ret),
                             {'ppa': 'unstable', 'dist': 'doo',
                              'pkgs': ['libgeos-dev'],
                              'ubuntu_ppa': 'ubuntugis-unstable'})

if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
