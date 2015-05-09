#!/usr/bin/env python
import unittest
from .. import base
from mc_states.api import invalidate_memoize_cache


class TestCase(base.ModuleCase):

    def test_settings(self):
        invalidate_memoize_cache('localreg_ulogd_settings')
        with self.patch(
            grains={'os': 'Ubuntu',
                    'oscodename': 'precise',
                    'os_family': 'Debian'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            data = self._('mc_ulogd.settings')()
            self.assertEquals(data['service_name'], 'ulogd')
        invalidate_memoize_cache('localreg_ulogd_settings')
        with self.patch(
            grains={'os': 'Ubuntu',
                    'oscodename': 'trusty',
                    'os_family': 'Debian'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            data = self._('mc_ulogd.settings')()
            self.assertTrue(isinstance(data['confs'], dict))
            self.assertEquals(data['service_name'], 'ulogd2')

if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
