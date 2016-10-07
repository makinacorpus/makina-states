
# -*- coding: utf-8 -*-
'''
.. _module_mc_burp:

mc_burp / burp functions
==================================



burp settings
'''

# Import python libs
import logging
import random
import os
import mc_states.api
from salt.utils.odict import OrderedDict
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
        - cron_periodicity: automaticly spray all around the hour
        - cron_cmd
        - restore_client
        - ssh_port (default 22)
        - ssh_username (default root)

    For each client you can define a ssh gateway
    (eg: for VMs with a private ip)

    Extra params are:

        - ssh_gateway: ip[:port] (default: 22)
        - ssh_gateway_user
        - ssh_gateway_key

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s, _g = __salt__,  __grains__
        debmode = None
        mc_pkgs = _s['mc_pkgs.settings']()
        ppa = None
        source = False
        pkgs = ['burp']
        fromrepo = None
        if debmode == 'debsource':
            pkgs = ['librsync-dev',
                    'zlib1g-dev',
                    'libssl-dev',
                    'uthash-dev',
                    'rsync',
                    'build-essential',
                    'libncurses5-dev',
                    'libacl1-dev']
        if _g['os'] in ['Ubuntu'] and _g['osrelease'] < '14.04':
            ppa = ('deb'
                   ' http://ppa.launchpad.net/bas-dikkenberg/'
                   'burp-stable/ubuntu'
                   ' {udist} main').format(**mc_pkgs)
        if _g['os'] in ['Debian']:
            fromrepo = 'sid'
            if _g['osrelease'][0] < '6':
                source = True
        local_conf = _s['mc_macros.get_local_registry'](
            'burp', registry_format='pack')
        ca_pass = local_conf.get('ca_pass', secure_password(32))
        server_pass = local_conf.get('server_pass', secure_password(32))
        timers = local_conf.setdefault('timers_v2', OrderedDict())
        local_conf['ca_pass'] = ca_pass
        local_conf['server_pass'] = server_pass
        data = _s['mc_utils.defaults'](
            'makina-states.services.backup.burp', {
                'ppa': ppa,
                'source': source,
                'fromrepo': fromrepo,
                'pkgs': pkgs,
                'admins': 'root',
                'cron_activated': True,
                'cron_periodicity': '40 0,6,12,18 * * *',
                'ver': '1.3.48',
                'user': 'root',
                'group': 'root',
                'ssl_cert_ca': '/etc/burp/ssl_cert_ca.pem',
                'server_conf': {
                    'fqdn': _g['id'],
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
                    'timer_arg': ['28h',
                                  ('Mon,Tue,Wed,Thu,Fri,'
                                   '00,01,02,03,04,05,06,07,08,09,10,11,12,'
                                   '13,14,15,16,17,18,19,20,21,22,23'),
                                  ('Sat,Sun,'
                                   '00,01,02,03,04,05,06,07,08,09,10,11,12,'
                                   '13,14,15,16,17,18,19,20,21,22,23')],
                    'ca_conf': '/etc/burp/CA.cnf',
                    'ca_name': 'burpCA',
                    'ca_server_name': _g['id'],
                    'ca_burp_ca': '/usr/sbin/burp_ca',
                    'ssl_cert': '/etc/burp/ssl_cert-server.pem',
                    'ssl_key': '/etc/burp/ssl_cert-server.key',
                    'ssl_key_password': server_pass,
                    'ssl_dhfile': '/etc/burp/dhfile.pem',
                    'notify_failure_script': '/etc/burp/notify_script',
                    'notify_failure_arg': [
                        'sendmail -t',
                        'To: root',
                        'From: "burp {0}" <root@makina-corpus.com>'.format(_g['id']),
                        'Subject: %b failed: %c %w'],
                    'server_script_pre': None,
                    'server_script_pre_arg': None,
                    'server_script_pre_notify': '0',
                    'server_script_post': None,
                    'server_script_post_arg': None,
                    'server_script_post_run_on_fail': '0',
                    'server_script_post_notify': '0',
                    'restore_client': None,
                    'restore_port': '4973',
                    'restore_status_port': '7974',
                    'restore_client_port': '4973',
                    'restore_client_status_port': '7974',
                    'restore_pidfile': '/var/run/burp.restore.pid',
                    'restore_lockfile': '/var/run/burp-server-restore.lock',
                    'lockfile': '/var/run/burp-server.lock',
                },
                'client_common': {
                    'dedup_group': 'linux',
                    'mode': 'client',
                    'port': '4971',
                    'restore_port': '4973',
                    'restore_status_port': '4974',
                    'syslog': '0',
                    'pidfile': '/var/run/burp.client.pid',
                    'restore_pidfile': '/var/run/burp.clientrestore.pid',
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
                    'restore_lockfile': '/var/run/burp-client.restore.lock',
                    'lockfile': '/var/run/burp-client.lock',
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
                        "* * * * *"
                    ),
                    'cron_cmd': (
                        " {user} /etc/burp/cron.sh 1>/dev/null 2>&1"
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
        tries_per_hour = 1
        hour = [i * (60 / tries_per_hour) for i in range(tries_per_hour)]
        removes = []
        for cname in [a for a in data['clients']]:
            cl = data['clients'][cname]
            if not isinstance(cl, dict):
                removes.append(cname)
                continue
            cl['cname'] = cname
            ssh_port = cl.get('ssh_port', '')
            if ssh_port:
                ssh_port = '-p {0}'.format(ssh_port)
            cl['rsh_cmd'] = 'ssh {1} {2} {4} {0} {3}'.format(
                '-oStrictHostKeyChecking=no',
                # Set hosts key database path to /dev/null, ie, non-existing
                '-oUserKnownHostsFile=/dev/null',
                # Don't re-use the SSH connection. Less failures.
                '-oControlPath=none',
                ssh_port,
                '-oPreferredAuthentications=publickey'
            )
            cl['rsh_dst'] = '{1}@{0}'.format(cname,
                                             cl.get('ssh_username', 'root'))
            cl['ssh_cmd'] = cl['rsh_cmd'] + '{1}@{0}'.format(
                cname, cl.get('ssh_username', 'root'))
            if 'ssh_gateway' in cl:
                ssh_gateway_key = ''
                if 'ssh_gateway_key' in cl:
                    ssh_gateway_key = '-i {0}'.format(cl['ssh_gateway_key'])
                ssh_gateway = cl['ssh_gateway']
                ssh_gateway_port = ''
                if ':' in ssh_gateway:
                    ssh_gateway, ssh_gateway_port = ssh_gateway.split(':')
                if ssh_gateway_port:
                    ssh_gateway_port = '-p {0}'.format(ssh_gateway_port)
                # Setup ProxyCommand
                proxy_cmd = (
                    ' -oProxyCommand="'
                    'ssh {0} {1} {2} {7} {3} {4}@{5} {6} '
                    'nc -q0 %h %p"'
                ).format(
                    '-oStrictHostKeyChecking=no',
                    # Set hosts key database path to /dev/null
                    '-oUserKnownHostsFile=/dev/null',
                    # Don't re-use the SSH connection. Less failures.
                    '-oControlPath=none',
                    ssh_gateway_key,
                    cl.get('ssh_gateway_user', 'root'),
                    ssh_gateway,
                    ssh_gateway_port,
                    '-oPreferredAuthentications=publickey'
                )
                cl['ssh_cmd'] += proxy_cmd
                cl['rsh_cmd'] += proxy_cmd
            cl.setdefault('activated', True)
            cl.setdefault('restore_client', '')
            restore_clients = [a for a in cl['restore_client'].split(',')
                               if a.strip()]
            if not data['server_conf']['fqdn'] in restore_clients:
                restore_clients.append(data['server_conf']['fqdn'])
            cl['restore_client'] = ','.join(restore_clients)
            if cl['cname'] == data['server_conf']['fqdn']:
                # backup host is only a client to query backups
                # and restore
                # we usually do not backup the backups locally
                excreg = cl.setdefault('exclude_regex', [])
                if data['server_conf']['directory'] not in excreg:
                    excreg.append('{0}.*'.format(
                        data['server_conf']['directory'].replace(
                            '/', '.*')))
                cl.setdefault('activated', True)
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
                # spray around the periodicity to spray the backup load
                # all over the hour.
                if k == 'cron_periodicity':
                    # val = None
                    try:
                        val = timers.get(cname, None)
                        tries = val.split()[0].split(',')
                        if not len(tries) == tries_per_hour:
                            val = None
                    except Exception:
                        val = None
                    if not val:
                        per = hour[:]
                        for ix, item in enumerate(per[:]):
                            rand = random.randint(0, (60/tries_per_hour)) - 1
                            if rand < 0:
                                rand = 0
                            item = item + rand
                            if item >= 60:
                                item = item - 60
                            if item not in per:
                                per[ix] = item
                        per = _s['mc_utils.uniquify'](per)
                        val = '{0} */6 * * *'.format(','.join(
                            ["{0}".format(t) for t in per]))
                    timers[cname] = val
                cl.setdefault(k, val)
        to_delete = [a for a in local_conf
                     if a.count('makina-states.local.burp.') >= 1]
        for a in to_delete:
            local_conf.pop(a, None)
        for i in removes:
            data['clients'].pop(i, None)
        _s['mc_macros.update_registry_params'](
            'burp', local_conf, registry_format='pack')
        return data
    return _settings()
#
