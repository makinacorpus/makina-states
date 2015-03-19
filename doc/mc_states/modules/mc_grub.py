# -*- coding: utf-8 -*-
'''

.. _module_mc_grub:

mc_grub / grub registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_grub

'''
# Import python libs
import logging
import copy
import mc_states.api
from salt.utils.pycrypto import secure_password

__name = 'grub'

log = logging.getLogger(__name__)


def settings():
    '''
    grub registry

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        grubData = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.grub', {
            }
        )
        return grubData
    return _settings()



#
