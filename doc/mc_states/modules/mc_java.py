#!/usr/bin/java python
# -*- coding: utf-8 -*-
'''

.. _module_mc_java:

mc_java / java registry
============================================




If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_java

'''
# Import python libs
import logging
import mc_states.api

__name = 'java'

log = logging.getLogger(__name__)


def settings():
    '''
    java registry

    default_jdk_ver
        default JDK version
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        data = _s['mc_utils.defaults'](
            'makina-states.localsettings.jdk', {
                'default_jdk_ver': 7,
                'installed': [],
            })
        if data['default_jdk_ver'] not in data['installed']:
            data['installed'].append(data['default_jdk_ver'])
        # retrocompat
        data['jdkDefaultVer'] = data['default_jdk_ver']
        return data
    return _settings()
# vim:set et sts=4 ts=4 tw=80:
