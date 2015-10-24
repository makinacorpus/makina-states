# -*- coding: utf-8 -*-
'''
.. _module_mc_pureftpd:

mc_pureftpd / pureftpd functions
============================================



'''

# Import python libs
import logging
import mc_states.api

__name = 'pureftpd'

log = logging.getLogger(__name__)


def settings():
    '''
    pureftpd settings

    Daemon lauch parameters (makina-states.services.ftp.pureftpdefaults)
        Virtualchroot
            TDB
        InetdMode
            TDB
        UploadUid
            TDB
        UploadGid
            TDB
        UploadScript
            TDB

    Pureftp configuration (makina-states.services.ftp.pureftp)
        AllowAnonymousFXP
            TDB
        AllowDotFiles
            TDB
        AllowUserFXP
            TDB
        AltLog
            TDB
        AnonymousBandwidth
            TDB
        AnonymousCanCreateDirs
            TDB
        AnonymousCantUpload
            TDB
        AnonymousOnly
            TDB
        AnonymousRatio
            TDB
        AntiWarez
            TDB
        AutoRename
            TDB
        Bind
            TDB
        BrokenClientsCompatibility
            TDB
        CallUploadScript
            TDB
        ChrootEveryone
            TDB
        ClientCharset
            TDB
        Daemonize
            TDB
        DisplayDotFiles
            TDB
        DontResolve
            TDB
        FSCharset
            TDB
        IPV4Only
            TDB
        IPV6Only
            TDB
        KeepAllFiles
            TDB
        LimitRecursion
            TDB
        LogPID
            TDB
        MaxClientsNumber
            TDB
        MaxClientsPerIP
            TDB
        MaxDiskUsage
            TDB
        MinUID
            TDB
        NATmode
            TDB
        NoAnonymous
            TDB
        NoChmod
            TDB
        NoRename
            TDB
        NoTruncate
            TDB
        Quota
            TDB
        SyslogFacility
            TDB
        TLS
            TDB
        TrustedGID
            TDB
        TrustedIP
            TDB
        Umask
            TDB
        UserBandwidth
            TDB
        UserRatio
            TDB
        VerboseLog
            TDB
        PassiveIP
            TDB
        PassivePortRange
            TDB
        PAMAuthentication
            TDB
        UnixAuthentication
            TDB
        PureDB
            TDB
        MySQLConfigFile
            TDB
        ExtAuth
            TDB
        LDAPConfigFile
            TDB
        PGSQLConfigFile
            TDB
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        data = {
            'defaults': __salt__['mc_utils.defaults'](
                'makina-states.services.ftp.pureftpd.defaults', {
                    'Virtualchroot': 'false',
                    'InetdMode': 'standalone',
                    'UploadUid': '',
                    'UploadGid': '',
                    'UploadScript': '',
                    'configs': {
                        '/etc/init.d/pure-ftpd': {},
                    },
                }
            ),
            'conf': __salt__['mc_utils.defaults'](
                'makina-states.services.ftp.pureftp', {
                    'AllowAnonymousFXP': 'no',
                    'AllowDotFiles': '',
                    'AllowUserFXP': '',
                    'AltLog': 'clf:/var/log/pure-ftpd/transfer.log',
                    'AnonymousBandwidth': '',
                    'AnonymousCanCreateDirs': 'no',
                    'AnonymousCantUpload': 'yes',
                    'AnonymousOnly': '',
                    'AnonymousRatio': '',
                    'AntiWarez': '',
                    'AutoRename': '',
                    'Bind': '',
                    'BrokenClientsCompatibility': 'yes',
                    'CallUploadScript': '',
                    'ChrootEveryone': 'yes',
                    'ClientCharset': '',
                    'Daemonize': "",
                    'DisplayDotFiles': "yes",
                    'DontResolve': "yes",
                    'FSCharset': 'utf-8',
                    'IPV4Only': "yes",
                    'IPV6Only': "",
                    'KeepAllFiles': "no",
                    'LimitRecursion': "5000 500",
                    'LogPID': "",
                    'MaxClientsNumber': "",
                    'MaxClientsPerIP': "",
                    'MaxDiskUsage': "90",
                    'MinUID': '1000',
                    'NATmode': "",
                    'NoAnonymous': 'yes',
                    'NoChmod': "",
                    'NoRename': "",
                    'NoTruncate': "",
                    'Quota': "",
                    'SyslogFacility': "",
                    'TLS': "1",
                    'TrustedGID': "",
                    'TrustedIP': "",
                    'Umask': "133 022",
                    'UserBandwidth': "",
                    'UserRatio': "",
                    'VerboseLog': "yes",

                    'PassiveIP': "",
                    'PassivePortRange': "",

                    'PAMAuthentication': 'yes',
                    'UnixAuthentication': 'no',
                    'PureDB': '/etc/pure-ftpd/pureftpd.pdb',
                    'MySQLConfigFile': "",
                    'ExtAuth': "",
                    'LDAPConfigFile': "",
                    'PGSQLConfigFile': "",
                }
            )
        }
        for setting in data['conf']:
            value = data['conf'][setting]
            if value.strip():
                data['conf'].update({setting: value + '\n'})
        return data
    return _settings()
