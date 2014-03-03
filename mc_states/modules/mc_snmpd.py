'''
.. _module_mc_snmpd:

mc_snmpd / snmpd functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'snmpd'

log = logging.getLogger(__name__)

def settings():
    '''
    snmpd settings


    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locs = localsettings['locations']
        data = __salt__['mc_utils.defaults'](
             'makina-states.services.monitoring.snmpd', {
                'SNMPDRUN':'yes',
                'SNMPDOPTS':'-Lsd -Lf /dev/null -p /var/run/snmpd.pid',
                'TRAPDRUN':'no',
                'TRAPDOPTS':'-Lsd -p /var/run/snmptrapd.pid',
                'agentAddress':'udp:161,udp6:[::1]:161'
            }
        )
        return data
    return _settings()

def dump():
    return mc_states.utils.dump(__salt__,__name)

#
