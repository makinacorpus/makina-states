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
import mc_states.utils

__name = 'java'

log = logging.getLogger(__name__)


def settings():
    '''
    java registry

    default_jdk_ver
        default JDK version
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        data = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.jdk', {
                'default_jdk_ver': 7,
            })
        # retrocompat
        data['jdkDefaultVer'] = data['default_jdk_ver']
        return data
    return _settings()



#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
