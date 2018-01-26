# -*- coding: utf-8 -*-
'''
.. _module_mc_autoupgrade:

mc_autoupgrade / packages autoupgrade
============================================



'''
# Import python libs
import logging
import mc_states.api

__name = 'autoupgrade'

log = logging.getLogger(__name__)


def settings():
    '''
    autoupgrade registry

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        _g = __grains__
        origins = []
        if _g['os'] in ['Debian']:
            origins.append("Debian:stable")
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
                    'blacklist': [],
                    'origins': origins,
                }
            }
        )
        return data
    return _settings()
