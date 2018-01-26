#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
.. _module_mc_state:

mc_state / module to execute functions on salt
================================================
'''


import hashlib


def patch(mod, key=None):
    h = hashlib.new('sha512')
    h.update(key)
    sha = h.hexdigest()
    default = {'__env__': "base", '__instance_id__': sha}
    for k in ['__env__',
              '__pillar__',
              '__instance_id__',
              '__grains__',
              '__salt__',
              '__opts__']:
        mkey = 'mc_old__{0}'.format(k)
        if getattr(mod, mkey, None):
            continue
        oldk = getattr(mod, k, None)
        setattr(mod, mkey, oldk)
        if not oldk:
            setattr(mod, k, globals().get(k, default.get(k)))


def unpatch(mod, key=None):
    for k in ['__env__',
              '__instance_id__',
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

     Eg

     .. code-block:: python

        from salt.states import file as sfile
        __salt__['mc_state.sexec'](
            sfile, 'managed', name = os.path.join(lgit, 'hooks/pre-receive'),
            source=(
            'salt://makina-states/files/projects/2/'
            'hooks/pre-receive'),
            defaults={'api_version': api_version, 'name': name},
            user=user, group=group, mode='750', template='jinja')
    '''
    ret = None
    key = repr(mod).split()[1] + func
    try:
        key += repr(a)
    except Exception:
        pass
    try:
        key += repr(kw)
    except Exception:
        pass
    try:
        patch(mod, key)
        ret = getattr(mod, func)(*a, **kw)
    finally:
        unpatch(mod, key)
    return ret
# vim:set et sts=4 ts=4 tw=80:
