#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_screen:

mc_screen / screen registry
============================================



If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_screen

'''
# Import python libs
import logging
import mc_states.api

__name = 'screen'

log = logging.getLogger(__name__)
RVM_URL = (
    'https://raw.github.com/wayneeseguin/screen/master/binscripts/screen-installer')


def settings():
    '''
    screen registry

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        locations = __salt__['mc_locations.settings']()
        data = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.screen', {
              'defscrollback': '30000',
              'vbell_msg': '"bell on %t (%n)"',
              'confs': {
                '/etc/screenrc': None
              },
              'hardstatus' : [ 
                   "on",
                   "alwayslastline",
                   "string '%{gk}[ %{G}%H %{g}][%= "
                   "%{wk}%?%-Lw%?%{=b kR}(%{W}%n*%f "
                   "%t%?(%u)%?%{=b kR})%{= "
                   "kw}%?%+Lw%?%?%= %{g}][%{Y}%l%{g}]%{=b C}[ "
                   "%m/%d %c ]%{W}'"],
            })
        return data
    return _settings()



#
# -*- coding: utf-8 -*-

# screen:set et sts=4 ts=4 tw=80:
