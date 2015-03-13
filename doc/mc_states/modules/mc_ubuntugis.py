# -*- coding: utf-8 -*-
'''

.. _module_mc_ubuntugis:

mc_ubuntugis / ubuntugis registry
============================================



If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_ubuntugis

'''
# Import python libs
import logging
import copy
import mc_states.utils

__name = 'ubuntugis'

log = logging.getLogger(__name__)


def settings():
    '''
    ubuntugis registry

    ppa
      use the unstable or stable ppa


    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        ubuntugisData = __salt__['mc_utils.defaults'](
            'makina-states.services.gis.ubuntugis', {
              'ppa': 'stable',
            }
        )
        return ubuntugisData
    return _settings()



#
