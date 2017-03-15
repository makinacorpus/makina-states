# -*- coding: utf-8 -*-
'''
.. _module_mc_rdiffbackup:

mc_rdiff-backup / rdiff-backup functions
============================================



'''

# Import python libs
import logging
import mc_states.api

from salt.utils.odict import OrderedDict

__name = 'rdiffbackup'

log = logging.getLogger(__name__)


def settings():
    '''
    rdiff-backup settings

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.backup.rdiff-backup', {
            }
        )
        return data
    return _settings()



#
