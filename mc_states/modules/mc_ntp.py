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

        servers
           server entries without the fudge headers
        fudge
            fudge entries without the fudge headers

        default_all
            allow query from ext (firewalled in ms)
        block_ext
            block all outbound queryies

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        ntpData = __salt__['mc_utils.defaults'](
            'makina-states.services.base.ntp', {
                'servers': [
                    '0.ubuntu.pool.ntp.org',
                    '1.ubuntu.pool.ntp.org',
                    '2.ubuntu.pool.ntp.org',
                    '3.ubuntu.pool.ntp.org',
                    'ntp.ubuntu.com',
                    '127.127.1.0',
                ],
                'fudge': [
                    '127.127.1.0 stratum 11',
                ],
                'default_all': True,
                'block_ext': False,
            }
        )
        return ntpData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
