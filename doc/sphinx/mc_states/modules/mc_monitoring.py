# -*- coding: utf-8 -*-
'''

.. _module_mc_monitoring:

mc_monitoring registry
============================================

'''
# Import python libs
import logging
import mc_states.api

__name = 'monitoring'

log = logging.getLogger(__name__)


def settings():
    '''
    monitoring

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        has_sysstat = not __salt__['mc_nodetypes.is_vm']()
        monitoringData = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.client', {
                'has_sysstat': has_sysstat and True or False,
                'sysstat_rotate_periodicity': '59 23 * * *',
                'sysstat_periodicity': '*/3 * * * *',
                'sysstat_rotate_count': '60 2',
                'sysstat_count': '20 3',
                'sysstat_history': 3*31,
                'sysstat_compress': 2*31,
                'sysstat_sadc_opts': "-S XDISK",
            }
        )
        return monitoringData
    return _settings()



# 
