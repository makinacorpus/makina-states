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
    Except targets, we take all the default from
    :ref:`module_mc_cloud_controller`

    bootsalt_args
        args to give to bootsalt
        (default to cloudcontroller configured value)
    bootsalt_mastersalt_args
        args to give to bootsalt
        (default to cloudcontroller configured value)
    mode
        salt mode (salt/mastersalt)
        (default to cloudcontroller configured value)
    master
        salt master fqdn to rattach to
        (default to cloudcontroller configured value)
    master_port
        salt master port to rattach to
        (default to cloudcontroller configured value)
    bootsalt_branch
        default bootsalt_branch to use
        (default to cloudcontroller configured value)

    targets
        Targets where to bootstrap salt using the saltcloud saltify
        driver (something accessible via ssh)
        mappings in the form:

        id:
            id (fqdn) of the host to saltify

            ssh_gateway (all the gw params are opt.)
                ssh gateway info
            ssh_gateway_port
                ssh gateway info
            ssh_gateway_user
                ssh gateway info
            ssh_gateway_key
                ssh gateway info
            name
                name of the host if it does not match id
                (do not use...)
            ssh_host 'ip_or_dns', (
            mode
                'mastersalt',
            ssh_username
                foo',
            password
                password',
            sudo_password
                sudo_password', (
            sudo
                do we use sudo (bool)
          }
    """
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        pillar = __pillar__
        cloudSettings = __salt__['mc_cloud_controller.settings']()
        sdata = __salt__['mc_utils.defaults'](
            'makina-states.cloud.saltify', {
                'bootsalt_args': cloudSettings['bootsalt_args'],
                'bootsalt_mastersalt_args': (
                    cloudSettings['bootsalt_mastersalt_args']),
                'ssh_gateway': cloudSettings['ssh_gateway'],
                'ssh_gateway_user': cloudSettings['ssh_gateway_user'],
                'ssh_gateway_key': cloudSettings['ssh_gateway_key'],
                'ssh_gateway_port': cloudSettings['ssh_gateway_port'],
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
            c_data['ssh_host'] = c_data['name']
            c_data['profile'] = 'ms-salt-minion'
            c_data.setdefault('mode', sdata['mode'])
            default_args = {
                'mastersalt': sdata['bootsalt_mastersalt_args']
            }.get(c_data['mode'], sdata['bootsalt_args'])
            c_data['keep_tmp'] = c_data.get('keep_tmp', False)
            c_data['script_args'] = c_data.get('script_args', default_args)
            branch = c_data.get('bootsalt_branch', sdata['bootsalt_branch'])
            c_data.setdefault('gateway', {})
            gw = c_data.get('ssh_gateway', sdata['ssh_gateway'])
            if gw:
                for k in [
                    'ssh_gateway', 'ssh_gateway_user',
                    'ssh_gateway_key', 'ssh_gateway_port',
                ]:
                    c_data['gateway'].setdefault(
                        k, c_data.get(k, sdata.get(k, None)))
            if (
                not '-b' in c_data['script_args']
                or not '--branch' in c_data['script_args']
            ):
                c_data['script_args'] += ' -b {0}'.format(branch)
            for k in ['master',
                      'bootsalt_branch',
                      'master_port']:
                c_data.setdefault(k, sdata.get(k, None))
        return sdata
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

# vim:set et sts=4 ts=4 tw=80:
