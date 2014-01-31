'''
Salt related variables
============================================

'''


import os
import mc_states.utils

__name = 'nodetypes'


def metadata():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata(REG):
        return __salt__['mc_macros.metadata'](
            __name, bases=['localsettings', 'services'])
    return metadata


def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings(REG):
        resolver = __salt__['mc_utils.format_resolve']
        metadata = __salt__['mc_localsettings.metadata']()
        return locals()
    return _settings()


def registry():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry(REG):
        settings = __salt__['mc_{0}.settings'.format(__name)]()
        travis = False
        for i in os.environ:
            if 'travis' in i.lower():
                travis = True
        reg = __salt__[
            'mc_macros.construct_registry_configuration'
        ](settings, defaults={
            'server': {'active': True},
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
