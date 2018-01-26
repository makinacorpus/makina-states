# -*- coding: utf-8 -*-
'''
mc_proxy / Dummy state generation
==================================



'''


def hook(name, changes=None, **kw):
    '''
    State that will always return ret, use that for orchestration purpose

    name
        name of dummy state

    '''
    if not changes:
        changes = {}
    ret = {'name': name,
           'result': True,
           'comment': 'Dummy state for {0}'.format(name),
           'changes': changes}
    return ret


def mod_watch(name, **kwargs):
    '''
    Execute a dummy state in case of watcher changes
    '''
    return hook(name, changes={1: 1})
#
