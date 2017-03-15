# -*- coding: utf-8 -*-
'''

.. _module_mc_mvn:

mc_mvn / mvn registry
============================================

'''
# Import python libs
import logging
import mc_states.api
from salt.utils.odict import OrderedDict

__name = 'mvn'
PREFIX = 'makina-states.localsettings.{0}'.format(__name)
log = logging.getLogger(__name__)


def settings():
    '''
    mvn

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        locations = __salt__['mc_locations.settings']()
        data = __salt__['mc_utils.defaults'](
            PREFIX, {
                'url':
                'http://www.trieuvan.com/apache/maven/'
                'maven-{version[0]}/'
                '{version}/binaries/'
                'apache-maven-{version}-bin.tar.gz',
                'shas': OrderedDict([
                    ('3.3.3', 'md5=794b3b7961200c542a7292682d21ba36'),
                ]),
                'version': '3.3.3',
                'versions': ['{version}'],
                'location': locations['apps_dir']+'/mvn'})
        return data
    return _settings()
