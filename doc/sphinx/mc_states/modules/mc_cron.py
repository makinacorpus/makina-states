# -*- coding: utf-8 -*-
'''

.. _module_mc_cron:

mc_cron / cron functions
============================================



'''

# Import python libs
import logging
import copy
import mc_states.api
from salt.utils.odict import OrderedDict


__name = 'cron'
six = mc_states.api.six
PREFIX = 'makina-states.services.base.{0}'.format(__name)
logger = logging.getLogger(__name__)


def settings():
    '''
    cron settings
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        DEFAULTS = {
            'is_container': __salt__['mc_nodetypes.is_container'](),
            'packages': ['cron'],
            'extra_confs': {
            }}

        #if (
        #    __grains__.get('os') == 'Ubuntu' and
        #    __grains__.get('osrelease', '') <= '15.04'
        #):
        #    DEFAULTS['extra_confs'].update(
        #        {
        #            '/etc/init/cron.conf': {'mode': '644'}
        #        })
        data = _s['mc_utils.defaults'](PREFIX, DEFAULTS)
        return data
    return _settings()
