# -*- coding: utf-8 -*-
'''

.. _module_mc_ssh:

mc_ssh / OpenSSH  related functions
============================================

'''
# Import salt libs
import mc_states.utils

__name = 'ssh'

def settings():
    '''
    Open ssh registry

    prefixes:
        - makina-states.services.ssh.server

            AuthorizedKeysFile
                List of authorized key filepaths

            ChallengeResponseAuthentication
                do we authorize ChallengeResponseAuthentication

            X11Forwarding
                do we authorize X11Forwarding

            PrintMotd
                do we print motd

            UsePrivilegeSeparation
                UsePrivilegeSeparation mode
            Banner
                path to the banner

            UsePAM
                do we use pam authentication

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
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        pillar = __pillar__
        data = {}
        data['server'] = __salt__['mc_utils.defaults'](
            'makina-states.services.ssh.server', {
                'AuthorizedKeysFile': (
                    '.ssh/authorized_keys .ssh/authorized_keys2'),
                'ChallengeResponseAuthentication': 'no',
                'X11Forwarding': 'yes',
                'PrintMotd': 'no',
                'UsePrivilegeSeparation': 'sandbox',
                'Banner': '/etc/ssh/banner',
                'UsePAM': 'yes',
            })
        data['client'] = __salt__['mc_utils.defaults'](
            'makina-states.services.ssh.client', {
                'StrictHostKeyChecking': 'no',
                'UserKnownHostsFile': '/dev/null',
                'AddressFamily': 'any',
                'ConnectTimeout': 0,
                'SendEnv': "LANG: LC_*",
                'HashKnownHosts': 'yes',
                'GSSAPIAuthentication': 'yes',
                'GSSAPIDelegateCredentials': 'no',
            })
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
