#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
.. _module_mc_state:

mc_state / module to execute functions on salt
================================================
'''

__docformat__ = 'restructuredtext en'


def patch(mod):
    default = {'__env__': "base"}
    for k in ['__env__',
              '__pillar__',
              '__grains__',
              '__salt__',
              '__opts__']:
        mkey = 'mc_old__{0}'.format(k)
        if getattr(mod, mkey, None):
            continue
        oldk = getattr(mod, k, None)
        setattr(mod, mkey, oldk)
        if not oldk:
            setattr(mod, k, globals()[k] or default.get(k))


def unpatch(mod):
    for k in ['__env__',
              '__pillar__',
              '__grains__',
              '__salt__',
              '__opts__']:
        mkey = 'mc_old__{0}'.format(k)
        if not getattr(mod, mkey, None):
            continue
        setattr(mod, k, getattr(mod, mkey))
        delattr(mod, mkey)


def sexec(mod, func, *a, **kw):
    '''
    Execute a function in a state module as if it is a state
    function, we dumb inject the salt variable globs on
    the fly.
    This is mainly only usable from other modules or runners
    as the first argument is a python module object.

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

     Eg::

      >>> from salt.states import file as sfile
      >>> __salt__['mc_state.sexec'](
            sfile, 'managed', name = os.path.join(lgit, 'hooks/pre-receive'),
            source=(
            'salt://makina-states/files/projects/2/'
            'hooks/pre-receive'),
            defaults={'api_version': api_version, 'name': name},
            user=user, group=group, mode='750', template='jinja')
    '''
    ret = None
    try:
        patch(mod)
        ret = getattr(mod, func)(*a, **kw)
    finally:
        unpatch(mod)
    return ret
# vim:set et sts=4 ts=4 tw=80:
