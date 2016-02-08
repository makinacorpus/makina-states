# -*- coding: utf-8 -*-
'''
.. _module_mc_controllers:

mc_controllers / controllers related variables
================================================

'''

# Import salt libs
import os
import mc_states.api
import logging

__name = 'controllers'


def metadata():
    '''controllers metadata registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings'])
    return _metadata()


def has_mastersalt():
    has_mastersalt = False
    bootsalt_mode = makina_grains._bootsalt_mode()
    if bootsalt_mode == 'mastersalt':
        has_mastersalt = True
    try:
        with open('/etc/makina-states/mode') as fic:
            has_mastersalt = 'mastersalt' in fic.read()
    except Exception:
        pass
    for i in [
        '/usr/bin/mastersalt-call',
        '/usr/bin/mastersalt',
        '/etc/mastersalt/minion',
        '/etc/mastersalt/master'
    ]:
        if has_mastersalt:
            break
        has_mastersalt = os.path.exists(i)
    return has_mastersalt


def has_mastersalt_running():
    ret = False
    pids = []
    all_pids = [int(pid) for pid in os.listdir('/proc') if pid.isdigit()]
    if not all_pids:
        processes = __salt__['cmd.run']('ps aux')
        for line in processes.splitlines():
            if ('/salt-minion' in line) and ('-c /etc/mastersalt' in line):
                chunks = line.split()
                if __salt__['mc_utils.filter_host_pids'](
                    [int(chunks[1])]
                ):
                    ret = True
                    break
    else:
        for pid in all_pids:
            line = ''
            try:
                with open(
                    os.path.join('/proc', str(pid), 'cmdline'),
                    'rb'
                ) as fic:
                    line = fic.read().replace('\x00', ' ')
            except IOError:
                continue
            if ('salt-minion' in line) and ('-c /etc/mastersalt' in line):
                if __salt__['mc_utils.filter_host_pids'](
                    [pid]
                ):
                    ret = True
                    break
    return ret


def mastersalt_mode():
    return (
        (
            has_mastersalt()
            and 'mastersalt' in __salt__['mc_utils.get']('config_dir')
        ))


def allow_lowlevel_states():
    '''
    Do we allow low level states

    in dual stack saltstack installs, only allow low level states
    on the mastersalt side
    in other cases, without the presence of the conf flag
    this will return 'unkown' also ensuring that in this case
    we can apply the states (no complete makina-states installs)
    '''
    if has_mastersalt():
        return mastersalt_mode()
    return True


def masterless():
    ret = False
    if not mastersalt_mode():
        if __salt__['mc_salt.get_local_salt_mode']() == "masterless":
            ret = True
    if mastersalt_mode():
        if __salt__['mc_salt.get_local_mastersalt_mode']() == "masterless":
            ret = True
    return ret


def settings():
    '''controllers settings registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        data = dict(metadata=saltmods['mc_{0}.metadata'.format(__name)]())
        return data
    return _settings()


def registry():
    '''controllers registry registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _registry():
        has_m = has_mastersalt()
        return  __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'mastersalt_minion': {'active': False},
            'mastersalt_master': {'active': False},
            'mastersalt_masterless': {'active': False},
            'mastersalt': {'active': False},
            'salt_minion': {'active': False},
            'salt_master': {'active': False},
            'salt_masterless': {'active': False},
            'salt': {'active': False},
        })
    return _registry()


def _local_salt_mode(typ, mode):
    fmode = '/etc/makina-states/local_{0}_mode'.format(typ)
    if os.path.exists(fmode):
        with open(fmode) as fic:
            mode = fic.read().strip()
    return mode


def local_mastersalt_mode():
    return _local_salt_mode('mastersalt', 'remote')


def local_salt_mode():
    return _local_salt_mode('salt', 'masterless')
