'''
.. _module_mc_nodetypes:

mc_nodetypes / nodetypes registry
============================================

'''


import os
import mc_states.api
from  mc_states.grains import makina_grains

__name = 'nodetypes'
DEFAULT_NT = 'server'


def metadata():
    '''nodetypes metadata registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings', 'services'])
    return _metadata()


def settings():
    '''nodetypes settings registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        metadata = __salt__['mc_{0}.metadata'.format(__name)]()
        return locals()
    return _settings()


def is_nt(nodetype):
    if nodetype == DEFAULT_NT:
        return True
    is_nodetype = None
    tflag = '/etc/makina-states/nodetype'
    if nodetype == 'travis':
        if os.environ.get('TRAVIS', 'false') == 'true':
            is_nodetype = True
    is_nodetype = __salt__['mc_utils.get'](
        'makina-states.nodetypes.{0}'.format(nodetype), None)
    if os.path.exists(tflag) and (is_nodetype is None):
        with open(tflag) as f:
            try:
                is_nodetype = f.read().strip().lower() == nodetype
            except Exception:
                is_nodetype = None
    is_nodetype = None
    if (
        nodetype in ['lxccontainer', 'dockercontainer'] and
        is_nodetype is None
    ):
        nt = nodetype.replace('container', '')
        try:
            is_nodetype = __salt__[
                'mc_cloud_{0}.is_{0}'.format(nt)]()
        except Exception:
            is_nodetype = None
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


def is_container():
    reg = registry()
    for i in ['lxccontainer', 'dockercontainer']:
        if reg['is'].get(i, False):
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
