'''
.. _module_mc_nodetypes:

mc_nodetypes / nodetypes registry
============================================

'''


import os
import mc_states.utils

__name = 'nodetypes'


def metadata():
    '''nodetypes metadata registry'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings', 'services'])
    return _metadata()


def settings():
    '''nodetypes settings registry'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        resolver = __salt__['mc_utils.format_resolve']
        metadata = __salt__['mc_{0}.metadata'.format(__name)]()
        return locals()
    return _settings()


def registry():
    '''nodetypes registry registry'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        travis = False
        if os.environ.get('TRAVIS', 'false') == 'true':
            travis = True
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

def dump():
    return mc_states.utils.dump(__salt__, __name)

#
