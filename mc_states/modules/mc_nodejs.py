# -*- coding: utf-8 -*-
'''

.. _module_mc_nodejs:

mc_nodejs / nodejs/npm registry
============================================

'''
# Import python libs
import logging
import mc_states.utils

__name = 'nodejs'

log = logging.getLogger(__name__)


def settings():
    '''
    nodejs

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        # nodejs
        cur_nodejsver = '0.10.26'
        url = 'http://nodejs.org/dist/v{ver}/node-v{ver}-linux-{arch}.tar.gz'
        nodejsData = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.nodejs', {
                'url': url,
                'shas': {
                    'node-v0.10.26-linux-x86.tar.gz': 'b3bebee7f256644266fccce04f54e2825eccbfc0',
                    'node-v0.10.26-linux-x64.tar.gz': 'd15d39e119bdcf75c6fc222f51ff0630b2611160',
                },
                'versions': [cur_nodejsver],
                'version': cur_nodejsver,
                'arch': __grains__['cpuarch'].replace('x86_64', 'x64'),
                'location': locations['apps_dir']+'/node',
                'packages': {
                    'system': [],
                     cur_nodejsver: [],
                },
            }
        )
        return nodejsData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
