# -*- coding: utf-8 -*-
'''

.. _module_mc_virtualbox:

mc_virtualbox / virtualbox
============================================

'''
# Import python libs
import logging
import mc_states.api
from salt.utils.odict import OrderedDict

__name = 'virtualbox'
PREFIX = 'makina-states.services.virt.{0}'.format(__name)
log = logging.getLogger(__name__)


def settings():
    '''
    virtualbox

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        locations = __salt__['mc_locations.settings']()
        data = __salt__['mc_utils.defaults'](
            PREFIX, {
                'version': '5.0',
                'packages': ['dkms', 'virtualbox-{version}']
            })
        return data
    return _settings()
