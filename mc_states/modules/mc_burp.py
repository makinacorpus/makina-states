
# -*- coding: utf-8 -*-
'''
.. _module_mc_burp:

mc_burp / burp functions
==================================

burp settings
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import mc_states.utils
from salt.utils.pycrypto import secure_password


__name = 'burp'

log = logging.getLogger(__name__)


def settings():
    '''
    burp settings
    server generates its ca
    server generate locally the client configuration and push it via rsync
    to clients

    prefix: makina-states.services.backups.burp

    Server opts (prefix: makina-states.services.backups.burp.server_conf)

        - fqdn
        - port
        - status_port
        - client_port
        - client_status_port
        - directory
        - clientconfdir
        - pidfile
        - hardlinked_archive
        - working_dir_recovery_method
        - max_children
        - max_status_children
        - umask
        - syslog
        - stdout
        - client_can_delete
        - client_can_force_backup
        - client_can_list
        - client_can_restore
        - client_can_verify
        - version_warn
        - keep
        - timer_script
        - timer_arg
        - ca_conf
        - ca_name
        - ca_server_name
        - ca_burp_ca
        - ssl_cert
        - ssl_key
        - ssl_key_password
        - ssl_dhfile
        - notify_failure_script
        - notify_failure_arg
        - server_script_pre
        - server_script_pre_arg
        - server_script_pre_notify
        - server_script_post
        - server_script_post_arg
        - server_script_post_run_on_fail
        - server_script_post_notify
        - restore_client

    client opts (client_common and client.<fqdn>)
        - (prefix: makina-states.services.backups.burp.client_common)
        - (prefix: makina-states.services.backups.burp.clients.<fqdn>)
        - dedup_group
        - mode
        - port
        - pidfile
        - syslog
        - stdout
        - progress_counter
        - ratelimit
        - network_timeout
        - autoupgrade_dir
        - autoupgrade_os
        - server_can_restore
        - cross_filesystem
        - cross_all_filesystems
        - encryption_password
        - ca_burp_ca
        - ca_csr_dir
        - ssl_cert
        - ssl_key
        - ssl_ciphers
        - backup_script_pre
        - backup_script_post
        - restore_script_pre
        - restore_script_post
        - include
        - exclude
        - exclude_ext
        - exclude_regex
        - exclude_fs
        - min_file_size
        - max_file_size
        - nobackup
        - read_fifo
        - read_all_fifos
        - read_blockdev
        - read_all_blockdevs
        - exclude_comp
        - cron_periodicity
        - cron_cmd
        - restore_client

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        salt = __salt__
        local_conf = salt['mc_macros.get_local_registry']('burp')
        ca_pass = local_conf.get('ca_pass', secure_password(32))
        server_pass = local_conf.get('server_pass', secure_password(32))
        local_conf['ca_pass'] = ca_pass
        local_conf['server_pass'] = server_pass
        grains = __grains__
        pillar = __pillar__
        locs = __salt__['mc_locations.settings']()
        data = {}
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.backup.burp', {
                'user': 'root',
                'group': 'root',
                'ssl_cert_ca': '/etc/burp/ssl_cert_ca.pem',
                'server_conf': {
                    'fqdn': grains['id'],
                    'port': '4971',
                    'status_port': '7972',
                    'client_port': '4971',
                    'client_status_port': '7972',
                    'directory': '/data/burp',
                    'clientconfdir': '/etc/burp/clientconfdir',
                    'pidfile': '/var/run/burp.server.pid',
                    'hardlinked_archive': '1',
                    'working_dir_recovery_method': 'delete',
                    'max_children': '5',
                    'max_status_children': '5',
                    'umask': '0022',
                    'syslog': '1',
                    'stdout': '0',
                    'client_can_delete': '0',
                    'client_can_force_backup': '0',
                    'client_can_list': '1',
                    'client_can_restore': '1',
                    'client_can_verify': '1',
                    'version_warn': '1',
                    'keep': [7, 4, 6],
                    # s (sec), m (min), h (hours), d (day), w (week), n (month)
                    # Allow backups to start in the evenings and nights
                    # during weekdays
                    # Allow more hours at the weekend.
                    'timer_script': '/etc/burp/timer_script',
                    'timer_arg': ['20h',
                                  ('Mon,Tue,Wed,Thu,Fri,'
                                   '00,01,02,03,04,05,19,20,21,22,23'),
                                  ('Sat,Sun,'
                                   '00,01,02,03,04,05,06,07,08,'
                                   '17,18,19,20,21,22,23')],
                    'ca_conf': '/etc/burp/CA.cnf',
                    'ca_name': 'burpCA',
                    'ca_server_name': grains['id'],
                    'ca_burp_ca': '/usr/sbin/burp_ca',
                    'ssl_cert': '/etc/burp/ssl_cert-server.pem',
                    'ssl_key': '/etc/burp/ssl_cert-server.key',
                    'ssl_key_password': server_pass,
                    'ssl_dhfile': '/etc/burp/dhfile.pem',
                    'notify_failure_script': '/etc/burp/notify_script',
                    'notify_failure_arg': [
                        'sendmail -t',
                        'To: root',
                        'From: "burp {0}" <root@makina-corpus.com>'.format(grains['id']),
                        'Subject: %b failed: %c %w'],
                    'server_script_pre': None,
                    'server_script_pre_arg': None,
                    'server_script_pre_notify': '0',
                    'server_script_post': None,
                    'server_script_post_arg': None,
                    'server_script_post_run_on_fail': '0',
                    'server_script_post_notify': '0',
                    'restore_client': None,
                },
                'client_common': {
                    'dedup_group': 'linux',
                    'mode': 'client',
                    'port': '4971',
                    'pidfile': '/var/run/burp.client.pid',
                    'syslog': '0',
                    'stdout': '1',
                    'progress_counter': '1',
                    'ratelimit': None,
                    'network_timeout': '7200',
                    'autoupgrade_dir': None,
                    'autoupgrade_os': None,
                    'server_can_restore': '1',
                    'cross_filesystem': [],
                    'cross_all_filesystems': '0',
                    'encryption_password': None,
                    'ca_burp_ca': None,
                    'ca_csr_dir': None,
                    'ssl_cert': '/etc/burp/ssl_cert-client.pem',
                    'ssl_key': '/etc/burp/ssl_cert-client.key',
                    'ssl_ciphers': None,
                    'backup_script_pre': None,
                    'backup_script_post': None,
                    'restore_script_pre': None,
                    'restore_script_post': None,
                    'include': ['/'],
                    'exclude': None,
                    'exclude_ext': ['pyc',
                                    'pyo'],
                    'exclude_regex': None,
                    'exclude_fs': ['sysfs', 'tmpfs'],
                    'min_file_size': None,
                    'max_file_size': None,
                    'nobackup': '.nobackup',
                    'read_fifo': None,
                    'read_all_fifos': None,
                    'read_blockdev': None,
                    'read_all_blockdevs': '0',
                    'exclude_comp': None,
                    'cron_periodicity': (
                        "07,27,47 * * * *"
                    ),
                    'cron_cmd': (
                        " {user} [ -x /usr/sbin/burp ] && "
                        " /usr/sbin/burp -a t "
                        "   >>/var/log/burp-client 2>&1"
                    )
                },
                'clients': {
                    # mapping of clients confs (defined in pillar),
                }
            }
        )
        for k in ['user',
                  'group',
                  'ssl_cert_ca']:
            data['server_conf'][k] = data['client_common'][k] = data[k]
        data['client_common']['cron_cmd'].format(user=data['user'])
        data['client_common'].setdefault('server',
                                         data['server_conf']['fqdn'])
        data['client_common'].setdefault(
            'ssl_peer_cn', data['server_conf']['fqdn'])
        data['clients'].setdefault(data['server_conf']['fqdn'], {})
        for cname in [a for a in data['clients']]:
            cl = data['clients'][cname]
            cl['cname'] = cname

            # backup host is only a client to query backups
            # and restore
            # we do not backup the backups locally
            cl.setdefault('activated', True)
            cl.setdefault('restore_client', '')
            restore_clients = [a for a in cl['restore_client'].split(',')
                               if a.strip()]
            if not data['server_conf']['fqdn'] in restore_clients:
                restore_clients.append(data['server_conf']['fqdn'])
            cl['restore_client'] = ','.join(restore_clients)
            if cl['cname'] == data['server_conf']['fqdn']:
                cl['activated'] = False
                cl['port'] = data['server_conf']['client_port']
                cl['status_port'] = data['server_conf']['client_status_port']
            if not cl['activated']:
                cl['include'] = []
                cl['cross_all_filesystems'] = []
                cl['exclude_regex'] = ['.*']
            cpassk = ('clients_passwords.{0}'.format(cname))
            cpass = local_conf.get(cpassk, secure_password(32))
            local_conf[cpassk] = cpass
            cl['ssl_key_password'] = cpass
            cpassk = ('clients_clipasswords.{0}'.format(cname))
            cpass = local_conf.get(cpassk, secure_password(32))
            local_conf[cpassk] = cpass
            cl['password'] = cpass
            for k, val in data['client_common'].items():
                cl.setdefault(k, val)
        salt['mc_macros.update_registry_params'](
            'burp', local_conf)
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
