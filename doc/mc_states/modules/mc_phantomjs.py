# -*- coding: utf-8 -*-
'''

.. _module_mc_phantomjs:

mc_phantomjs / phantomjs/npm registry
============================================

'''
# Import python libs
import logging
import mc_states.api

__name = 'phantomjs'

log = logging.getLogger(__name__)


def settings():
    '''
    phantomjs

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        # phantomjs
        cur_phantomjsver = '1.9.7'
        phantomjsData = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.phantomjs', {
                'archive': "phantomjs-{0}-linux-{1}.tar.bz2",
                'url': (
                    'https://bitbucket.org/ariya/phantomjs/'
                    'downloads/{archive}'),
                'shas': {
                    'phantomjs-1.9.7-linaux-i686.tar.bz2':  (
                        '9c1426eef5b04679d65198b1bdd6ef88'),
                    'phantomjs-1.9.7-linux-x86_64.tar.bz2':  (
                        'f278996c3edd0e8d8ec4893807f27d71'),
                },
                'versions': [cur_phantomjsver],
                'version': cur_phantomjsver,
                'arch': 'x86_64',
                'location': locations['apps_dir']+'/phantomjs',
                'bn': "phantomjs-{0}-linux-{1}",
            }
        )
        return phantomjsData
    return _settings()



#
