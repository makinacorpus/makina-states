# -*- coding: utf-8 -*-
'''
.. _module_mc_snmpd:

mc_snmpd / snmpd functions
===========================



snmpd module

'''
# Import python libs
import logging
import mc_states.api

__name = 'snmpd'

log = logging.getLogger(__name__)


def settings():
    '''
    snmpd settings

        SNMPDRUN
            yes
        MIBS    
            /usr/share/mibs
        SNMPDOPTS
            -Lsd -Lf /dev/null -p /var/run/snmpd.pid
        TRAPDRUN
            no
        TRAPDOPTS
            -Lsd -p /var/run/snmptrapd.pid
        agentAddress
            udp:161,udp6:[::1]:161
        default_user
            user
        default_key
            sup3rs3cret
        default_password
            s3cret
        default_enc_type
            DES
        default_password_enc_type
            SHA
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _salt = __salt__
        grains = __grains__
        pillar = __pillar__
        nodetypes_registry = _salt['mc_nodetypes.registry']()
        locs = _salt['mc_locations.settings']()
        data = _salt['mc_utils.defaults'](
            'makina-states.services.monitoring.snmpd', {
                'SNMPDRUN': 'yes',
                'MIBS': '/usr/share/mibs',
                'SNMPDOPTS': '-Lsd -Lf /dev/null -p /var/run/snmpd.pid',
                'TRAPDRUN': 'no',
                'TRAPDOPTS': '-Lsd -p /var/run/snmptrapd.pid',
                'agentAddress': 'udp:161,udp6:[::1]:161',
                'default_user': 'user',
                'default_key': 'sup3rs3cret',
                'default_password': 's3cret',
                'default_enc_type': 'DES',
                'default_password_enc_type': 'SHA',
            }
        )
        return data
    return _settings()



#
