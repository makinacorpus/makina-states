# -*- coding: utf-8 -*-
'''
Management of Nginx, Makina Corpus version
============================================

If you alter this module and want to test it, do not forget to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_nginx

'''

# Import python libs
import logging
import mc_states.utils

__name = 'nginx'

log = logging.getLogger(__name__)



def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings(REG):
        '''
        This is called from mc_services, loading all Nginx default settings

        :!Settings are merged with grains and pillar via mc_utils.defaults
        '''
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locations = localsettings['locations']

        nginxData = __salt__['mc_utils.defaults'](
            'makina-states.services.http.nginx',
            __salt__['grains.filter_by']({
                'Debian': {
                    'package': 'nginx',
                    'service': 'nginx',
                    'basedir': locations['conf_dir'] + '/nginx',
                    'vhostdir': (
                        locations['conf_dir'] + '/nginx/sites-available'),
                    'confdir': locations['conf_dir'] + '/nginx/conf.d',
                    'logdir': locations['var_log_dir'] + '/nginx',
                    'wwwdir': locations['srv_dir'] + '/www'
                },
            },
                merge=__salt__['grains.filter_by']({
                    'dev': {
                    },
                    'prod': {
                    },
                },
                    merge={
                        'virtualhosts': {}
                    },
                    grain='default_env',
                    default='dev'
                ),
                grain='os_family',
                default='Debian',
            )
        )
        return nginxData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
