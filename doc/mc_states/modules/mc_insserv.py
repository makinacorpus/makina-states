# -*- coding: utf-8 -*-
'''
.. _module_mc_inssserv:

mc_inssserv / inssserv functions
==================================



'''

# Import python libs
import logging
import mc_states.api

__name = 'inssserv'
PREFIX ='makina-states.localsettings.{0}'.format(__name)
log = logging.getLogger(__name__)


def settings():
    '''
    inssserv settings

    '''
    _g = __grains__
    _s = __salt__
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = {
            'configs': {
                '/etc/insserv.conf.d/dnsmasq': {},
            }
        }
        return data
    return _settings()
# vim:set et sts=4 ts=4 tw=80:
