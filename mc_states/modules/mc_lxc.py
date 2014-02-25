# -*- coding: utf-8 -*-
'''

.. _module_mc_lxc:

mc_lxc / lxc registry
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


def is_lxc():
    """
    in case of a container, we have the container name in cgroups
    else, it is equal to /

    in lxc:
        ['11:name=systemd:/user/1000.user/1.session',
        '10:hugetlb:/thisname',
        '9:perf_event:/thisname',
        '8:blkio:/thisname',
        '7:freezer:/thisname',
        '6:devices:/thisname',
        '5:memory:/thisname',
        '4:cpuacct:/thisname',
        '3:cpu:/thisname',
        '2:cpuset:/thisname']

    in host:
        ['11:name=systemd:/',
        '10:hugetlb:/',
        '9:perf_event:/',
        '8:blkio:/',
        '7:freezer:/',
        '6:devices:/',
        '5:memory:/',
        '4:cpuacct:/',
        '3:cpu:/',
        '2:cpuset:/']
    """

    try:
        cgroups = open('/proc/1/cgroup').read().splitlines()
        lxc = not '/' == [a.split(':')[-1]
                          for a in cgroups if ':cpu:' in a][-1]
    except Exception:
        lxc = False
    return lxc


def settings():
    '''Lxc registry

    containers
        Mapping of containers defintions
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        locations = localsettings['locations']
        lxcSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.http.lxc', {
                'is_lxc': is_lxc(),
            }
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

def create(vm_):
    if config.get_cloud_config_value('deploy', vm_, __opts__) is False:
        return {
            'Error': {
                'No Deploy': '\'deploy\' is not enabled. Not deploying.'
            }
        }
    key_filename = config.get_cloud_config_value(
        'key_filename', vm_, __opts__, search_global=False, default=None
    )
    if key_filename is not None and not os.path.isfile(key_filename):
        raise SaltCloudConfigError(
            'The defined ssh_keyfile {0!r} does not exist'.format(
                key_filename
            )
        )

    if key_filename is None and salt.utils.which('sshpass') is None:
        raise SaltCloudSystemExit(
            'Cannot deploy salt in a VM if the \'ssh_keyfile\' setting '
            'is not set and \'sshpass\' binary is not present on the '
            'system for the password.'
        )

    ret = {}

    log.info('Provisioning existing machine {0}'.format(vm_['name']))

    ssh_username = config.get_cloud_config_value('ssh_username', vm_, __opts__)
    deploy_script = script(vm_)
    deploy_kwargs = {
        'host': vm_['ssh_host'],
        'username': ssh_username,
        'script': deploy_script,
        'name': vm_['name'],
        'tmp_dir': config.get_cloud_config_value(
            'tmp_dir', vm_, __opts__, default='/tmp/.saltcloud'
        ),
        'deploy_command': config.get_cloud_config_value(
            'deploy_command', vm_, __opts__,
            default='/tmp/.saltcloud/deploy.sh',
        ),
        'start_action': __opts__['start_action'],
        'parallel': __opts__['parallel'],
        'sock_dir': __opts__['sock_dir'],
        'conf_file': __opts__['conf_file'],
        'minion_pem': vm_['priv_key'],
        'minion_pub': vm_['pub_key'],
        'keep_tmp': __opts__['keep_tmp'],
        'sudo': config.get_cloud_config_value(
            'sudo', vm_, __opts__, default=(ssh_username != 'root')
        ),
        'sudo_password': config.get_cloud_config_value(
            'sudo_password', vm_, __opts__, default=None
        ),
        'tty': config.get_cloud_config_value(
            'tty', vm_, __opts__, default=True
        ),
        'password': config.get_cloud_config_value(
            'password', vm_, __opts__, search_global=False
        ),
        'key_filename': key_filename,
        'script_args': config.get_cloud_config_value('script_args', vm_, __opts__),
        'script_env': config.get_cloud_config_value('script_env', vm_, __opts__),
        'minion_conf': salt.utils.cloud.minion_config(__opts__, vm_),
        'preseed_minion_keys': vm_.get('preseed_minion_keys', None),
        'display_ssh_output': config.get_cloud_config_value(
            'display_ssh_output', vm_, __opts__, default=True
        )
    }

    # Deploy salt-master files, if necessary
    if config.get_cloud_config_value('make_master', vm_, __opts__) is True:
        deploy_kwargs['make_master'] = True
        deploy_kwargs['master_pub'] = vm_['master_pub']
        deploy_kwargs['master_pem'] = vm_['master_pem']
        master_conf = salt.utils.cloud.master_config(__opts__, vm_)
        deploy_kwargs['master_conf'] = master_conf

        if master_conf.get('syndic_master', None):
            deploy_kwargs['make_syndic'] = True

    deploy_kwargs['make_minion'] = config.get_cloud_config_value(
        'make_minion', vm_, __opts__, default=True
    )

    win_installer = config.get_cloud_config_value('win_installer', vm_, __opts__)
    if win_installer:
        deploy_kwargs['win_installer'] = win_installer
        minion = salt.utils.cloud.minion_config(__opts__, vm_)
        deploy_kwargs['master'] = minion['master']
        deploy_kwargs['username'] = config.get_cloud_config_value(
            'win_username', vm_, __opts__, default='Administrator'
        )
        deploy_kwargs['password'] = config.get_cloud_config_value(
            'win_password', vm_, __opts__, default=''
        )

    # Store what was used to the deploy the VM
    event_kwargs = copy.deepcopy(deploy_kwargs)
    del event_kwargs['minion_pem']
    del event_kwargs['minion_pub']
    del event_kwargs['sudo_password']
    if 'password' in event_kwargs:
        del event_kwargs['password']
    ret['deploy_kwargs'] = event_kwargs

    salt.utils.cloud.fire_event(
        'event',
        'executing deploy script',
        'salt/cloud/{0}/deploying'.format(vm_['name']),
        {'kwargs': event_kwargs},
    )

    deployed = False
    if win_installer:
        deployed = salt.utils.cloud.deploy_windows(**deploy_kwargs)
    else:
        deployed = salt.utils.cloud.deploy_script(**deploy_kwargs)

    if deployed:
        ret['deployed'] = deployed
        log.info('Salt installed on {0}'.format(vm_['name']))
        return ret

    log.error('Failed to start Salt on host {0}'.format(vm_['name']))
    return {
        'Error': {
            'Not Deployed': 'Failed to start Salt on host {0}'.format(
                vm_['name']
            )
        }
    }
        






















#
