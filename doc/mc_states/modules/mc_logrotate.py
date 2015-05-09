#!/usr/bin/logrotate python
# -*- coding: utf-8 -*-
'''

.. _module_mc_logrotate:

mc_logrotate / logrotate registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_logrotate

'''
# Import python libs
import logging
import mc_states.api

__name = 'logrotate'

log = logging.getLogger(__name__)


def settings():
    '''
    logrotate registry

    days
        days rotatation
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.rotate', {
                'days':  '365',
            })
        return data
    return _settings()
# vim:set et sts=4 ts=4 tw=80:
