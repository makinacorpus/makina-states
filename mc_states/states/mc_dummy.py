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


def dummy(name):
    '''
    State that will always return ret, use that for orchestration purpose

    name
        name of dummy state

    '''
    ret = {'name': name,
           'result': True,
           'comment': 'Dummy state for {0}'.format(name),
           'changes': {}}
    return ret

#
