'''
.. _module_mc_nodetypes:

mc_nodetypes / nodetypes registry
============================================

'''


import os
import mc_states.api
from  mc_states.grains import makina_grains

__name = 'nodetypes'


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


def is_travis():
    travis = False
    tflag = '/etc/makina-states/nodetype'
    if (
        os.path.exists(tflag)
        or os.environ.get('TRAVIS', 'false') == 'true'
    ):
        travis = True
    if os.path.exists(tflag) and not travis:
        with open(tflag) as f:
            try:
                travis = f.read().strip().lower() == 'travis'
            except Exception:
                travis = False
    return travis


def registry():
    '''nodetypes registry registry'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _registry():
        travis = is_travis()
        reg = __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'server': {'active': True},
            'kvm': {'active': False},
            'vm': {'active': False},
            'devhost': {'active': False},
            'travis': {'active': travis},
            'vagrantvm': {'active': False},
            'lxccontainer': {'active': False},
            'dockercontainer': {'active': False},
        })
        return reg
    return _registry()


def is_devhost():
    return makina_grains._is_devhost()


def is_vm():
    reg = registry()
    for i in [
        'kvm',
        'travis',
        'lxccontainer',
        'dockercontainer',
    ]:
        if reg['is'].get(i, False):
            return True
    return False
#
