# -*- coding: utf-8 -*-
'''
Management of Nginx, Makina Corpus version
============================================

If you alter this module and want to test it, do not forget to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_lxc

'''

# Import python libs
import logging
import mc_states.utils

from salt.utils.odict import OrderedDict

__name = 'lxc'

log = logging.getLogger(__name__)



def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        '''
        This is called from mc_services, loading all Nginx default settings

        :!Settings are merged with grains and pillar via mc_utils.defaults
        '''
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locations = localsettings['locations']
        lxcSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.http.lxc',
            __salt__['grains.filter_by']({
                'Debian': {},
            },
                merge=__salt__['grains.filter_by']({
                    'dev': {
                    },
                    'prod': {
                    },
                },
                    merge={
                    },
                    grain='default_env',
                    default='dev'
                ),
                grain='os_family',
                default='Debian',
            )
        )
        lxcSettings['containers'] = OrderedDict()
        # server-def is retro compat
        sufs = ['-lxc-server-def', '-lxc-container-def']

        for suf in sufs:
            for k, lxc_data in pillar.items():
                if k.endswith(suf):
                    lxc_data = lxc_data.copy()
                    lxc_name = lxc_data.get('name', k.split(suf)[0])
                    lxcSettings['containers'][lxc_name] = lxc_data
                    lxc_data.setdefault('template', 'ubuntu')
                    lxc_data.setdefault('netmask', '255.255.255.0')
                    lxc_data.setdefault('gateway', '10.0.3.1')
                    lxc_data.setdefault('dnsservers', '10.0.3.1')
                    lxc_root = lxc_data.setdefault(
                        'root',
                        locations['var_lib_dir'] + '/lxc/' + lxc_name)
                    lxc_data.setdefault('rootfs', lxc_root + '/rootfs')
                    lxc_data.setdefault('config', lxc_root + '/config')
                     # raise key error if undefined
                    lxc_data.setdefault('mac', lxc_data['mac'])
                    lxc_data.setdefault('ip4', lxc_data['ip4'])
        return lxcSettings
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
