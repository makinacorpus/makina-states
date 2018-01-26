# -*- coding: utf-8 -*-
'''

.. _module_mc_casperjs:

mc_casperjs / casperjs/npm registry
============================================



'''
# Import python libs
import logging
import mc_states.api

__name = 'casperjs'

log = logging.getLogger(__name__)


def settings():
    '''
    casperjs

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        # casperjs
        cur_casperjsver = '1.1-beta3'
        casperjsData = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.casperjs', {
                'url': (
                    'https://github.com/n1k0/casperjs/archive/{0}.tar.gz'
                ),
                'shas': {
                    '1.1-beta3.tar.gz':  (
                        '552db60dbdedd185f1bd6bc83ab2c816'),
                    '1.1-beta3':  (
                        '4a4858917a2ef4f8274ae86032694568'),
                },
                'versions': [cur_casperjsver],
                'version': cur_casperjsver,
                'arch': 'x86_64',
                'location': locations['apps_dir']+'/casperjs',
                'bn': "casperjs-{0}-linux-{1}",
            }
        )
        return casperjsData
    return _settings()



#
