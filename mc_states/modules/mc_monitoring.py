# -*- coding: utf-8 -*-
'''

.. _module_mc_monitoring:

mc_monitoring registry
============================================

'''
# Import python libs
import logging
import mc_states.utils

__name = 'monitoring'

log = logging.getLogger(__name__)


def settings():
    '''
    monitoring

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        has_sysstat = not __salt__['mc_nodetypes.is_vm']()
        monitoringData = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.client', {
                'has_sysstat': has_sysstat and "true" or "false",
                'sysstat_rotate_periodicity': '59 23 * * *',
                'sysstat_periodicity': '*/3 * * * *',
                'sysstat_rotate': '60 2',
            }
        )
        return monitoringData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

# 
