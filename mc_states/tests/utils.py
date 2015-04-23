#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function

import os
import shutil
import tempfile
from mc_states import api
from mc_states.modules import mc_locations

TMPDIRS = []


def test_setup():
    '''
    Must be called twice:

        - from within unit test setUp
        - from the exec module
    '''
    TMPDIR = tempfile.mkdtemp()
    if TMPDIR not in TMPDIRS:
        TMPDIRS.append(TMPDIR)
    api._CACHE_PREFIX['testkey'] = api._CACHE_PREFIX['key']
    api._CACHE_PREFIX['key'] = 'test'
    mc_locations.default_locs['root_dir'] = '{0}/'.format(TMPDIR)
    return TMPDIR


def test_teardown():
    '''
    Must be called twice:

        - from within unit test setUp
        - from the exec module
    '''
    if 'testkey' in api._CACHE_PREFIX:
        api._CACHE_PREFIX['key'] = api._CACHE_PREFIX.pop('testkey')
    mc_locations.default_locs['root_dir'] = '/'
    for tmp in TMPDIRS:
        if os.path.exists(tmp):
            shutil.rmtree(tmp)
# vim:set et sts=4 ts=5 tw=80:
