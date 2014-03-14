#!/usr/bin/env python
'''
.. _mc_states_project:

mc_states_project / general projects API
========================================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from salt.exceptions import SaltException

LAST_PROJECT_API_VERSION = "2"
EDITABLE_MODE = 'editable'
COOKING_MODE = 'cooking'
FINAL_MODE = 'final'
OPERATION_MODES = [EDITABLE_MODE,
                   COOKING_MODE,
                   FINAL_MODE]

DEFAULTS_SKIPS = {
    FINAL_MODE: {
        True: [
            'skip_build',
        ],
    },
    EDITABLE_MODE: {
        True: [
            'skip_archive',
            'skip_rollback',
            'skip_release_sync',
            'skip_reconfigure',
            'skip_bundle',
        ],
    },
    COOKING_MODE: {
        True: [
            'skip_archive',
            'skip_release_sync',
            'skip_rollback',
        ],
    },
}
ENVS = {
    'prod': ['prod'],
    'dev': ['dev'],
    'qa': ['staging',
           'test',
           'preprod'],
}
_DEFAULT = object()


class ProjectException(SaltException):
    '''Project global exc'''


class ProjectInitException(SaltException):
    '''Project init exc'''

class ProjectProcedureException(SaltException):
    '''Project init exc'''


    def __init__(self, *args, **kw):
        super(ProjectProcedureException, self).__init__(*args)
        self.salt_ret = kw.get('salt_ret', None)
        self.salt_step = kw.get('salt_step', None)

# vim:set et sts=4 ts=4 tw=80:
