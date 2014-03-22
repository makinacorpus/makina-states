#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
'''
.. _module_mc_cloud_saltify:

mc_cloud_controller / cloud related variables
==============================================

- This contains generate settings around cloud_saltify
- This contains also all targets to be driven using the saltify driver
- LXC driver profile and containers settings are in :ref:`module_mc_lxc`.

'''
# Import salt libs
import mc_states.utils

__name = 'cloud_saltify'


def gen_id(name):
    return name.replace('.', '-')


def settings():
    """
          targets
            Target where to bootstrap salt using the saltify cloud_saltify driver


            ::

                'salty_targets': {
                    #'id': {
                    #    'name': 'germaine.tld',
                    #    'ssh_host': 'ip_or_dns',
                    #    'profile': 'salt-minion',
                    #    'ssh_username': 'foo',
                    #    'password': 'password',
                    #    'sudo_password': 'sudo_password',
                    #    'sudo': True,
                    #}
    """
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        localsettings = __salt__['mc_localsettings.settings']()
        pillar = __pillar__
        cloudSettings = __salt__['mc_saltcloud.settings']()
        sdata = __salt__['mc_utils.defaults'](
            'makina-states.services.cloud.saltify', {
                'mode': cloudSettings['mode'],
                'master': cloudSettings['master'],
                'master_port': cloudSettings['master_port'],
                'bootsalt_branch': cloudSettings['bootsalt_branch'],
                'targets': {}
            }
        )
        for t in [a for a in sdata['targets']]:
            c_data = sdata['targets'][t]
            c_data['name'] = c_data.get('name', t)
            c_data['ssh_host'] = c_data.get('ssh_host', c_data['name'])
            c_data['profile'] = 'ms-salt-minion'
            c_data.setdefault('mode', sdata['mode'])
            if 'mastersalt' in c_data['mode']:
                default_args = sdata['bootsalt_mastersalt_args']
            else:
                default_args = sdata['bootsalt_args']
            c_data['keep_tmp'] = c_data.get('keep_tmp', False)
            c_data['script_args'] = c_data.get('script_args', default_args)
            branch = c_data.get('bootsalt_branch', sdata['bootsalt_branch'])
            if (
                not '-b' in c_data['script_args']
                or not '--branch' in c_data['script_args']
            ):
                c_data['script_args'] += ' -b {0}'.format(branch)
            for k in ['master',
                      'bootsalt_branch',
                      'master_port']:
                c_data[k] = c_data.get(k, sdata[k])
                c_data.setdefault(k, sdata.get(k, None))
        return sdata
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

# 

# vim:set et sts=4 ts=4 tw=80:
