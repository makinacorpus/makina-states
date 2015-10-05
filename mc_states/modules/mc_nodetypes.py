# -*- coding: utf-8 -*-
'''
.. _module_mc_nodetypes:

mc_nodetypes / nodetypes registry
============================================

'''


import os
import copy
import mc_states.api
from mc_states.grains import makina_grains


__name = 'nodetypes'
DEFAULT_NT = 'server'


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
    tflag = '/etc/makina-states/nodetype'
    is_nodetype = None
    if os.path.exists(tflag):
        with open(tflag) as f:
            try:
                is_nodetype = f.read().strip().lower() == nodetype
            except Exception:
                is_nodetype = None
    return is_nodetype


def is_container_nodetype(nodetype):
    is_nodetype = None
    if nodetype in ['lxccontainer', 'dockercontainer']:
        nt = nodetype.replace('container', '')
        try:
            is_nodetype = __salt__[
                'mc_nodetypes.is_{0}'.format(nt)]()
        except Exception:
            is_nodetype = None
    return is_nodetype


def is_travis():
    return makina_grains._is_travis()


def is_nt(nodetype):
    if nodetype == DEFAULT_NT:
        return True
    is_nodetype = None
    if nodetype == 'travis':
        is_nodetype = is_travis()
    is_nodetype = __salt__['mc_utils.get'](
        'makina-states.nodetypes.{0}'.format(nodetype), None)
    if is_nodetype is None:
        is_nodetype = is_fs_nodetype(nodetype)
    if is_nodetype is None:
        is_nodetype = is_container_nodetype(nodetype)
    if is_nodetype is None:
        is_nodetype = False
    return is_nodetype


def registry():
    '''nodetypes registry registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _registry():
        reg_nt = {
            'server': {'active': True},
            'kvm': {'active': False},
            'vm': {'active': False},
            'devhost': {'active': False},
            'travis': {'active': False},
            'vagrantvm': {'active': False},
            'lxccontainer': {'active': False},
            'laptop': {'active': False},
            'dockercontainer': {'active': False}}
        reg_nt[DEFAULT_NT] = {'active': True}
        for nt in [a for a in reg_nt]:
            reg_nt[nt]['active'] = is_nt(nt)
        reg = __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults=reg_nt)
        return reg
    return _registry()


def is_devhost():
    return makina_grains._is_devhost()


def is_docker():
    return makina_grains._is_docker()


def is_container():

    return makina_grains._is_container()


def is_docker_service():
    return (
        is_docker() and
        not __salt__['mc_controllers.mastersalt_mode']()
    )


def activate_sysadmin_states():
    if (
        __salt__['mc_controllers.mastersalt_mode']() and
        not is_docker_service()
    ) or (
        is_docker_service()
    ):
        return True
    return False


def is_vm():
    reg = registry()
    if is_container():
        return True
    for i in ['kvm', 'travis']:
        if reg['is'].get(i, False):
            return True
    return False
