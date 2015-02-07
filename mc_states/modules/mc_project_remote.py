# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
__docformat__ = 'restructuredtext en'
'''

.. _module_mc_project_remote:

mc_project_remote / remote project execution functions
============================================================
The following functions are related to do remote executions over ssh transport.
This acts on corpus based projects to deploy an maintain them
as you would do with a local salt-call or a git push
'''


def run(host, fun, project=None, only=None, only_steps=None, **kw):
    '''
    Run a mc_project.deploy call on an remote host
    '''
    if only is None:
        only = []
    if isinstance(only, basestring):
        only = only.split(',')
    if isinstance(only_steps, basestring):
        only_steps = only_steps.split(',')
    for step in [
        'archive', 'sync_hooks', 'sync_modules',
        'install', 'fixperms'
    ]:
        val = kw.get('project_step_{0}'.format(step), None)
        if val and val is not None:
            if step not in only:
                only.append(step)
    only = __salt__['mc_utils.uniquify'](only)
    only_steps = __salt__['mc_utils.uniquify'](only_steps)
    arg = [project]
    kwarg = {}
    if only:
        kwarg['only'] = only
    if only:
        kwarg['only_steps'] = only_steps
        return __salt__['mc_remote.salt_call'](host,
                                               'mc_project.{0}'.format(fun),
                                               arg=arg, kwarg=kwarg,
                                               **kw)


def report(host, **kw):
    '''
    Run a mc_project.report call on an remote host
    '''
    return run(host, 'report', **kw)


def configuration(host, project, only=None, only_steps=None, **kw):
    '''
    Run a mc_project.get_configuration call on an remote host
    '''
    return run(host, project, 'get_configuration', **kw)


def deploy(host, project, only=None, only_steps=None, **kw):
    '''
    Run a mc_project.deploy call on an remote host
    '''
    return run(host, 'deploy', project, only=only, only_steps=only_steps, **kw)


def install(host,
            project,
            install=True,
            fixperms=True,
            only_steps=None,
            **kw):
    '''
    Run a mc_project.deploy call on an remote host, without
    the archive & rollback steps
    '''
    if not any((install, fixperms)):
        raise ValueError('choose at least install or fixperms for'
                         ' deploying {0}'.format(host))
    return deploy(host,
                  project,
                  project_step_install=install,
                  project_step_fixperms=fixperms,
                  only_steps=only_steps,
                  **kw)
# vim:set et sts=4 ts=4 tw=80:
