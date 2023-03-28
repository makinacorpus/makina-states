# -*- coding: utf-8 -*-
'''

.. _module_mc_ubuntugis:

mc_ubuntugis / ubuntugis registry
============================================



If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_ubuntugis

'''
# Import python libs
import logging
import copy
import mc_states.api

__name = 'ubuntugis'
PREFIX = 'makina-states.services.gis.{0}'.format(__name)
log = logging.getLogger(__name__)


def settings():
    '''
    ubuntugis registry

    ppa
      use the unstable, testing  or stable ppa


    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _g = __grains__
        pkgssettings = __salt__['mc_pkgs.settings']()
        if _g['os'] in ['Debian']:
            dist = pkgssettings['ubuntu_lts']
        else:
            dist = pkgssettings['udist']
        ppa = 'stable'
        if _g['os'] == 'Ubuntu' and _g['osrelease'] >= '14.04':
            ppa = 'unstable'
        data = __salt__['mc_utils.defaults'](
            PREFIX, {
                'pkgs': ['libgeos-dev'],
                'dist': dist,
                'ppa': ppa,
                'ubuntu_ppa': None})
        if not data['ubuntu_ppa']:
            data['ubuntu_ppa'] = {
                'stable': 'ppa'
            }.get(data['ppa'], 'ubuntugis-{0}'.format(data['ppa']))
        return data
    return _settings()
