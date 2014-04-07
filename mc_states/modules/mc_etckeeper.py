'''

.. _module_mc_etckeeper:

mc_etckeeper
============================================

'''
# Import python libs
import logging
import mc_states.utils

__name = 'etckeeper'

log = logging.getLogger(__name__)


def settings():
    '''
    etckeeper

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        # etckeeper
        etckeeperData = __salt__['mc_utils.defaults'](
            'makina.localsettings.etckeeper', {
                'pm': 'apt',
                'installer': 'dpkg',
                'specialfilewarning': False,
                'autocommit': True,
                'vcs': 'git',
                'commitbeforeinstall': True})
        return etckeeperData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

# 
