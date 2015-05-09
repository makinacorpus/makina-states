#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base
from mc_states.api import invalidate_memoize_cache


class TestCase(base.ModuleCase):

    def test_m(self):
        invalidate_memoize_cache('localreg_services_metadata')
        data = self._('mc_services.metadata')()
        self.assertEquals(data, {'bases': ['localsettings'],
                                 'kind': 'services'})

    def test_settings(self):
        invalidate_memoize_cache('localreg_services_registry')
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.is_container': lambda: True
                }
            },
            grains={'os': 'Ubuntu',
                    'osrelease': '12.04',
                    'oscodename': 'precise',
                    'os_family': 'Debian'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            data = self._('mc_services.registry')()
            self.assertFalse(data['is']['log.ulogd'])

        fun = self.get_private('mc_services._ulogdEn')
        invalidate_memoize_cache('localreg_services_registry')
        with self.patch(
            funcs={
                'modules': {
                    'mc_nodetypes.is_container': lambda: True
                }
            },
            grains={'os': 'Ubuntu',
                    'osrelease': '14.04',
                    'oscodename': 'trusty',
                    'os_family': 'Debian'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            self.assertTrue(fun(self.salt))


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
