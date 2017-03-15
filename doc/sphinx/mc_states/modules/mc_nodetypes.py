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
DEFAULT_NT = 'scratch'
log = logging.getLogger(__name__)
NODETYPES = ['lxccontainer',
             'dockercontainer',
             'vagrantvm',
             'devhost',
             'travis',
             'kvm',
             'laptop',
             'vm',
             'server']


def environ():
    return copy.deepcopy(os.environ)


def get_makina_grains():
    '''
    Expose real time grains
    '''
    return makina_grains.get_makina_grains(_o=__opts__)


def is_upstart():
    return makina_grains._is_upstart(_o=__opts__)


def is_systemd():
    return makina_grains._is_systemd(_o=__opts__)


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
        nt = makina_grains._nodetype(_o=__opts__)
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
    return makina_grains._is_travis(_o=__opts__)


def is_docker():
    return makina_grains._is_docker(_o=__opts__)


def is_lxc():
    return makina_grains._is_lxc(_o=__opts__)


def is_container():
    return is_lxc() or is_docker()


def is_vagrantvm():
    return makina_grains._is_vagrantvm(_o=__opts__)


def is_devhost():
    return (makina_grains._is_devhost(_o=__opts__) or
            is_vagrantvm())


def is_docker_service():
    return is_docker()


def is_vm():
    reg = registry()
    for i in NODETYPES:
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


def get_nodetypes():
    nodetypes = set()
    if is_scratch():
        nodetypes.add('scratch')
    else:
        for i in NODETYPES:
            if is_nt(i):
                nodetypes.add(i)
    return [a for a in nodetypes]


def has_system_services_manager():
    '''
    Does the actual host has a system level services manager
    aka a PIDEINS
    '''
    return not is_docker()


def activate_sysadmin_states():
    '''retrocompat'''
    return True
