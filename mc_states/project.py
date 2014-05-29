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
ENVS = {
    'prod': ['prod'],
    'dev': ['dev'],
    'qa': ['staging', 'test', 'preprod'],
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
