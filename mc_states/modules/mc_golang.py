# -*- coding: utf-8 -*-
'''

.. _module_mc_golang:

mc_golang / golang registry
============================================


If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_golang

'''
# Import python libs
import logging
import copy
import mc_states.api

__name = 'golang'
PREFIX = 'makina-states.localsettings.{0}'.format(__name)
log = logging.getLogger(__name__)


def settings():
    '''
    golang registry

    ppa
      use the unstable, testing  or stable ppa


    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s, _g = __salt__, __grains__
        data = _s['mc_utils.defaults'](
            PREFIX, {
                'ppa': 'http://ppa.launchpad.net/gophers/archive/ubuntu',
                'dist': _g['oscodename'],
                'packages': [],
                'versions': ['1.7']
            })
        for v in data['versions']:
            p = 'golang-{0}'.format(v)
            if p in data['packages']:
                continue
            data['packages'].append(p)
        return data
    return _settings()
