#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
__docformat__ = 'restructuredtext en'
from mc_states import api


def test_setup():
    '''
    Must be called twice:

        - from within unit test setUp
        - from the exec module
    '''
    api._CACHE_PREFIX['testkey'] = api._CACHE_PREFIX['key']
    api._CACHE_PREFIX['key'] = 'test'


def test_teardown():
    '''
    Must be called twice:

        - from within unit test setUp
        - from the exec module
    '''
    if 'testkey' in api._CACHE_PREFIX:
        api._CACHE_PREFIX['key'] = api._CACHE_PREFIX.pop('testkey')
# vim:set et sts=4 ts=5 tw=80:
