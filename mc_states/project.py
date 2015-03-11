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



class _BaseProjectException(salt.exceptions.SaltException):
    '''Project global exc'''
    def __init__(self, *args, **kw):
        if args:
            cargs = [args[0]]
        else:
            cargs = []
        super(_BaseProjectException, self).__init__(*cargs)
        self.deploy_args = args
        self.deploy_kw = kw
        for attr in ['salt_ret', 'salt_step']:
            if attr in self.deploy_kw:
                setattr(self, attr, self.deploy_kw[attr])


class ProjectException(_BaseProjectException):
    '''Project global exc'''


class ProjectNotCleanError(ProjectException):
    '''Project global exc'''


class ProjectInitException(ProjectException):
    '''Project init exc'''


class ProjectProcedureException(_BaseProjectException):
    '''Project init exc'''


class TooEarlyError(ProjectInitException):
    '''.'''


class RemoteProjectException(ProjectException):
    """."""


class BaseProjectInitException(ProjectException):
    """."""


class RemoteProjectInitException(BaseProjectInitException):
    """."""


class RemotePillarInitException(BaseProjectInitException):
    """."""


class BaseRemoteProjectSyncError(RemoteProjectException):
    """."""


class RemoteProjectSyncError(BaseRemoteProjectSyncError):
    """."""


class RemoteProjectTransferError(RemoteProjectSyncError):
    """."""


class RemoteProjectWCSyncError(RemoteProjectSyncError):
    """."""


class RemoteProjectSyncRemoteError(RemoteProjectSyncError):
    """."""


class RemoteProjectDeployError(RemoteProjectException):
    """."""
# vim:set et sts=4 ts=4 tw=80:
