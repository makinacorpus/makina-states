# -*- coding: utf-8 -*-
'''
.. _module_mc_fail2ban:

mc_fail2ban / fail2ban functions
==================================



'''

# Import python libs
import logging
import os
import mc_states.api

__name = 'fail2ban'

log = logging.getLogger(__name__)


def settings():
    '''
    fail2ban settings

    location
        conf dir
    destemail:
        destination mail for alerts(root@fqdn})
    loglevel
        (3)
    logtarget
        (/var/log/fail2ban.log)
    mail_from
        (fail2ban@makina-corpus.com)
    mail_to
        (root)
    mail_enabled
        (false)
    mail_host
        (localhost)
    mail_port
        (25)
    mail_user
        (foo)
    mail_password
        (bar)
    mail_localtime
        (true)
    mail_subject
        ([Fail2Ban] <section>: Banned <ip>)
    mail_message
       (Hi,<br> The IP <ip> has just been banned by Fail2Ban'
        after <failures> attempts against <section>.<br>'
        Regards,<br> Fail2Ban)
    socket
        (/var/run/fail2ban/fail2ban.sock)
    backend
        (polling)
    bantime
       (86400)
    maxretry
       (10)
    ssh_maxretry
       ({maxretry})
    protocol
       (tcp)
    mta
       (sendmail)
    banaction
        (iptables or shorewall if activated)
    ignoreip
        ([127.0.0.1])
    postfix_enabled
       (false)
    wuftpd_enabled
       (false)
    vsftpd_enabled
       (false)
    proftpd_enabled
       (false)
    pureftpd_enabled
       (false)
    ssh_enabled
       (true)
    recidive_enabled
       (false)
    asterisk_tcp_enabled
       (false)
    asterisk_udp_enabled
       (false)
    named_refused_tcp_enabled
       (false)
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        _g = _s['mc_utils.assert_good_grains'](__grains__)
        services_registry = _s['mc_services.registry']()
        banaction = 'iptables'
        if (
            services_registry['has']['firewall.ms_iptables']
        ):
            banaction = 'iptables'
        elif services_registry['has']['firewall.shorewall']:
            shorewall = _s['mc_shorewall.settings']()
            if (
                shorewall['shw_enabled'] and (
                    os.path.exists('/usr/bin/shorewall') or
                    os.path.exists('/sbin/shorewall') or
                    os.path.exists('/usr/sbin/shorewall') or
                    os.path.exists('/usr/bin/shorewall') or
                    os.path.exists('/usr/local/sbin/shorewall') or
                    os.path.exists('/usr/local/bin/shorewall')
                )
            ):
                banaction = 'shorewall'
        elif services_registry['has']['firewall.firewalld']:
            firewalld = _s['mc_firewalld.settings']()
            if (
                not firewalld.get('permissive_mode') and (
                    os.path.exists('/usr/sbin/firewalld') or
                    os.path.exists('/sbin/firewalld') or
                    os.path.exists('/usr/sbin/firewalld') or
                    os.path.exists('/usr/bin/firewalld') or
                    os.path.exists('/usr/local/sbin/firewalld') or
                    os.path.exists('/usr/local/bin/firewalld')
                )
            ):
                banaction = 'firewallcmd-ipset'
        locs = _s['mc_locations.settings']()
        destmail = 'root@localhost'
        if 'fqdn' in _g:
            destmail = 'root@{0}'.format(_g['fqdn'])
        ignoreip = ['127.0.0.1']
        if _s['mc_nodetypes.is_vagrantvm']():
            ignoreip.append('10.0.2.2')
        data = _s['mc_utils.defaults'](
            'makina-states.services.firewall.fail2ban', {
                'location': locs['conf_dir'] + '/fail2ban',
                'destemail': destmail,
                'loglevel': '3',
                'logtarget': '/var/log/fail2ban.log',
                'mail_from': 'fail2ban@makina-corpus.com',
                'mail_to': 'root',
                'mail_enabled': 'false',
                'mail_host': 'localhost',
                'mail_port': '25',
                'mail_user': 'foo',
                'mail_password': 'bar',
                'mail_localtime': 'true',
                'actions': {
                },
                'filters': {
                    'wordpress': {
                        'failregex': (
                            '^%(__prefix_line)sWordpress'
                            ' authentication failure for'
                            ' .* from <HOST>$')
                    }
                },
                'jails': {
                    'wordpress': {
                        'filter': 'wordpress',
                        'port': 'http,https',
                    }
                },
                'default_filters_opts': {
                    'ignoreregex': ''
                },
                'default_jail_opts': {
                    'port': 'ssh',
                    'logpath': '/var/log/syslog',
                    'banaction': banaction,
                    'maxretry': 5,
                    'findtime': 600,
                    'bantime': 600,
                    'enabled': False,
                    'filter': 'sshd',
                },
                'mail_subject': (
                    '[Fail2Ban {0}] <section>: Banned <ip>'
                ).format(_g['id']),
                'mail_message': (
                    'Hi,<br> The IP <ip> has just been banned by Fail2Ban'
                    ' after <failures> attempts against <section>.<br>'
                    ' Regards,<br> Fail2Ban'),
                'socket': '/var/run/fail2ban/fail2ban.sock',
                'backend': 'polling',
                'bantime': '86400',
                'extra_confs': {
                    '/etc/fail2ban/fail2ban.conf': {'mode': '750'},
                    # not yet in trusty !
                    '/etc/fail2ban/jail.conf': {'mode': '750'},
                    '/etc/init.d/fail2ban': {'mode': '750'},
                    '/etc/systemd/system/fail2ban.service': {'mode': '644'},
                },
                'maxretry': '10',
                'ssh_maxretry': '{maxretry}',
                'protocol': 'tcp',
                'mta': 'sendmail',
                'banaction': banaction,
                'ignoreip': ignoreip,
                'postfix_enabled': 'false',
                'wuftpd_enabled': 'false',
                'vsftpd_enabled': 'false',
                'proftpd_enabled': 'false',
                'pureftpd_enabled': 'false',
                'ssh_enabled': 'true',
                'recidive_enabled': 'false',
                'asterisk_tcp_enabled': 'false',
                'asterisk_udp_enabled': 'false',
                'named_refused_tcp_enabled': 'false',
            }
        )
        # if a filter is defined with the same name of a jail
        # and no filter is defined for this jail
        # make this filter as the jailname
        for item in [a for a in data['jails']]:
            ddata = data['jails'][item]
            if (
                'filter' not in ddata and
                (item in data['filters'])
            ):
                ddata['filter'] = item
        return data
    return _settings()
