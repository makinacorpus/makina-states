#!/usr/bin/env python
'''
.. _mc_states_project:

mc_states_project / general projects API
========================================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import salt.exceptions

LAST_PROJECT_API_VERSION = "2"
KEEP_ARCHIVES = 3
ENVS = {
    'prod': ['prod'],
    'dev': ['dev'],
    'qa': ['staging', 'test', 'preprod'],
}
_DEFAULT = object()


class ProjectException(salt.exceptions.SaltException):
    '''Project global exc'''


class ProjectInitException(salt.exceptions.SaltException):
    '''Project init exc'''


class ProjectProcedureException(salt.exceptions.SaltException):
    '''Project init exc'''

    def __init__(self, *args, **kw):
        super(ProjectProcedureException, self).__init__(*args)
        self.salt_ret = kw.get('salt_ret', None)
        self.salt_step = kw.get('salt_step', None)


class TooEarlyError(ProjectInitException):
    '''.'''


class RemoteProjectException(salt.exceptions.SaltException):
    """."""

    def __init__(self, *args, **kw):
        super(RemoteProjectException, self).__init__()
        self.deploy_args = args
        self.deploy_kw = kw


class RemoteProjectInitException(RemoteProjectException):
    """."""


class RemotePillarInitException(ProjectInitException):
    """."""


class RemoteProjectSyncError(RemoteProjectException):
    """."""


class RemoteProjectSyncPillarError(RemoteProjectSyncError):
    """."""


class RemoteProjectSyncProjectError(RemoteProjectSyncError):
    """."""


class RemoteProjectDeployError(RemoteProjectException):
    """."""
# vim:set et sts=4 ts=4 tw=80:
