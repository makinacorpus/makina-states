#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import os
import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest

J = os.path.join
D = os.path.dirname

STATES_DIR = J(D(D(D(__file__))), '_modules')
_NO_ATTR = object()

class ModuleCase(unittest.TestCase):
    '''Base test class
    Its main function is to be used in salt modules
    and to mock the __salt__, __pillar__ and __grains__ attributes
    all in one place

    '''
    _mods = tuple()

    def setUp(self):
        '''
        1. Monkey patch the __salt__, __grains__ & __pillar__ in the
        objects (certainly python modules) given in self.mods

            - This search in self._{grains, pillar, salt} for a dict containing
              the monkey patch replacement and defaults to {}
            - We will then have on the test class _salt, _grains & _pillar d
              dicts to be used and mocked in tests, this ensure that the mock
              has to be done only at one place, on the class attribute.

        '''
        for mod in self._mods:
            for patched in [
                'salt', 'pillar', 'grains'
            ]:
                patch_key = '_{0}'.format(patched)
                sav_attribute = '__old_{0}'.format(patched)
                attribute = '__{0}__'.format(patched)
                if not hasattr(mod, sav_attribute):
                    _patch = getattr(self, patch_key, {})
                    setattr(self, patch_key, _patch)
                    setattr(mod, sav_attribute,
                            getattr(mod, attribute, _NO_ATTR))
                    setattr(mod, attribute, _patch)

    def tearDown(self):
        '''
        1. Ungister any Monkey patch on  __salt__, __grains__ & __pillar__ in
        objects (certainly python modules) given in self.mods
        '''
        for mod in self._mods:
            for patched in [
                'salt', 'pillar', 'grains',
            ]:
                sav_attribute = '__old_{0}'.format(patched)
                _patch = getattr(mod, sav_attribute)
                attribute = '__{0}__'.format(patched)
                if _patch:
                    if _patch is not _NO_ATTR:
                        setattr(mod, attribute, _patch)
                    else:
                        delattr(mod, attribute)
                    delattr(mod, sav_attribute)

# vim:set et sts=4 ts=4 tw=80:
