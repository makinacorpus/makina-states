# -*- coding: utf-8 -*-
'''

.. _module_mc_dbus:

mc_dbus / dbus functions
============================================



'''

# Import python libs
import logging
import copy
import mc_states.api
from salt.utils.odict import OrderedDict


__name = 'dbus'
six = mc_states.api.six
PREFIX = 'makina-states.services.base.{0}'.format(__name)
logger = logging.getLogger(__name__)


def settings():
    '''
    dbus settings
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        DEFAULTS = {
            'is_container': __salt__['mc_nodetypes.is_container'](),
            'packages': ['dbus'],
            'extra_confs': {
                # '/etc/default/dbus': {},
                # '/etc/dbus.json': {'mode': '644'},
                # '/etc/init.d/dbus': {'mode': '755'},
                # '/etc/systemd/system/dbus.service': {'mode': '644'},
                # '/usr/bin/ms_dbus.py': {'mode': '755'}
            }}
        data = _s['mc_utils.defaults'](PREFIX, DEFAULTS)
        return data
    return _settings()
