# -*- coding: utf-8 -*-
'''
Dummy state generation
=======================
'''

def __virtual__():
    '''
    Only load if mc_dummy is available
    '''
    return 'mc_dummy'


def dummy(name, changes=None):
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
    return dummy(name, changes={1: 1})
#
