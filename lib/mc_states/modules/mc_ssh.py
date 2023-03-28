# -*- coding: utf-8 -*-
'''

.. _module_mc_ssh:

mc_ssh / OpenSSH  related functions
============================================



'''
# Import salt libs
import mc_states.api

__name = 'ssh'


def settings():
    '''
    Open ssh registry

    prefixes:
        - makina-states.services.ssh.server

            settings.AuthorizedKeysFile
                List of authorized key filepaths

            settings.ChallengeResponseAuthentication
                do we authorize ChallengeResponseAuthentication

            settings.X11Forwarding
                do we authorize X11Forwarding

            settings.PrintMotd
                do we print motd

            settings.UsePrivilegeSeparation
                UsePrivilegeSeparation mode
            settings.Banner
                path to the banner

            settings.UsePAM
                do we use pam authentication

            sshgroup
                named of the allowed group or users allowed
                to connect via ssh

             AllowUsers
                List of users allowed to connect via ssh

             AllowGroups
                List of users allowed to connect via ssh

        - makina-states.services.ssh.client

            StrictHostKeyChecking
                to be documented

            UserKnownHostsFile
                to be documented
            AddressFamily
                to be documented

            ConnectTimeout
                to be documented

            SendEnv
                to be documented

            HashKnownHosts
                to be documented

            GSSAPIAuthentication
                to be documented

            GSSAPIDelegateCredentials
                to be documented

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        pillar = __pillar__
        g = 'sshusers'
        grains = __grains__
        data = __salt__['grains.filter_by']({
            'Debian': {
                'pkg_server': 'openssh-server',
                'pkg_client': 'openssh-client',
                'service': 'ssh',
                'sshd_config': '/etc/ssh/sshd_config',
                #'banner': '/etc/ssh/banner',
            },
            'RedHat': {
                'server': 'openssh-server',
                'client': 'openssh',
                'service': 'sshd',
                'sshd_config': '/etc/ssh/sshd_config',
                #'banner': '/etc/ssh/banner',
            },
        })
        UsePrivilegeSeparation = 'sandbox'
        AuthorizedKeysFile = '.ssh/authorized_keys .ssh/authorized_keys2'
        if grains['os'] in ['Debian']:
            if grains['osrelease'][0] < '6':
                UsePrivilegeSeparation = 'no'
                AuthorizedKeysFile = '.ssh/authorized_keys'
        data.update({
            'extra_confs': {
                '/etc/ssh/sshd_config': {'mode': '640'},
                '/etc/ssh/banner': {'mode': '644'},
                '/usr/bin/sshd_wrapper.sh': {'mode': '755'},
            },
            'server': {
                'allowusers': [],

                'group': g,
                'allowgroups': [
                    'sftponly', 'root', 'sudo', 'wheel', 'admin', 'ubuntu', g],
                'allowusers': ['root', 'sysadmin', 'ubuntu'],
                'settings': {
                    'AuthorizedKeysFile': AuthorizedKeysFile,
                    'ChallengeResponseAuthentication': 'no',
                    'X11Forwarding': 'yes',
                    'PrintMotd': 'no',
                    'UsePrivilegeSeparation': UsePrivilegeSeparation,
                    # 'Banner': '/etc/ssh/banner',
                    'UsePAM': 'yes',
                    'PermitRootLogin': 'without-password',
                    'chroot_sftp': False,
                }
            },
            'custom': '',
            'client': {
                'StrictHostKeyChecking': 'no',
                'UserKnownHostsFile': '/dev/null',
                'AddressFamily': 'any',
                'ConnectTimeout': 0,
                'SendEnv': "LANG: LC_*",
                'HashKnownHosts': 'yes',
                'GSSAPIAuthentication': 'yes',
                'GSSAPIDelegateCredentials': 'no',
            }
        })
        data = __salt__['mc_utils.defaults'](
                'makina-states.services.base.ssh', data)
        if data['server']['allowgroups']:
            data['server']['settings']['AllowGroups'] = ' '.join(data['server']['allowgroups'])
        # those are mutually exclusive !
        elif data['server']['allowusers']:
            data['server']['settings']['AllowUsers'] = ' '.join(data['server']['allowusers'])
        return data
    return _settings()
