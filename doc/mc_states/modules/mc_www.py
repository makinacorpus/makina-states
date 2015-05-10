#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_www:

mc_www / www registry
============================================



If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_www

'''
# Import python libs
import logging
import mc_states.api

__name = 'www'

log = logging.getLogger(__name__)


def settings():
    '''
    www registry

    fastcgi_socket_directory
        fastcgi socket directory
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        wwwData = __salt__['mc_utils.defaults'](
            'makina-states.services.http.www', {
                'doc_root': '/var/www/default',
                'serveradmin_mail': 'webmaster@localhost',
                'socket_directory': '/var/spool/www',
                'upload_max_filesize': '25000000M',
            })
        return wwwData
    return _settings()



# vim:set et sts=4 ts=4 tw=80:
