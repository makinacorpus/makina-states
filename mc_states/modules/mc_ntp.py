# -*- coding: utf-8 -*-
'''

.. _module_mc_ntp:

mc_ntp / ntp registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_ntp

'''
# Import python libs
import logging
import mc_states.utils

__name = 'ntp'

log = logging.getLogger(__name__)


def settings():
    '''
    ntp
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        ntpData = __salt__['mc_utils.defaults'](
            }
        )
        return ntpData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
