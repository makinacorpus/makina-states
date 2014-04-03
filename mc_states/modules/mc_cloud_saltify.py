# -*- coding: utf-8 -*-
'''
.. _module_mc_cloud_saltify:

mc_cloud_saltify / cloud related variables
==============================================

- This contains generate settings around cloud_saltify
- This contains also all targets to be driven using the saltify driver
- LXC driver profile and containers settings are in :ref:`module_mc_lxc`.

'''
__docformat__ = 'restructuredtext en'
# Import salt libs
import mc_states.utils
from pprint import pformat
from salt.utils.odict import OrderedDict
from mc_states import saltapi

__name = 'cloud_saltify'


def gen_id(name):
    return name.replace('.', '-')


def settings():
    """
    Except targets, we take all the default from
    :ref:`module_mc_cloud`

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
        List of minionid Targets where to bootstrap salt using the saltcloud
        saltify driver (something accessible via ssh)
    """
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        cloudSettings = __salt__['mc_cloud.settings']()
        sdata = __salt__['mc_utils.defaults'](
            'makina-states.cloud.saltify', {
                'bootsalt_args': cloudSettings['bootsalt_args'],
                'bootsalt_mastersalt_args': (
                    cloudSettings['bootsalt_mastersalt_args']),
                'ssh_gateway': cloudSettings['ssh_gateway'],
                'ssh_gateway_password': cloudSettings['ssh_gateway_password'],
                'ssh_gateway_user': cloudSettings['ssh_gateway_user'],
                'ssh_username': 'root',
                'ssh_keyfile': None,
                'ssh_gateway_key': cloudSettings['ssh_gateway_key'],
                'ssh_gateway_port': cloudSettings['ssh_gateway_port'],
                'mode': cloudSettings['mode'],
                'master': cloudSettings['master'],
                'no_sudo_password': False,
                'master_port': cloudSettings['master_port'],
                'bootsalt_branch': cloudSettings['bootsalt_branch'],
                'targets': {},
            }
        )
        # empty the targets information dict to not explode RAM cache.
        # we just keep the target to saltify
        # please use the get_settings_for_target method
        # to grab specific per vm saltify settings
        targets = []
        for k in [l for l in sdata['targets']]:
            targets.append(k)
        targets.sort()
        sdata['targets'] = OrderedDict([(a, {}) for a in targets])
        return sdata
    return _settings()


def settings_for_target(name):
    '''Settings for bootstrapping a target using saltcloud saltify
    driver (something accessible via ssh)
    mappings in the form:

        id
            fqdn/minionid of the host to saltify
        ssh_gateway
            (all the gw params are opt.)
            ssh gateway info
        ssh_gateway_port
            ssh gateway info
        ssh_gateway_user
            ssh gateway info
        ssh_gateway_key
            ssh gateway info
        ssh_gateway_password
            ssh gateway password
        name
            name of the host if it does not match id
            (do not use...)
        ip
            eventual ip if dns is not yet accessible
        mode
            mastersalt or salt, keep at any price mastersalt
            or your are on your own
        ssh_username
            user name to connect as to provision the box
        password
            password to use (leave empty for key)
        no_sudo_password
            disable sudo password handling (default: False).
            If the guest system disable sudo password asking, set this
            parameter to true
        sudo_password
            sudo_password (leave empty to default to password)
        sudo
            do we use sudo (bool)
        ssh_keyfile
            use the ssh key (private) instead of using password base
            authentication
    '''
    sdata = settings()
    conf_key = 'makina-states.cloud.saltify.targets.{0}'.format(name)
    try:
        c_data = __salt__['mc_utils.defaults'](conf_key, {})
        if not c_data:
            raise KeyError('empty')
    except KeyError:
        raise KeyError(
            '{0} is not to be saltified'.format(name))
    c_data['name'] = c_data.get('name', name)
    c_data['ssh_host'] = c_data.get('ip', c_data['name'])
    c_data['profile'] = 'ms-salt-minion'
    c_data.setdefault('mode', sdata['mode'])
    default_args = {
        'mastersalt': sdata['bootsalt_mastersalt_args']
    }.get(c_data['mode'], sdata['bootsalt_args'])
    c_data['keep_tmp'] = c_data.get('keep_tmp', False)
    c_data['script_args'] = c_data.get('script_args', default_args)
    branch = c_data.get('bootsalt_branch', sdata['bootsalt_branch'])

    c_data = saltapi.complete_gateway(c_data, sdata)
    if (
        '-b' not in c_data['script_args']
        or '--branch' not in c_data['script_args']
    ):
        c_data['script_args'] += ' -b {0}'.format(branch)
    for k in ['master',
              'gateway',
              'ssh_keyfile',
              'password',
              'ssh_username',
              'bootsalt_branch',
              'master_port']:
        c_data.setdefault(k, sdata.get(k, None))
    if not c_data['ssh_keyfile'] and not c_data['password']:
        raise ValueError('We should have one of have sshkey + '
                         'password for \n{0}'.format(pformat(c_data)))
    if c_data['ssh_keyfile'] and c_data['password']:
        raise ValueError('Not possible to have sshkey + password '
                         'for \n{0}'.format(pformat(c_data)))
    sudo_password = c_data.get('sudo_password', '')
    if not sudo_password:
        sudo_password = c_data['password']
    if c_data.get('no_sudo_password', sdata['no_sudo_password']):
        sudo_password = None
    c_data['sudo_password'] = sudo_password
    return c_data


def dump():
    return mc_states.utils.dump(__salt__, __name)

# vim:set et sts=4 ts=4 tw=80:
