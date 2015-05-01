#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from .. import base
from mc_states.api import invalidate_memoize_cache


class TestCase(base.ModuleCase):

    def test_settings(self):
        invalidate_memoize_cache('localreg_memcached_settings')
        with self.patch(
            grains={'os': 'Ubuntu',
                    'oscodename': 'precise',
                    'os_family': 'Debian'},
            filtered=['mc.*'],
            kinds=['modules']
        ):
            data = self._('mc_memcached.settings')()
            self.assertEquals(data['conf']['unitcachesize'], '10M')

if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
