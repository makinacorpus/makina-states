# -*- coding: utf-8 -*-
'''
.. _module_mc_nodetypes:

mc_nodetypes / nodetypes registry
============================================

'''


import os
import copy
import logging
import mc_states.api
from mc_states.grains import makina_grains


__name = 'nodetypes'
DEFAULT_NT = 'server'
log = logging.getLogger(__name__)


def environ():
    return copy.deepcopy(os.environ)


def get_makina_grains():
    '''
    Expose real time grains
    '''
    return makina_grains.get_makina_grains()


def is_upstart():
    return makina_grains._is_upstart()


def is_systemd():
    return makina_grains._is_systemd()


def metadata():
    '''
    nodetypes metadata registry
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings', 'services'])
    return _metadata()


def settings():
    '''
    nodetypes settings registry
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        return {'metadata': __salt__['mc_{0}.metadata'.format(__name)]()}
    return _settings()


def is_fs_nodetype(nodetype):
    try:
        is_nodetype = (
            makina_grains._get_msconf(
                'nodetype').lower() == nodetype)
    except Exception:
        is_nodetype = None
    return is_nodetype


def is_nt(nodetype):
    is_nodetype = None
    is_nodetype = __salt__['mc_utils.get'](
        'makina-states.nodetypes.{0}'.format(nodetype), None)
    if is_nodetype is None:
        is_nodetype = is_fs_nodetype(nodetype)
    if is_nodetype is None:
        is_nodetype = False
    return is_nodetype


def registry():
    '''nodetypes registry registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _registry():
        reg_nt = {
            'scratch': {'active': False},
            'server': {'active': False},
            'kvm': {'active': False},
            'vm': {'active': False},
            'devhost': {'active': False},
            'travis': {'active': False},
            'vagrantvm': {'active': False},
            'lxccontainer': {'active': False},
            'laptop': {'active': False},
            'dockercontainer': {'active': False}}
        nt = makina_grains._nodetype()
        if nt:
            if nt in reg_nt:
                reg_nt[nt] = {'active': True}
            else:
                log.error('{0}: invalid nodetype'.format(nt))
        for nt in [a for a in reg_nt]:
            reg_nt[nt]['active'] = is_nt(nt)
        reg = __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults=reg_nt)
        return reg
    return _registry()


def is_scratch():
    reg = registry()
    true = False
    for k in [
        'server', 'vm',
        'kvm',
        'container', 'dockercontainer', 'lxccontainer',
    ]:
        if k in reg['actives']:
            true = True
            break
    return not true


def is_travis():
    return makina_grains._is_travis()


def is_docker():
    return makina_grains._is_docker()


def is_lxc():
    return makina_grains._is_lxc()


def is_container():
    return is_lxc() or is_docker()


def is_vagrantvm():
    return makina_grains._is_vagrantvm()


def is_devhost():
    return makina_grains._is_devhost() or is_vagrantvm()


def is_container_nodetype(nodetype):
    is_nodetype = None
    _s = __salt__
    if nodetype in ['lxccontainer', 'dockercontainer']:
        nt = nodetype.replace('container', '')
        try:
            is_nodetype = _s['mc_nodetypes.is_{0}'.format(nt)]()
        except Exception:
            is_nodetype = None
    return is_nodetype


def is_docker_service():
    return (
        is_docker() and
        not __salt__['mc_controllers.mastersalt_mode']())


def is_vm():
    reg = registry()
    for i in [
        'lxccontainer',
        'dockercontainer',
        'vagrantvm',
        'devhost',
        'travis',
        'kvm',
        'vm',
    ]:
        if is_nt(i):
            return True
        elif reg['is'].get(i, False):
            return True
    for i in [
        is_travis,
        is_devhost,
        is_vagrantvm,
        is_docker,
        is_container,
        is_lxc
    ]:
        if i():
            return True
    return False


def has_system_services_manager():
    '''
    Does the actual host has a system level services manager
    aka a PIDEINS
    '''
    return not is_docker()


def activate_sysadmin_states():
    if (
        __salt__['mc_controllers.mastersalt_mode']() and
        not is_docker_service()
    ) or (
        is_docker_service()
    ):
        return True
    return False
