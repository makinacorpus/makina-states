# -*- coding: utf-8 -*-
'''
mc_postgres_extension / Wrapper to automaticly set the rigth pgsql to attack
==============================================================================
'''
from salt.states import postgres_extension as postgres


def absent(name, *args, **kw):
    '''Absent wrapper'''
    return __salt__['mc_pgsql.wrapper'](postgres.absent)(name, *args, **kw)


def present(name, *args, **kw):
    '''Present wrapper'''
    return __salt__['mc_pgsql.wrapper'](postgres.present)(name, *args, **kw)

# vim:set et sts=4 ts=4 tw=80:
