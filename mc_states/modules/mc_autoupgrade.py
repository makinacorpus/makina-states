# -*- coding: utf-8 -*-
'''
.. _module_mc_autoupgrade:

mc_autoupgrade / packages autoupgrade
============================================


'''
# Import python libs
import logging
import mc_states.utils

__name = 'autoupgrade'

log = logging.getLogger(__name__)


def settings():
    '''
    autoupgrade registry

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        origins = []
        if grains['os'] in ['Debian']:
            origins.append(
                "o=Debian,a=stable")
            origins.append(
                "origin=Debian,archive=stable,label=Debian-Security")
        if grains['os'] in ['Ubuntu']:
            origins.append("${distro_id}:${distro_codename}-security")
        data = _s['mc_utils.defaults'](
            'makina-states.localsettings.autoupgrade', {
                'enable': True,
                "unattended": {
                    "activated": "1",
                    "autoclean": "7",
                    "DownloadUpgradeablePackages": "1",
                    "UpdatePackageLists": "1",
                    "mail_on_error": "true",
                    "remove_unused": "false",
                    "mail": "root",
                    "autofix": "true",
                    'blacklist': [
                    ],
                    'origins': origins,
                }
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
