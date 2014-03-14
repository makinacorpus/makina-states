#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
.. _module_mc_state:

mc_state / module to execute functions on salt
================================================
'''
 
__docformat__ = 'restructuredtext en'

def sexec(mod, func, *a, **kw):
    '''
    Execute a function in a module as if it is a state
    function, we dumb inject the salt variable sglobs on
    the fly.
    This is mainly only usable from other modules as the first
    argument is a python module object.

        mod
            python module to search the function on
        func
            function to execute
        a
            positionnal arguments to pass to the function
        kw
            keyword arguments to pass to the function

       Eg in an execution module:


        def func():
            """Wrapper to the  user state"""
            from salt.states import user as suser
            __salt__['mc_state.exec'](suser, 'present', 'foo')

    '''
    if not getattr(mod,' __env__', None):
        setattr(mod, '__env__', 'base')
    if not getattr(mod,' __salt__', None):
        setattr(mod, '__salt__', __salt__)
    if not getattr(mod,' __opts__', None):
        setattr(mod, '__opts__', __opts__)
    if not getattr(mod,' __grains__', None):
        setattr(mod, '__grains__', __grains__)
    return getattr(mod, func)(*a, **kw)
# vim:set et sts=4 ts=4 tw=80:
