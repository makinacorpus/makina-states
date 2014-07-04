# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga:

mc_icinga / icinga functions
============================

The first level of subdictionaries is for distinguish configuration files. There is one subdictionary per configuration file. The key used for subdictionary correspond
to the name of the file but the "." is replaced with a "_"

The subdictionary "modules" contains a subsubdictionary for each module. In each module subdictionary, there is a subdictionary per file.
The key "enabled" in each module dictionary is for enabling or disabling the module.

The "nginx" and "uwsgi" sub-dictionaries are given to macros in \*\*kwargs parameter.

The key "package" is for listing packages installed between pre-install and post-install hooks

The keys "has_pgsql" and "has_mysql" determine if a local postgresql or mysql instance must be installed.
The default value is computed from default database parameters
If the connection is made through a unix pipe or with the localhost hostname, the booleans are set to True.

'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import copy
import mc_states.utils

__name = 'icinga'

log = logging.getLogger(__name__)

def objects():
    locs = __salt__['mc_locations.settings']()
    data = {
        'directory': locs['conf_dir']+"/icinga/objects/salt_generated",
        'filescopy': ['check_ping',
                      'check_ssh',
                      'check_dig',
                      'check_http',
                      'check_ntp_peer',
                      'check_ntp_time',
                      'check_by_ssh',
                      'check_disk',
                      'check_raid.pl',
                      'check_md_raid',
                      'check_megaraid_sas',
                      'check_3ware_raid',
                      'check_cciss-1.12',
                      'check_drbd',
                      'check_swap',
                      'check_load',
                      'check_procs',
                      'check_cron',
                      'check_debian_packages',
                      'check_solr.py',
                      'check_burp_backup_age.py',
                      'check_rdiff',
                      'check_ddos.pl',
                      'check_haproxy_stats.pl',
                      'check_postfixqueue.sh',
                      'check_postfix_mailqueue'],
        'objects_definitions': {
            # meta_commands defintions
            'command_check_meta': {
                'type': "command",
                'file': "checkcommands/check_meta.cfg",
                'attrs': {
                    'command_name': "check_meta",
                    'command_line': "/usr/local/nagios/libexec/check_meta_service -i $ARG1$",
                },
            },
            'command_meta_notify': {
                'type': "command",
                'file': "checkcommands/meta_notify.cfg",
                'attrs': {
                    'command_name': "meta_notify",
                    'command_line': "/usr/bin/printf \"%b\" \"***** Meta Service Centreon *****\\n\\nNotification Type: $NOTIFICATIONTYPE$\\n\\nService: $SERVICEDESC$\\nState: $SERVICESTATE$\\n\\nDate/Time: $DATETIME$\\n\\nAdditional Info:\\n\\n$OUTPUT$\" | \/bin\/mail -s \"** $NOTIFICATIONTYPE$ $SERVICEDESC$ is $SERVICESTATE$ **\" $CONTACTEMAIL$",
                },
            },

            # commands definitions
            'command_ALWAYS_UP': {
                'type': "command",
                'file': "checkcommands/ALWAYS_UP.cfg",
                'attrs': {
                    'command_name': "ALWAYS_UP",
                    'command_line': "$USER1$/check_centreon_dummy -s 0 -o \"PING Not Allowed, always OK\"",
                },
            },
            'command_check_centreon_cpu': {
                'type': "command",
                'file': "checkcommands/check_centreon_cpu.cfg",
                'attrs': {
                    'command_name': "check_centreon_cpu",
                    'command_line': "$USER1$/check_centreon_snmp_cpu -H $HOSTADDRESS$ -v 1 -C $ARG1$ -c $ARG2$ -w $ARG3$",
                },
            },
            'command_check_centreon_dummy': {
                'type': "command",
                'file': "checkcommands/check_centreon_dummy.cfg",
                'attrs': {
                    'command_name': "check_centreon_dummy",
                    'command_line': "$USER1$/check_centreon_dummy -s $ARG1$ -o $ARG2$",
                },
            },
            'command_check_centreon_load_average': {
                'type': "command",
                'file': "checkcommands/check_centreon_load_average.cfg",
                'attrs': {
                    'command_name': "check_centreon_load_average",
                    'command_line': "$USER1$/check_centreon_snmp_loadaverage -H $HOSTADDRESS$ -v $ARG1$ -C $ARG2$ -w $ARG3$ -c $ARG4$",
                },
            },
            'command_check_centreon_memory': {
                'type': "command",
                'file': "checkcommands/check_centreon_memory.cfg",
                'attrs': {
                    'command_name': "check_centreon_memory",
                    'command_line': "$USER1$/check_centreon_snmp_memory -H $HOSTADDRESS$ -C $USER2$ -v 1 -w 80 -c 90",
                },
            },
            'command_check_centreon_nb_connections': {
                'type': "command",
                'file': "checkcommands/check_centreon_nb_connections.cfg",
                'attrs': {
                    'command_name': "check_centreon_nb_connections",
                    'command_line': "$USER1$/check_centreon_TcpConn -H $HOSTADDRESS$ -C $USER2$ -v 1 -p $ARG1$ -w $ARG2$ -c $ARG3$",
                },
            },
            'command_check_centreon_nt': {
                'type': "command",
                'file': "checkcommands/check_centreon_nt.cfg",
                'attrs': {
                    'command_name': "check_centreon_nt",
                    'command_line': "$USER1$/check_centreon_nt -H $HOSTADDRESS$ -p 12489 -v $ARG1$ -l $ARG2$ -s $ARG3$ -w $ARG4$ -c $ARG5$",
                },
            },
            'command_check_centreon_ping': {
                'type': "command",
                'file': "checkcommands/check_centreon_ping.cfg",
                'attrs': {
                    'command_name': "check_centreon_ping",
                    'command_line': "$USER1$/check_centreon_ping -H $HOSTADDRESS$ -n $ARG1$ -w $ARG2$ -c $ARG3$",
                },
            },
            'command_check_centreon_process': {
                'type': "command",
                'file': "checkcommands/check_centreon_process.cfg",
                'attrs': {
                    'command_name': "check_centreon_process",
                    'command_line': "$USER1$/check_centreon_snmp_process -H $HOSTADDRESS$ -v $ARG1$ -C $ARG2$ -n -p $ARG3$",
                },
            },
            'command_check_centreon_remote_storage': {
                'type': "command",
                'file': "checkcommands/check_centreon_remote_storage.cfg",
                'attrs': {
                    'command_name': "check_centreon_remote_storage",
                    'command_line': "$USER1$/check_centreon_snmp_remote_storage -H $HOSTADDRESS$ -n -d $ARG1$ -w $ARG2$ -c $ARG3$ -C $ARG4$ -v $ARG5$",
                },
            },
            'command_check_centreon_snmp_proc_detailed': {
                'type': "command",
                'file': "checkcommands/check_centreon_snmp_proc_detailed.cfg",
                'attrs': {
                    'command_name': "check_centreon_snmp_proc_detailed",
                    'command_line': "$USER1$/check_centreon_snmp_process_detailed -H $HOSTADDRESS$ -C $USER2$ -n $ARG1$ -m $ARG2$",
                },
            },
            'command_check_centreon_snmp_value': {
                'type': "command",
                'file': "checkcommands/check_centreon_snmp_value.cfg",
                'attrs': {
                    'command_name': "check_centreon_snmp_value",
                    'command_line': "$USER1$/check_centreon_snmp_value -H $HOSTADDRESS$ -C $ARG1$ -v $ARG2$ -o $ARG3$ -w $ARG4$  -c $ARG5$",
                },
            },
            'command_check_centreon_traffic': {
                'type': "command",
                'file': "checkcommands/check_centreon_traffic.cfg",
                'attrs': {
                    'command_name': "check_centreon_traffic",
                    'command_line': "$USER1$/check_centreon_snmp_traffic -H $HOSTADDRESS$ -n -i $ARG1$ -w $ARG2$ -c $ARG3$ -C $USER2$ -v $ARG4$",
                },
            },
            'command_check_centreon_traffic_limited': {
                'type': "command",
                'file': "checkcommands/check_centreon_traffic_limited.cfg",
                'attrs': {
                    'command_name': "check_centreon_traffic_limited",
                    'command_line': "$USER1$/check_centreon_snmp_traffic -H $HOSTADDRESS$ -n -i $ARG1$ -w $ARG2$ -c $ARG3$ -C $ARG4$ -v $ARG5$ -T $ARG6$",
                },
            },
            'command_check_centreon_uptime': {
                'type': "command",
                'file': "checkcommands/check_centreon_uptime.cfg",
                'attrs': {
                    'command_name': "check_centreon_uptime",
                    'command_line': "$USER1$/check_centreon_snmp_uptime -H $HOSTADDRESS$ -C $USER2$ -v 2 -d",
                },
            },
            'command_check_dhcp': {
                'type': "command",
                'file': "checkcommands/check_dhcp.cfg",
                'attrs': {
                    'command_name': "check_dhcp",
                    'command_line': "$USER1$/check_dhcp -s $HOSTADDRESS$ -i $ARG1$",
                },
            },
            'command_check_dig': {
                'type': "command",
                'file': "checkcommands/check_dig.cfg",
                'attrs': {
                    'command_name': "check_dig",
                    'command_line': "$USER1$/check_dig -H $HOSTADDRESS$ -l $ARG1$",
                },
            },
            'command_check_disk_smb': {
                'type': "command",
                'file': "checkcommands/check_disk_smb.cfg",
                'attrs': {
                    'command_name': "check_disk_smb",
                    'command_line': "$USER1$/check_disk_smb -H $HOSTADDRESS$ -s $ARG1$ -u $ARG2$ -p $ARG3$ -w $ARG4$ -c $ARG5$",
                },
            },
            'command_check_distant_disk_space': {
                'type': "command",
                'file': "checkcommands/check_distant_disk_space.cfg",
                'attrs': {
                    'command_name': "check_distant_disk_space",
                    'command_line': "$USER1$/check_distant_disk_space -H $HOSTADDRESS$ -C $ARG1$ -p $ARG2$ -w $ARG3$ -c $ARG4$",
                },
            },
            'command_check_dns': {
                'type': "command",
                'file': "checkcommands/check_dns.cfg",
                'attrs': {
                    'command_name': "check_dns",
                    'command_line': "$USER1$/check_dns -H $ARG1$ -s $HOSTADDRESS$",
                },
            },
            'command_check_ftp': {
                'type': "command",
                'file': "checkcommands/check_ftp.cfg",
                'attrs': {
                    'command_name': "check_ftp",
                    'command_line': "$USER1$/check_ftp -H $HOSTADDRESS$",
                },
            },
            'command_check_host_alive': {
                'type': "command",
                'file': "checkcommands/check_host_alive.cfg",
                'attrs': {
                    'command_name': "check_host_alive",
                    'command_line': "$USER1$/check_ping -H $HOSTADDRESS$ -w 3000.0,80% -c 5000.0,100% -p 1",
                },
            },
            'command_check_hpjd': {
                'type': "command",
                'file': "checkcommands/check_hpjd.cfg",
                'attrs': {
                    'command_name': "check_hpjd",
                    'command_line': "$USER1$/check_hpjd -H $HOSTADDRESS$ -C public",
                },
            },
            'command_check_http': {
                'type': "command",
                'file': "checkcommands/check_http.cfg",
                'attrs': {
                    'command_name': "check_http",
                    'command_line': "$USER1$/check_http -H $HOSTADDRESS$",
                },
            },
            'command_check_https': {
                'type': "command",
                'file': "checkcommands/check_https.cfg",
                'attrs': {
                    'command_name': "check_https",
                    'command_line': "$USER1$/check_http -S $HOSTADDRESS$",
                },
            },
            'command_check_http_vhost_uri': {
                'type': "command",
                'file': "checkcommands/check_http_vhost_uri.cfg",
                'attrs': {
                    'command_name': "check_http_vhost_uri",
                    'command_line': "$USER1$/check_http -H $ARG1$ -u $ARG2$",
                },
            },
            'command_check_load_average': {
                'type': "command",
                'file': "checkcommands/check_load_average.cfg",
                'attrs': {
                    'command_name': "check_load_average",
                    'command_line': "$USER1$/check_load $HOSTADDRESS$ -w $ARG1$ -c $ARG2$",
                },
            },
            'command_check_local_cpu_load': {
                'type': "command",
                'file': "checkcommands/check_local_cpu_load.cfg",
                'attrs': {
                    'command_name': "check_local_cpu_load",
                    'command_line': "$USER1$/check_nt -H $HOSTADDRESS$ -v CPULOAD -l $ARG1$ -s \"public\"",
                },
            },
            'command_check_local_disk': {
                'type': "command",
                'file': "checkcommands/check_local_disk.cfg",
                'attrs': {
                    'command_name': "check_local_disk",
                    'command_line': "$USER1$/check_disk -w $ARG2$ -c $ARG3$ -p $ARG1$",
                },
            },
            'command_check_local_disk_space': {
                'type': "command",
                'file': "checkcommands/check_local_disk_space.cfg",
                'attrs': {
                    'command_name': "check_local_disk_space",
                    'command_line': "$USER1$/check_nt -H $HOSTADDRESS$ -v USEDDISKSPACE -l $ARG1$ -w $ARG2$ -c $ARG3$ -s \"public\"",
                },
            },
            'command_check_local_load': {
                'type': "command",
                'file': "checkcommands/check_local_load.cfg",
                'attrs': {
                    'command_name': "check_local_load",
                    'command_line': "$USER1$/check_load -w $ARG1$ -c $ARG2$",
                },
            },
            'command_check_local_procs': {
                'type': "command",
                'file': "checkcommands/check_local_procs.cfg",
                'attrs': {
                    'command_name': "check_local_procs",
                    'command_line': "$USER1$/check_procs -w $ARG1$ -c $ARG2$ -u $ARG3$",
                },
            },
            'command_check_local_procs_1': {
                'type': "command",
                'file': "checkcommands/check_local_procs_1.cfg",
                'attrs': {
                    'command_name': "check_local_procs_1",
                    'command_line': "$USER1$/check_procs -w $ARG1$ -c $ARG2$ -u $ARG3$",
                },
            },
            'command_check_local_swap': {
                'type': "command",
                'file': "checkcommands/check_local_swap.cfg",
                'attrs': {
                    'command_name': "check_local_swap",
                    'command_line': "$USER1$/check_swap -w $ARG1$ -c $ARG2$ -v",
                },
            },
            'command_check_local_users': {
                'type': "command",
                'file': "checkcommands/check_local_users.cfg",
                'attrs': {
                    'command_name': "check_local_users",
                    'command_line': "$USER1$/check_users -w $ARG1$ -c $ARG2$",
                },
            },
            'command_check_maxq': {
                'type': "command",
                'file': "checkcommands/check_maxq.cfg",
                'attrs': {
                    'command_name': "check_maxq",
                    'command_line': "$USER1$/check_maxq_script_return -r $ARG1$ -P $ARG2$",
                },
            },
            'command_check_nntp': {
                'type': "command",
                'file': "checkcommands/check_nntp.cfg",
                'attrs': {
                    'command_name': "check_nntp",
                    'command_line': "$USER1$/check_nntp -H $HOSTADDRESS$",
                },
            },
            'command_check_nt_cpu': {
                'type': "command",
                'file': "checkcommands/check_nt_cpu.cfg",
                'attrs': {
                    'command_name': "check_nt_cpu",
                    'command_line': "$USER1$/check_nt -H $HOSTADDRESS$ -v CPULOAD -s \"public\" -p $ARG1$ -l 2,90,95",
                },
            },
            'command_check_nt_disk': {
                'type': "command",
                'file': "checkcommands/check_nt_disk.cfg",
                'attrs': {
                    'command_name': "check_nt_disk",
                    'command_line': "$USER1$/check_nt -H $HOSTADDRESS$ -v USEDDISKSPACE -s \"public\" -l $ARG1$ -w $ARG2$ -c $ARG3$",
                },
            },
            'command_check_nt_memuse': {
                'type': "command",
                'file': "checkcommands/check_nt_memuse.cfg",
                'attrs': {
                    'command_name': "check_nt_memuse",
                    'command_line': "$USER1$/check_nt -H $HOSTADDRESS$ -v MEMUSE -s \"public\" -p $ARG1$ -w $ARG2$ -c $ARG3$",
                },
            },
            'command_check_pop': {
                'type': "command",
                'file': "checkcommands/check_pop.cfg",
                'attrs': {
                    'command_name': "check_pop",
                    'command_line': "$USER1$/check_pop -H $HOSTADDRESS$",
                },
            },
            'command_check_smtp': {
                'type': "command",
                'file': "checkcommands/check_smtp.cfg",
                'attrs': {
                    'command_name': "check_smtp",
                    'command_line': "$USER1$/check_smtp -H $HOSTADDRESS$",
                },
            },
            'command_check_snmp': {
                'type': "command",
                'file': "checkcommands/check_snmp.cfg",
                'attrs': {
                    'command_name': "check_snmp",
                    'command_line': "$USER1$/check_snmp -H $HOSTADDRESS$ -o $ARG1$ -w $ARG2$ -C $ARG3$",
                },
            },
            'command_check_tcp': {
                'type': "command",
                'file': "checkcommands/check_tcp.cfg",
                'attrs': {
                    'command_name': "check_tcp",
                    'command_line': "$USER1$/check_tcp -H $HOSTADDRESS$ -p $ARG1$ -w $ARG2$ -c $ARG3$",
                },
            },
            'command_check_telnet': {
                'type': "command",
                'file': "checkcommands/check_telnet.cfg",
                'attrs': {
                    'command_name': "check_telnet",
                    'command_line': "$USER1$/check_tcp -H $HOSTADDRESS$ -p 23",
                },
            },
            'command_check_udp': {
                'type': "command",
                'file': "checkcommands/check_udp.cfg",
                'attrs': {
                    'command_name': "check_udp",
                    'command_line': "$USER1$/check_udp -H $HOSTADDRESS$ -p $ARG1$",
                },
            },
            'command_CSSH_BACKUP': {
                'type': "command",
                'file': "checkcommands/CSSH_BACKUP.cfg",
                'attrs': {
                    'command_name': "CSSH_BACKUP",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG1$",
                },
            },
            'command_CSSH_BACKUP_BURP': {
                'type': "command",
                'file': "checkcommands/CSSH_BACKUP_BURP.cfg",
                'attrs': {
                    'command_name': "CSSH_BACKUP_BURP",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -q -H $ARG1$ -l root -i $USER7_SSHKEY$ -C '/root/admin_scripts/nagios/check_burp_backup_age.py -H $HOSTNAME$ -d /data/burp -w $ARG2$ -c $ARG3$'",
                },
            },
            'command_CSSH_BACKUP_EXT': {
                'type': "command",
                'file': "checkcommands/CSSH_BACKUP_EXT.cfg",
                'attrs': {
                    'command_name': "CSSH_BACKUP_EXT",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG1$",
                },
            },
            'command_CSSH_CRON': {
                'type': "command",
                'file': "checkcommands/CSSH_CRON.cfg",
                'attrs': {
                    'command_name': "CSSH_CRON",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C '/root/admin_scripts/nagios/check_cron'",
                },
            },
            'command_CSSH_CUSTOM': {
                'type': "command",
                'file': "checkcommands/CSSH_CUSTOM.cfg",
                'attrs': {
                    'command_name': "CSSH_CUSTOM",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -q -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG1$",
                },
            },
            'command_CSSH_CYRUS_CONNECTIONS': {
                'type': "command",
                'file': "checkcommands/CSSH_CYRUS_CONNECTIONS.cfg",
                'attrs': {
                    'command_name': "CSSH_CYRUS_CONNECTIONS",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr  -q -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C '/root/admin_scripts/nagios/check_cyrus-imapd -w  $ARG1$ -c $ARG2$'",
                },
            },
            'command_CSSH_DDOS': {
                'type': "command",
                'file': "checkcommands/CSSH_DDOS.cfg",
                'attrs': {
                    'command_name': "CSSH_DDOS",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C '/root/admin_scripts/nagios/check_ddos.pl -w $ARG1$ -c$ARG2$'",
                },
            },
            'command_CSSH_DEBIAN_UPDATES': {
                'type': "command",
                'file': "checkcommands/CSSH_DEBIAN_UPDATES.cfg",
                'attrs': {
                    'command_name': "CSSH_DEBIAN_UPDATES",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -q -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C '/root/admin_scripts/nagios/check_debian_packages --timeout=60' --timeout=60",
                },
            },
            'command_CSSH_DRBD': {
                'type': "command",
                'file': "checkcommands/CSSH_DRBD.cfg",
                'attrs': {
                    'command_name': "CSSH_DRBD",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG1$",
                },
            },
            'command_CSSH_HAPROXY': {
                'type': "command",
                'file': "checkcommands/CSSH_HAPROXY.cfg",
                'attrs': {
                    'command_name': "CSSH_HAPROXY",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG1$",
                },
            },
            'command_CSSH_MAILQUEUE': {
                'type': "command",
                'file': "checkcommands/CSSH_MAILQUEUE.cfg",
                'attrs': {
                    'command_name': "CSSH_MAILQUEUE",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C '/root/admin_scripts/nagios/check_postfix_mailqueue -w $ARG1$ -c $ARG2$'",
                },
            },
            'command_CSSH_MEGARAID_SAS': {
                'type': "command",
                'file': "checkcommands/CSSH_MEGARAID_SAS.cfg",
                'attrs': {
                    'command_name': "CSSH_MEGARAID_SAS",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG1$",
                },
            },
            'command_CSSH_NTP_PEER': {
                'type': "command",
                'file': "checkcommands/CSSH_NTP_PEER.cfg",
                'attrs': {
                    'command_name': "CSSH_NTP_PEER",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$  -C '/root/check_ntp_peer -H 195.144.11.170 -w 1 -c 10 -j -1:100 -k -1:200 -W 4 -C 10'",
                },
            },
            'command_CSSH_NTP_PEERS': {
                'type': "command",
                'file': "checkcommands/CSSH_NTP_PEERS.cfg",
                'attrs': {
                    'command_name': "CSSH_NTP_PEERS",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C '/root/admin_scripts/nagios/check_ntp_peer -H $ARG1$ -w 1 -c 10 -j -1:100 -k -1:200 -W 4 -C 10'",
                },
            },
            'command_CSSH_NTP_TIME': {
                'type': "command",
                'file': "checkcommands/CSSH_NTP_TIME.cfg",
                'attrs': {
                    'command_name': "CSSH_NTP_TIME",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C '/root/check_ntp_time -H 195.144.11.170 -w 60 -c 120'",
                },
            },
            'command_CSSH_PROCESS_CRON_RUNNING': {
                'type': "command",
                'file': "checkcommands/CSSH_PROCESS_CRON_RUNNING.cfg",
                'attrs': {
                    'command_name': "CSSH_PROCESS_CRON_RUNNING",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -q -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C '/root/admin_scripts/nagios/check_procs -w 1: -c 1: --command=cron'",
                },
            },
            'command_CSSH_RAID_3WARE': {
                'type': "command",
                'file': "checkcommands/CSSH_RAID_3WARE.cfg",
                'attrs': {
                    'command_name': "CSSH_RAID_3WARE",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG1$",
                },
            },
            'command_CSSH_RAID_SOFT': {
                'type': "command",
                'file': "checkcommands/CSSH_RAID_SOFT.cfg",
                'attrs': {
                    'command_name': "CSSH_RAID_SOFT",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG1$",
                },
            },
            'command_CSSH_RO_MOUNT': {
                'type': "command",
                'file': "checkcommands/CSSH_RO_MOUNT.cfg",
                'attrs': {
                    'command_name': "CSSH_RO_MOUNT",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr  -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG1$ -t $ARG2$",
                },
            },
            'command_CSSH_SAS2IRCU': {
                'type': "command",
                'file': "checkcommands/CSSH_SAS2IRCU.cfg",
                'attrs': {
                    'command_name': "CSSH_SAS2IRCU",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C $ARG2$",
                },
            },
            'command_CSSH_SUPERVISOR': {
                'type': "command",
                'file': "checkcommands/CSSH_SUPERVISOR.cfg",
                'attrs': {
                    'command_name': "CSSH_SUPERVISOR",
                    'command_line': "$USER1$/check_by_ssh --skip-stderr  -q -H $HOSTADDRESS$ -l root -i $USER7_SSHKEY$ -C '/root/admin_scripts/nagios/check_supervisorctl.sh $ARG1$'",
                },
            },
            'command_C_APACHE_STATUS': {
                'type': "command",
                'file': "checkcommands/C_APACHE_STATUS.cfg",
                'attrs': {
                    'command_name': "C_APACHE_STATUS",
                    'command_line': "$USER1$/check_apachestatus_auto.pl -H $HOSTADDRESS$  -t 8 -w $ARG1$ -c $ARG2$ $ARG3$",
                },
            },
            'command_C_CHECK_LABORANGE_LOGIN': {
                'type': "command",
                'file': "checkcommands/C_CHECK_LABORANGE_LOGIN.cfg",
                'attrs': {
                    'command_name': "C_CHECK_LABORANGE_LOGIN",
                    'command_line': "$USER1$/check_laborange_login.sh -u $ARG1$  -w $ARG2$  -c $ARG3$  $ARG4$",
                },
            },
            'command_C_CHECK_LABORANGE_STATS': {
                'type': "command",
                'file': "checkcommands/C_CHECK_LABORANGE_STATS.cfg",
                'attrs': {
                    'command_name': "C_CHECK_LABORANGE_STATS",
                    'command_line': "$USER1$/check_laborange_stats.pl -H $HOSTADDRESS$ -s $ARG1$  -t 5",
                },
            },
            'command_C_CHECK_NGINX_STATUS': {
                'type': "command",
                'file': "checkcommands/C_CHECK_NGINX_STATUS.cfg",
                'attrs': {
                    'command_name': "C_CHECK_NGINX_STATUS",
                    'command_line': "$USER1$/check_nginx_status.pl -H $HOSTADDRESS$ -u $ARG1$ -s $ARG2$  -t 8 -w $ARG3$ -c $ARG4$",
                },
            },
            'command_C_CHECK_ONE_NAGIOS_ONLY': {
                'type': "command",
                'file': "checkcommands/C_CHECK_ONE_NAGIOS_ONLY.cfg",
                'attrs': {
                    'command_name': "C_CHECK_ONE_NAGIOS_ONLY",
                    'command_line': "$USER1$/check_one_nagios",
                },
            },
            'command_C_CHECK_PHPFPM': {
                'type': "command",
                'file': "checkcommands/C_CHECK_PHPFPM.cfg",
                'attrs': {
                    'command_name': "C_CHECK_PHPFPM",
                    'command_line': "$USER1$/check_phpfpm_status.pl -H $HOSTADDRESS$ -u $ARG1$ -s $ARG2$  -t 8 -w $ARG3$ -c $ARG4$",
                },
            },
            'command_C_DNS_EXTERNE_ASSOCIATION': {
                'type': "command",
                'file': "checkcommands/C_DNS_EXTERNE_ASSOCIATION.cfg",
                'attrs': {
                    'command_name': "C_DNS_EXTERNE_ASSOCIATION",
                    'command_line': "$USER1$/check_dns_host.pl  -H $ARG1$ -q FORWARD -w 50 -c 500 -m $HOSTADDRESS$ -t 8 --recurse=1 $ARG2$",
                },
            },
            'command_C_HTTPS_OPENID_REDIRECT': {
                'type': "command",
                'file': "checkcommands/C_HTTPS_OPENID_REDIRECT.cfg",
                'attrs': {
                    'command_name': "C_HTTPS_OPENID_REDIRECT",
                    'command_line': "$USER1$/check_http -H $ARG1$ -I $HOSTADDRESS$  -u $ARG2$ --useragent=supervision --warning=$ARG3$ --critical=$ARG4$ --timeout=$ARG5$ -s \"https://openid.makina-corpus.net/login/login.php\" -S -e \"HTTP/1.1 302 Found\"",
                },
            },
            'command_C_HTTPS_STRING_ONLY': {
                'type': "command",
                'file': "checkcommands/C_HTTPS_STRING_ONLY.cfg",
                'attrs': {
                    'command_name': "C_HTTPS_STRING_ONLY",
                    'command_line': "$USER1$/check_http --ssl -H $ARG1$ -I $HOSTADDRESS$  -u $ARG2$ --useragent=supervision --onredirect=follow --timeout=$ARG4$ -s $ARG5$ $ARG6$",
                },
            },
            'command_C_HTTP_STRING': {
                'type': "command",
                'file': "checkcommands/C_HTTP_STRING.cfg",
                'attrs': {
                    'command_name': "C_HTTP_STRING",
                    'command_line': "$USER1$/check_http -H $ARG1$ -I $HOSTADDRESS$  -u $ARG2$ --useragent=supervision  --onredirect=follow --warning=$ARG3$ --critical=$ARG4$ --timeout=$ARG5$ -s $ARG6$ $ARG7$",
                },
            },
            'command_C_HTTP_STRING_AUTH': {
                'type': "command",
                'file': "checkcommands/C_HTTP_STRING_AUTH.cfg",
                'attrs': {
                    'command_name': "C_HTTP_STRING_AUTH",
                    'command_line': "$USER1$/check_http --ssl -H $ARG1$ -I $HOSTADDRESS$  -u $ARG2$ -a $USER6_AUTHPAIR$ --useragent=supervision --onredirect=follow --warning=$ARG3$ --critical=$ARG4$ --timeout=$ARG5$ -s $ARG6$ $ARG7$",
                },
            },
            'command_C_HTTP_STRING_ONLY': {
                'type': "command",
                'file': "checkcommands/C_HTTP_STRING_ONLY.cfg",
                'attrs': {
                    'command_name': "C_HTTP_STRING_ONLY",
                    'command_line': "$USER1$/check_http -H $ARG1$ -I $HOSTADDRESS$  -u $ARG2$ --useragent=supervision --onredirect=follow --timeout=$ARG4$ -s $ARG5$ $ARG6$",
                },
            },
            'command_C_HTTP_STRING_SOLR': {
                'type': "command",
                'file': "checkcommands/C_HTTP_STRING_SOLR.cfg",
                'attrs': {
                    'command_name': "C_HTTP_STRING_SOLR",
                    'command_line': "$USER1$/check_http -H $ARG1$ -p $ARG2$ -I $HOSTADDRESS$  -u $ARG3$ --useragent=supervision --onredirect=follow --warning=$ARG4$ --critical=$ARG5$ --timeout=$ARG6$ -s $ARG7$ $ARG8$",
                },
            },
            'command_C_HTTP_STRING_ZOPE': {
                'type': "command",
                'file': "checkcommands/C_HTTP_STRING_ZOPE.cfg",
                'attrs': {
                    'command_name': "C_HTTP_STRING_ZOPE",
                    'command_line': "$USER1$/check_http -H $ARG1$ -p $ARG2$ -I $HOSTADDRESS$  -u $ARG3$ --useragent=supervision --onredirect=follow --warning=$ARG4$ --critical=$ARG5$ --timeout=$ARG6$ -s $ARG7$ $ARG8$",
                },
            },
            'command_C_MAIL_IMAP': {
                'type': "command",
                'file': "checkcommands/C_MAIL_IMAP.cfg",
                'attrs': {
                    'command_name': "C_MAIL_IMAP",
                    'command_line': "$USER1$/check_imap -H $HOSTADDRESS$ -w $ARG1$ -c $ARG2$",
                },
            },
            'command_C_MAIL_IMAP_SSL': {
                'type': "command",
                'file': "checkcommands/C_MAIL_IMAP_SSL.cfg",
                'attrs': {
                    'command_name': "C_MAIL_IMAP_SSL",
                    'command_line': "$USER1$/check_imap -p 993 --ssl -H $HOSTADDRESS$ -w $ARG1$ -c $ARG2$",
                },
            },
            'command_C_MAIL_POP': {
                'type': "command",
                'file': "checkcommands/C_MAIL_POP.cfg",
                'attrs': {
                    'command_name': "C_MAIL_POP",
                    'command_line': "$USER1$/check_pop -H $HOSTADDRESS$ -w $ARG1$ -c $ARG2$",
                },
            },
            'command_C_MAIL_POP_SSL': {
                'type': "command",
                'file': "checkcommands/C_MAIL_POP_SSL.cfg",
                'attrs': {
                    'command_name': "C_MAIL_POP_SSL",
                    'command_line': "$USER1$/check_pop -p 995 --ssl -H $HOSTADDRESS$ -w $ARG1$ -c $ARG2$",
                },
            },
            'command_C_MAIL_SMTP': {
                'type': "command",
                'file': "checkcommands/C_MAIL_SMTP.cfg",
                'attrs': {
                    'command_name': "C_MAIL_SMTP",
                    'command_line': "$USER1$/check_smtp -H $HOSTADDRESS$ -w $ARG1$ -c $ARG2$ -e \"220 mail.makina-corpus.com ESMTP Postfix (BlueMind)\"  -f \"$USER8_TESTUSER$@makina-corpus.com\" -C 'RCPT TO:<$USER8_TESTUSER$@makina-corpus.com>' -R '250 2.1.5 Ok' -C 'data' -R '354 End data with <CR><LF>.<CR><LF>' -C '.' -R '250 2.0.0 Ok: queued'",
                },
            },
            'command_C_PING': {
                'type': "command",
                'file': "checkcommands/C_PING.cfg",
                'attrs': {
                    'command_name': "C_PING",
                    'command_line': "$USER1$/check_centreon_ping -H $HOSTADDRESS$ -n 5 -i 0.5",
                },
            },
            'command_C_POP3_TEST_SIZE_AND_DELETE': {
                'type': "command",
                'file': "checkcommands/C_POP3_TEST_SIZE_AND_DELETE.cfg",
                'attrs': {
                    'command_name': "C_POP3_TEST_SIZE_AND_DELETE",
                    'command_line': "$USER1$/check_pop3_cleaner.py -H $HOSTADDRESS$  -u $USER8_TESTUSER$$ARG5$ -p \"$USER9_TESTPWD$\" -d 25 -t 10 -w $ARG1$,$ARG3$ -c $ARG2$,$ARG4$",
                },
            },
            'command_C_PROCESS_IRCBOT_RUNNING': {
                'type': "command",
                'file': "checkcommands/C_PROCESS_IRCBOT_RUNNING.cfg",
                'attrs': {
                    'command_name': "C_PROCESS_IRCBOT_RUNNING",
                    'command_line': "$USER1$/check_procs -w 1: -c 1: --command=ircbot.py",
                },
            },
            'command_C_SNMP_DISK': {
                'type': "command",
                'file': "checkcommands/C_SNMP_DISK.cfg",
                'attrs': {
                    'command_name': "C_SNMP_DISK",
                    'command_line': "$USER1$/check_centreon_snmp_remote_storage2 -P 161 -v 3 -z des -x sha -y $USER3_SNMPCRYPT$ -p $USER4_SNMPPASS$ -u $USER5_SNMPUSER$ -H $HOSTADDRESS$ -n -d $ARG1$ -w $ARG2$ -c $ARG3$ -a 5",
                },
            },
            'command_C_SNMP_LOADAVG': {
                'type': "command",
                'file': "checkcommands/C_SNMP_LOADAVG.cfg",
                'attrs': {
                    'command_name': "C_SNMP_LOADAVG",
                    'command_line': "$USER1$/check_centreon_snmp_loadaverage2 -P 161 -v 3 -z des -x sha -y $USER3_SNMPCRYPT$ -p $USER4_SNMPPASS$ -u $USER5_SNMPUSER$ -H $HOSTADDRESS$ -w 30,30,30 -c 50,50,50 $ARG1$",
                },
            },
            'command_C_SNMP_MEMORY': {
                'type': "command",
                'file': "checkcommands/C_SNMP_MEMORY.cfg",
                'attrs': {
                    'command_name': "C_SNMP_MEMORY",
                    'command_line': "$USER1$/check_centreon_snmp_memory2 -P 161 -v 3 -z des -x sha -y $USER3_SNMPCRYPT$ -p $USER4_SNMPPASS$ -u $USER5_SNMPUSER$ -H $HOSTADDRESS$ -w $ARG1$ -c $ARG2$",
                },
            },
            'command_C_SNMP_NETWORK': {
                'type': "command",
                'file': "checkcommands/C_SNMP_NETWORK.cfg",
                'attrs': {
                    'command_name': "C_SNMP_NETWORK",
                    'command_line': "$USER1$/check_centreon_snmp_traffic2 -P 161 -v 3 -z des -x sha -y $USER3_SNMPCRYPT$ -p $USER4_SNMPPASS$ -u $USER5_SNMPUSER$ -H $HOSTADDRESS$ -n -i $ARG1$ -a 5 $ARG2$",
                },
            },
            'command_C_SNMP_PROCESS': {
                'type': "command",
                'file': "checkcommands/C_SNMP_PROCESS.cfg",
                'attrs': {
                    'command_name': "C_SNMP_PROCESS",
                    'command_line': "$USER1$/check_snmp_process.pl -H $HOSTADDRESS$ -l $USER5_SNMPUSER$ -x $USER4_SNMPPASS$ -X $USER3_SNMPCRYPT$ -L sha,des -n $ARG1$ -w $ARG2$ -c $ARG3$ -F",
                },
            },
            'command_C_SNMP_PROCESS_COMPLETE': {
                'type': "command",
                'file': "checkcommands/C_SNMP_PROCESS_COMPLETE.cfg",
                'attrs': {
                    'command_name': "C_SNMP_PROCESS_COMPLETE",
                    'command_line': "$USER1$/check_snmp_process.pl -H $HOSTADDRESS$ -l $USER5_SNMPUSER$ -x $USER4_SNMPPASS$ -X $USER3_SNMPCRYPT$ -L sha,des -n $ARG1$ -w $ARG2$ -c $ARG3$ -F -a --memory=$ARG4$ -d 300 -u $ARG5$",
                },
            },
            'command_C_SNMP_PROCESS_WITH_MEM': {
                'type': "command",
                'file': "checkcommands/C_SNMP_PROCESS_WITH_MEM.cfg",
                'attrs': {
                    'command_name': "C_SNMP_PROCESS_WITH_MEM",
                    'command_line': "$USER1$/check_snmp_process.pl -H $HOSTADDRESS$ -l $USER5_SNMPUSER$ -x $USER4_SNMPPASS$ -X $USER3_SNMPCRYPT$ -L sha,des -n $ARG1$ -w $ARG2$ -c $ARG3$ -F -a --memory=$ARG4$",
                },
            },
            'command_C_VERIFY_TCP_PORT': {
                'type': "command",
                'file': "checkcommands/C_VERIFY_TCP_PORT.cfg",
                'attrs': {
                    'command_name': "C_VERIFY_TCP_PORT",
                    'command_line': "$USER1$/check_tcp  -H $HOSTADDRESS$ -p $ARG1$",
                },
            },
            'command_EV_SSH_RELANCE_NTP': {
                'type': "command",
                'file': "checkcommands/EV_SSH_RELANCE_NTP.cfg",
                'attrs': {
                    'command_name': "EV_SSH_RELANCE_NTP",
                    'command_line': "$USER1$/eventhandlers/relance_ntp  $SERVICESTATE$ $SERVICESTATETYPE$ $SERVICEATTEMPT$ $HOSTADDRESS$ $HOSTNAME$ $SERVICEDESC$",
                },
            },
            # services templates definitions
            'serviceTemplate_ST_ROOT': {
                'type': "service",
                'file': "serviceTemplates/ST_ROOT.cfg",
                'attrs': {
                    'name': "ST_ROOT",
                    'service_description': 'S_ROOT',
                    'is_volatile': 0,
                    'max_check_attempts': 3,
                    'normal_check_interval': 5,
                    'retry_check_interval': 1,
                    'active_checks_enabled': 1,
                    'passive_checks_enabled': 1,
                    'check_period': "24x7",
                    'notification_interval': 0,
                    'notifications_enabled': 0,
                    'contact_groups': "Supervisors",
                    'register': 0,
                },
            },
            'serviceTemplate_ST_HOURLY_ALERT': {
                'type': "service",
                'file': "serviceTemplates/ST_HOURLY_ALERT.cfg",
                'attrs': {
                    'name': "ST_HOURLY_ALERT",
                    'service_description': "ST_HOURLY_ALERT",
                    'use': "ST_ROOT",
                    'max_check_attempts': 3,
                    'normal_check_interval': 60,
                    'retry_check_interval': 1,
                    'register': 0,
                },
            },
            # hosts templates definitions
            # (shouldn't use autoconfigured for templates because we can't associate a service to
            # a host template. It seems to be not working with icinga)
            'hostTemplateHT+_BACKUP_BURP': {
                'type': "host",
                'file': "hostTemplates/HT+_BACKUP_BURP.cfg",
                'attrs': {
                    'name': "HT+_BACKUP_BURP",
                    'alias': "HT+_BACKUP_BURP",
                    'register': 0,
                },
            },
            'hostTemplateHT+_PUBLIC_DNS': {
                'type': "host",
                'file': "hostTemplates/HT+_PUBLIC_DNS.cfg",
                'attrs': {
                    'name': "HT+_PUBLIC_DNS",
                    'alias': "Host avec DNS public",
                    'register': 0,
                },
            },
            'hostTemplateHT+_SNMP_Linux': {
                'type': "host",
                'file': "hostTemplates/HT+_SNMP_Linux.cfg",
                'attrs': {
                    'name': "HT+_SNMP_Linux",
                    'alias': "HT+_SNMP_Linux",
                    'register': 0,
                },
            },
            'hostTemplateHT+_WEB_INTRA': {
                'type': "host",
                'file': "hostTemplates/HT+_WEB_INTRA.cfg",
                'attrs': {
                    'name': "HT+_WEB_INTRA",
                    'alias': "HT+_WEB_INTRA",
                    'register': 0,
                },
            },
            'hostTemplateHT+_WEB_PUBLIC': {
                'type': "host",
                'file': "hostTemplates/HT+_WEB_PUBLIC.cfg",
                'attrs': {
                    'name': "HT+_WEB_PUBLIC",
                    'alias': "HT+_WEB_PUBLIC",
                    'register': 0,
                },
            },
            'hostTemplateHT_ICON_Dedibox': {
                'type': "host",
                'file': "hostTemplates/HT_ICON_Dedibox.cfg",
                'attrs': {
                    'name': "HT_ICON_Dedibox",
                    'use': "_HT_BASE",
                    'alias': "Hébergeur Dedibox pour logo",
                    'register': 0,
                    'icon_image': "heberg/dedibox.png",
                },
            },
            'hostTemplateHT_ICON_Free': {
                'type': "host",
                'file': "hostTemplates/HT_ICON_Free.cfg",
                'attrs': {
                    'name': "HT_ICON_Free",
                    'use': "_HT_BASE",
                    'alias': "Hébergeur Free pour logo",
                    'register': 0,
                    'icon_image': "heberg/news_free.gif",
                },
            },
            'hostTemplateHT_ICON_Gandi': {
                'type': "host",
                'file': "hostTemplates/HT_ICON_Gandi.cfg",
                'attrs': {
                    'name': "HT_ICON_Gandi",
                    'use': "_HT_BASE",
                    'alias': "Hébergeur Gandi pour logo",
                    'register': 0,
                    'icon_image': "heberg/gandi.png",
                },
            },
            'hostTemplateHT_ICON_ImageCrea': {
                'type': "host",
                'file': "hostTemplates/HT_ICON_ImageCrea.cfg",
                'attrs': {
                    'name': "HT_ICON_ImageCrea",
                    'use': "_HT_BASE",
                    'alias': "Hébergeur ImageCrea pour logo",
                    'register': 0,
                    'icon_image': "heberg/imagecreation.jpg",
                },
            },
            'hostTemplateHT_ICON_OVH': {
                'type': "host",
                'file': "hostTemplates/HT_ICON_OVH.cfg",
                'attrs': {
                    'name': "HT_ICON_OVH",
                    'use': "_HT_BASE",
                    'alias': "Hébergeur OVH pour logo",
                    'register': 0,
                    'icon_image': "heberg/logo_ovh.png",
                },
            },
            'hostTemplateHT_ICON_PHPNET': {
                'type': "host",
                'file': "hostTemplates/HT_ICON_PHPNET.cfg",
                'attrs': {
                    'name': "HT_ICON_PHPNET",
                    'use': "_HT_BASE",
                    'alias': "Hébergeur PHPNET pour logo",
                    'register': 0,
                    'icon_image': "heberg/phpnet.gif",
                },
            },
            'hostTemplateHT_Router': {
                'type': "host",
                'file': "hostTemplates/HT_Router.cfg",
                'attrs': {
                    'name': "HT_Router",
                    'use': "_HT_BASE",
                    'alias': "Tous les routeurs",
                    'register': 0,
                },
            },
            'hostTemplateHT_test_1': {
                'type': "host",
                'file': "hostTemplates/HT_test_1.cfg",
                'attrs': {
                    'name': "HT_test_1",
                    'use': "HT_test_2",
                    'alias': "HT_test_1",
                    'register': 0,
                },
            },
            'hostTemplateHT_test_2': {
                'type': "host",
                'file': "hostTemplates/HT_test_2.cfg",
                'attrs': {
                    'name': "HT_test_2",
                    'use': "HT_test_3",
                    'alias': "HT_test_2",
                    'register': 0,
                },
            },
            'hostTemplateHT_test_3': {
                'type': "host",
                'file': "hostTemplates/HT_test_3.cfg",
                'attrs': {
                    'name': "HT_test_3",
                    'use': "_HT_BASE",
                    'alias': "HT_test_3",
                    'register': 0,
                },
            },
            'hostTemplateHT_Xen': {
                'type': "host",
                'file': "hostTemplates/HT_Xen.cfg",
                'attrs': {
                    'name': "HT_Xen",
                    'use': "_HT_BASE",
                    'alias': "Xen server",
                    'register': 0,
                },
            },
            'hostTemplateSwitchs-Cisco': {
                'type': "host",
                'file': "hostTemplates/Switchs-Cisco.cfg",
                'attrs': {
                    'name': "Switchs-Cisco",
                    'use': "_HT_BASE",
                    'alias': "Cisco Switchs",
                    'register': 0,
                },
            },
            'hostTemplate_HT_BASE': {
                'type': "host",
                'file': "hostTemplates/_HT_BASE.cfg",
                'attrs': {
                    'name': "_HT_BASE",
                    'alias': "Base Generic Host",
                    'check_command': "check_host_alive",
                    'max_check_attempts': 5,
                    'active_checks_enabled': 1,
                    'passive_checks_enabled': 1,
                    'check_period': "24x7",
                    'contact_groups': "Supervisors",
                    'notification_interval': 0,
                    'notification_period': "24x7",
                    'notification_options': "d,r",
                    'notifications_enabled': 1,
                    'register': 0,
                    'statusmap_image': "gd2/fonc//server2.gd2",
                },
            },
        },

        # host definitions
        'autoconfigured_hosts_definitions': {
            'webservices': {
                'hostname': "webservices",
                'attrs': {
                    'host_name': "webservices",
                    'use': "HT_ICON_OVH,HT+_SNMP_Linux,HT+_PUBLIC_DNS",
                    'alias': "VIRT",
                    'address': "127.0.0.1",
                    '_HOST_ID': 78,
                    'hostgroups': "HG_ALL_HOSTS,HG_HEBERGEUR",
                },
                'ssh_user': "root",
                'ssh_addr': "127.0.0.1",
                'mountpoint_root': True,
                'check_mountpoints': True,
                'check_dns': True,
                'check_cpuload': True,
                'check_memory': True,
                'services_check_command_args': {
                    'dns': {
                        'localhost': {
                            'hostname': "www.localhost",
                        },
                        'other_name': {
                            'hostname': "www.example.net",
                        },
                        'hostname': {
                            'hostname': "webservices",
                        },
                    },
                },
            },
        },
    }
    return data


def settings():
    '''
    icinga settings

    location
        installation directory

    package
        list packages to install icinga
    has_pgsql
        install and configure a postgresql service in order to be used with ido2db module
    has_mysql
        install and configure a mysql service in order to be used with ido2db module
    user
        icinga user
    group
        icinga group
    pidfile
        file to store icinga pid
    configuration_directory
        directory where configuration files are located
    niceness
        priority of icinga process
    objects
        dictionary to configure objects

        directory
            directory in which objects will be stored. All the files in this directory are removed when salt is executed
        filescopy
            the list of programs which have to be copied in /roott/admin_scripts/nagios/
        commands_static_values
            dictionary to store values used in check_commands in configuration_add_auto_host macro
        objects_definitions
            dictionary to store objects configuration like commands, contacts, timeperiods, ...
            each subdictionary is given to configuration_add_object macros
            as \*\*kwargs parameter
        autoconfigured_hosts_definitions
            dictionary to store hosts auto configurations ;
            each subdictionary is given to configuration_add_auto_host macro as \*\*kwargs
            parameter

    icinga_cfg
        dictionary to store values of icinga.cfg configuration file
    modules
        mklivestatus
            enabled
                enable mklivestatus module. If true, mklivestatus will be
                downloaded and built.
            socket
                file through wich mklivestatus will be available
            lib_file
                location for installing the module
            download
                url
                    url to download mklivestatus
                sha512sum
                    hash to verify that the downloaded file is not corrupted


        cgi
            enabled
                enable cgi module. If true, nginx webserver 
                and uwsgi will be installed and configured
            package
                list of packages to install cgi module
            absolute_styles_dir
                absolute path of directory where css files will be moved
                (by default on ubuntu/debian icinga-cgi package stores 
                them in /etc/icinga which seems to be a bad location for 
                theses css files. /etc/ should be dedicated for 
                configuration only)
            root_account
                login
                    login for root login on cgi interface
                password
                    password for root login on cgi interface
            nginx
                dictionary to store values of nginx configuration
            
                domain
                    name of virtualhost created to serve webpages 
                    (dns will not be configured)
                doc_root
                    root location of virtualhost
                vh_content_source
                    template file for nginx content file
                vh_top_source
                    template file for nginx top file
                icinga_cgi
                    dictionary to store values used in templates given in 
                    vh_content_source and vh_top_source

                    web_directory
                        location under which webpages will be available
                    realm
                        message displayed for digest authentication
                    htpasswd_file
                        location of file storing users password
                    htdoc_dir
                        root location for web_directory
                    images_dir
                        directory where images used by cgi are stored
                    styles_dir
                        directory where css used by cgi are stored
                    cgi_dir
                        directory where cgi files are located
                    uwsgi_pass
                        socket used to contact uwsgi server
            uwsgi
                dictionary to store values of uwsgi configuration

                config_name
                    name of uwsgi configuration file
                config_file
                    template file for uwsgi configuration  file
                enabled
                    true if uwsgi configuration must be enabled
                master
                    "true" or "false"
                plugins
                    plugin used in uwsgi. with icinga we have to use the "cgi" plugin
                async
                    number of asynchronous threads used by uwsgi
                    it seems that icinga-cgi doesn't work very well when we use async (the webpages are not complete)
                ugreen
                    "true" or "false"
                threads
                    number of threads used by uwsgi
                socket
                    socket where uwsgi listen on. This value should be equal to one in 
                    uwsgi_pass
                uid
                    uwsgi user
                gid
                    uwsgi group
                cgi
                    location where cgi files are located. This value should be equal 
                    to one in cgi_dir
                cgi_allowed_ext
                    extension used by file which can be executed

            cgi_cfg
                dictionary to store values of cgi.cfg configuration file


        ido2db
            enabled
                enable ido2db module
            package
                list of packages to install ido2db module
            user
                ido2db user
            group
                ido2db group
            pidfile
                file to store ido2db pid
            icinga_socket
                dictionary to store connection parameters between icinga and ido2db module

                socket_type
                    "tcp" or "unix" socket
                name
                    host/port or pipe used for connection
                socket_perm
                    used only in unix socket for pipe chmod
                tcp_port
                    used only in tcp socket
                use_ssl
                    used only in tcp socket

           database:
               dictionary to store database connection parameters
               
               type
                   type of sgbd used "pgsql" or "mysql"
               host
                   host used for connection
               port
                   port used for connection
               user
                   user used for connection
               password
                   password used for connection
               name
                   database name
               prefix
                   prefix used in table's names

           ido2db_cfg
               dictionary to store values of ido2db.cfg configuration file
           idomod_cfg
               dictionary to store values of idomod.cfg configuration file


        nagios-plugins
            enabled
                install nagios-plugins package which provides some standards check binaries
                for icinga
            package
                list of packages to install nagios-plugins

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        icinga_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga', registry_format='pack')
        locs = __salt__['mc_locations.settings']()

        # generate default password
        icinga_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga', registry_format='pack')

        password_ido = icinga_reg.setdefault('ido.db_password'
                                        , __salt__['mc_utils.generate_password']())
        password_cgi = icinga_reg.setdefault('cgi.root_account_password'
                                        , __salt__['mc_utils.generate_password']())

        module_ido2db_database = {
            'type': "pgsql",
            'host': "localhost",
            'port': 5432,
#            'socket': "",
            'user': "icinga_ido",
            'password': password_ido,
            'name': "icinga_ido",
            'prefix': "icinga_",
        }

        has_sgbd = ((('host' in module_ido2db_database) 
                     and (module_ido2db_database['host']
                          in  [
                              'localhost', '127.0.0.1', grains['host']
                          ]))
                    or ('socket' in module_ido2db_database))

        checks_directory = "/root/admin_scripts/nagios"
        check_ping_warning = "5000,100%"
        check_ping_critical = check_ping_warning
        check_by_ssh_params="-q -l '$ARG1$' -H '$ARG2$' -p '$ARG3$' -t '$ARG4$' "

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga', {
                'package': ['icinga-core', 'icinga-common', 'icinga-doc'],
                'has_pgsql': ('pgsql' == module_ido2db_database['type']
                              and has_sgbd),
                'has_mysql': ('mysql' == module_ido2db_database['type']
                              and has_sgbd),
                'user': "nagios",
                'group': "nagios",
                'pidfile': "/var/run/icinga/icinga.pid",
                'configuration_directory': locs['conf_dir']+"/icinga",
                'niceness': 5,
                'objects': objects(),
                'icinga_cfg': {
                    'log_file': "/var/log/icinga/icinga.log",
                    'cfg_file': ["/etc/icinga/commands.cfg"],
                    'cfg_dir': ["/etc/icinga/objects/salt_generated/"
                               ,"/etc/icinga/modules"],
                    'object_cache_file': "/var/cache/icinga/objects.cache",
                    'precached_object_file': "/var/cache/icinga/objects.precache",
                    'resource_file': "/etc/icinga/resource.cfg",
                    'status_file': "/var/lib/icinga/status.dat",
                    'status_update_interval': 10,
                    'check_external_commands': 1,
                    'command_check_interval': -1,
                    'command_file': "/var/lib/icinga/rw/icinga.cmd",
                    'external_command_buffer_slots': 4096,
                    'temp_file': "/var/cache/icinga/icinga.tmp",
                    'temp_path': "/tmp",
                    'event_broker_options': -1,
                    'log_rotation_method': "d",
                    'log_archive_path': "/var/log/icinga/archives",
                    'use_daemon_log': 1,
                    'use_syslog': 1,
                    'use_syslog_local_facility': 0,
                    'syslog_local_facility': 5,
                    'log_notifications': 1,
                    'log_service_retries': 1,
                    'log_host_retries': 1,
                    'log_event_handlers': 1,
                    'log_initial_states': 0,
                    'log_current_states': 1,
                    'log_external_commands': 1,
                    'log_passive_checks': 1,
                    'log_long_plugin_output': 0,
#                   'global_host_event_handler': "",
#                   'global_service_event_handler': "",
                    'service_inter_check_delay_method': "s",
                    'max_service_check_spread': 30,
                    'service_interleave_factor': "s",
                    'host_inter_check_delay_method': "s",
                    'max_host_check_spread': 30,
                    'max_concurrent_checks': 0,
                    'check_result_reaper_frequency': 10,
                    'max_check_result_reaper_time': 30,
                    'check_result_path': "/var/lib/icinga/spool/checkresults",
                    'max_check_result_file_age': 3600,
                    'max_check_result_list_items': 0,
                    'cached_host_check_horizon': 15,
                    'cached_service_check_horizon': 15,
                    'enable_predictive_host_dependency_checks': 1,
                    'enable_predictive_service_dependency_checks': 1,
                    'soft_state_dependencies': 0,
                    'time_change_threshold': 900,
                    'auto_reschedule_checks': 0,
                    'auto_rescheduling_interval': 30,
                    'auto_rescheduling_window': 180,
                    'sleep_time': 0.25,
                    'service_check_timeout': 60,
                    'host_check_timeout': 30,
                    'event_handler_timeout': 30,
                    'notification_timeout': 30,
                    'ocsp_timeout': 5,
                    'perfdata_timeout': 5,
                    'retain_state_information': 1,
                    'state_retention_file': "/var/cache/icinga/retention.dat",
                    'sync_retention_file': "/var/cache/icinga/sync.dat",
                    'retention_update_interval': 60,
                    'use_retained_program_state': 1,
                    'dump_retained_host_service_states_to_neb': 0,
                    'use_retained_scheduling_info': 1,
                    'retained_host_attribute_mask': 0,
                    'retained_service_attribute_mask': 0,
                    'retained_process_host_attribute_mask': 0,
                    'retained_process_service_attribute_mask': 0,
                    'retained_contact_host_attribute_mask': 0,
                    'retained_contact_service_attribute_mask': 0,
                    'interval_length': 60,
                    'use_aggressive_host_checking': 0,
                    'execute_service_checks': 1,
                    'accept_passive_service_checks': 1,
                    'execute_host_checks': 1,
                    'accept_passive_host_checks': 1,
                    'enable_notifications': 1,
                    'enable_event_handlers': 1,
                    'enable_state_based_escalation_ranges': 0,
                    'process_performance_data': 0,
#                   'host_perfdata_command': "",
#                   'service_perfdata_command': "",
#                   'host_perfdata_file': "",
#                   'service_perfdata_file': "",
#                   'host_perfdata_file_template': "",
#                   'service_perfdata_file_template': "",
                    'host_perfdata_file_mode': "a",
                    'service_perfdata_file_mode': "a",
                    'host_perfdata_file_processing_interval': 0,
                    'service_perfdata_file_processing_interval': 0,
#                   'host_perfdata_file_processing_command': "",
#                   'service_perfdata_file_processing_command': "",
                    'host_perfdata_process_empty_result': 1,
                    'service_perfdata_process_empty_result': 1,
                    'allow_empty_hostgroup_assignment': 1,
                    'obsess_over_services': 0,
#                   'ocsp_command': "",
                    'obsess_over_hosts': 0,
#                   'ochp_command': "",
                    'translate_passive_host_checks': 0,
                    'passive_host_checks_are_soft': 0,
                    'check_for_orphaned_services': 1,
                    'check_for_orphaned_hosts': 1,
                    'service_check_timeout_state': "u",
                    'check_service_freshness': 1,
                    'service_freshness_check_interval': 60,
                    'check_host_freshness': 0,
                    'host_freshness_check_interval': 60,
                    'additional_freshness_latency': 15,
                    'enable_flap_detection': 1,
                    'low_service_flap_threshold': 5.0,
                    'high_service_flap_threshold': 20.0,
                    'low_host_flap_threshold': 5.0,
                    'high_host_flap_threshold': 20.0,
                    'date_format': "iso8601",
#                   'use_timezone': "",
                    'p1_file': "/usr/lib/icinga/p1.pl",
                    'enable_embedded_perl': 1,
                    'use_embedded_perl_implicitly': 1,
                    'stalking_event_handlers_for_hosts': 0,
                    'stalking_event_handlers_for_services': 0,
                    'stalking_notifications_for_hosts': 0,
                    'stalking_notifications_for_services': 0,
                    'illegal_object_name_chars': "`~!$%^&*|'\"<>?,()=': ",
                    'illegal_macro_output_chars': "`~$&|'\"<>",
                    'keep_unknown_macros': 0,
                    'use_regexp_matching': 0,
                    'use_true_regexp_matching': 0,
                    'admin_email': "root@localhost",
                    'admin_pager': "pageroot@localhost",
                    'daemon_dumps_core': 0,
                    'use_large_installation_tweaks': 0,
                    'enable_environment_macros': 0,
                    'free_child_process_memory': 1,
                    'child_processes_fork_twice': 1,
                    'debug_level': 0,
                    'debug_verbosity': 2,
                    'debug_file': "/var/log/icinga/icinga.debug",
                    'max_debug_file_size': 100000000,
                    'event_profiling_enabled': 0,
                },
                'resource_cfg': {
                    '$USER1$': "/usr/local/nagios/libexec",
                    '$USER2$': "public",
                    '$USER5_SNMPUSER': "CHANGETHIS",
                    '$USER3_SNMPCRYPT$': "CHANGETHIS",
                    '$USER4_SNMPPASS$': "CHANGETHIS",
                    '$USER6_AUTHPAIRS$': "CHANGETHIS",
                    '$USER7_SSHKEYS$': "/home/nagios/.ssh/id_rsa_supervision",
                    '$USER8_TESTUSER$': "tsa",
                    '$USER9_TESTPWD$': "CHANGETHIS"
                },
                'modules': {
                    'mklivestatus': {
                        'enabled': True,
                        'socket': "/var/lib/icinga/rw/live",
                        'lib_file': "/usr/lib/icinga/livestatus.o",
                        'download': {
                            'url': "http://mathias-kettner.de/download/mk-livestatus-1.2.4.tar.gz",
                            'sha512sum': "412215c5fbed5897e4e2f2adf44ccc340334f7138acd2002df0ae42cfe1022250b94ed76288bd6cdd7469856ad8f176674a7cce6e4998e2fd95fcd447c533192",
                        },
                    },
                    'cgi': {
                        'package': ['icinga-cgi'],
                        'enabled': True,
                        'user': "www-data",
                        'group': "www-data",
                        'root_account': {
                          'login': "icingaadmin",
                          'password': password_cgi,
                        },
                        'absolute_styles_dir': "/usr/share/icinga/htdocs/stylesheets",
                        'nginx': {
                            'domain': "icinga-cgi.localhost",
                            'doc_root': "/usr/share/icinga/htdocs/",
                            'vh_content_source': "salt://makina-states/files/etc/nginx/sites-available/icinga-cgi.content.conf",
                            'vh_top_source': "salt://makina-states/files/etc/nginx/sites-available/icinga-cgi.top.conf",
                            'icinga_cgi': {
                                'web_directory': "",
                                'realm': "Authentication",
                                'htpasswd_file': "/etc/icinga/htpasswd.users",
                                'htdocs_dir': "/usr/share/icinga/htdocs/",
                                'images_dir': "/usr/share/icinga/htdocs/images/$1",
                                'styles_dir': "/usr/share/icinga/htdocs/stylesheets/$1",
                                'cgi_dir': "/usr/lib/cgi-bin/",
                                'uwsgi_pass': "127.0.0.1:3030",
                            },
                        },
                        'uwsgi': {
                            'config_name': "icinga.ini",
                            'config_file': "salt://makina-states/files/etc/uwsgi/apps-available/icinga-cgi.ini",
                            'enabled': True,
                            'master': "true",
                            'plugins': "cgi",
                            'async': 20,
                            'ugreen': True,
                            'threads': 5,
                            'socket': "127.0.0.1:3030",
                            'uid': "www-data",
                            'gid': "www-data",
                            'cgi': "/cgi-bin/icinga/=/usr/lib/cgi-bin/icinga/",
                            'cgi_allowed_ext': ".cgi",
                        },
                        'cgi_cfg': {
                            'main_config_file': "/etc/icinga/icinga.cfg",
                            'standalone_installation': 0,
                            'physical_html_path': "/usr/share/icinga/htdocs",
                            'url_html_path': "/icinga",
                            'icinga_check_command': "/usr/lib/nagios/plugins/check_nagios /var/lib/icinga/status.dat 5 '/usr/sbin/icinga'",
                            'url_stylesheets_path': "/icinga/stylesheets",
                            'http_charset': "utf-8",
                            'refresh_rate': 90,
                            'refresh_type': 1,
                            'escape_html_tags': 1,
                            'result_limit': 50,
                            'show_tac_header': 1,
                            'use_pending_states': 1,
                            'first_day_of_week': 0,
                            'csv_delimiter': ";",
                            'csv_data_enclosure': "'",
                            'suppress_maintenance_downtime': 0,
                            'action_url_target': "main",
                            'notes_url_target': "main",
                            'authorization_config_file': "/etc/icinga/cgiauth.cfg",
                            'use_authentication': 1,
                            'use_ssl_authentication': 0,
                            'lowercase_user_name': 0,
                            'default_user_name': "guest",
                            'authorized_for_system_information': "icingaadmin",
#                            'authorized_contactgroup_for_system_information': "",
                            'authorized_for_configuration_information': "icingaadmin",
#                            'authorized_contactgroup_for_configuration_information': "",
                            'authorized_for_full_command_resolution': "icingaadmin",
#                            'authorized_contactgroup_for_full_command_resolution': "",
                            'authorized_for_system_commands': "icingaadmin",
#                            'authorized_contactgroup_for_system_commands': "",
                            'authorized_for_all_services': "icingaadmin",
                            'authorized_for_all_hosts': "icingaadmin",
#                            'authorized_contactgroup_for_all_service': "",
#                            'authorized_contactgroup_for_all_hosts': "",
                            'authorized_for_all_service_commands': "icingaadmin",
                            'authorized_for_all_host_commands': "icingaadmin",
#                            'authorized_contactgroup_for_all_service_commands': "",
#                            'authorized_contactgroup_for_all_host_commands', "",
#                            'authorized_for_read_only': "",
#                            'authorized_contactgroup_for_read_only': "",
#                            'authorized_for_comments_read_only': "",
#                            'authorized_contactgroup_for_comments_read_only': "",
#                            'authorized_for_downtimes_read_only': "",
#                            'authorized_contactgroup_for_downtimes_read_only': "",
                            'show_all_services_host_is_authorized_for': 1,
                            'show_partial_hostgroups': 0,
                            'show_partial_servicegroups': 0,
                            'statusmap_background_image': "logomakina.png",
                            'color_transparency': [255, 255, 255], 
                            'default_statusmap_layout': 5,
                            'host_unreachable_sound': "hostdown.wav",
                            'host_down_sound': "hostdown.wav",
                            'service_critical_sound': "critical.wav",
                            'service_warning_sound': "warning.wav",
                            'service_unknown_sound': "warning.wav",
                            'normal_sound': "noproblem.wav",
                            'status_show_long_plugin_output': 0,
                            'display_status_totals': 0,
                            'highlight_table_rows': 1,
                            'add_notif_num_hard': 28,
                            'add_notif_num_soft': 0,
                            'use_logging': 0,
                            'cgi_log_file': "/usr/share/icinga/htdocs/log/icinga-cgi.log",
                            'cgi_log_rotation_method': "d",
                            'cgi_log_archive_path': "/usr/share/icinga/htdocs/log",
                            'enforce_comments_on_actions': 0,
                            'send_ack_notifications': 1,
                            'persistent_ack_comments': 0,
                            'lock_author_names': 1,
                            'default_downtime_duration': 7200,
                            'set_expire_ack_by_default': 0,
                            'default_expiring_acknowledgement_duration': 86400,
                            'default_expiring_disabled_notifications_duration': 86400,
                            'tac_show_only_hard_state': 0,
                            'show_tac_header_pending': 1,
                            'exclude_customvar_name': "PASSWORD,COMMUNITY",
                            'exclude_customvar_value': "secret",
                            'extinfo_show_child_hosts': 0,
                            'tab_friendly_titles': 1,
                            'showlog_initial_states': 0,
                            'showlog_current_states': 0,
                            'enable_splunk_integration': 0,
#                            'splunk_url': "",
                            'object_cache_file': "/var/cache/icinga/objects.cache",
                            'status_file': "/var/cache/icinga/status.dat",
                            'resource_file': "/etc/icinga/resource.cfg",
                            'command_file': "/var/lib/icinga/rw/icinga.cmd",
                            'check_external_commands': 1,
                            'interval_length': 60,
                            'status_update_interval': 10,
                            'log_file': "/var/log/icinga/icinga.log",
                            'log_rotation_method': "d",
                            'log_archive_path': "/var/log/icinga/archives",
                            'date_format': "us",
                        },
                    },
                    'ido2db': {
                        'package': ['icinga-idoutils'],
                        'enabled': True,
                        'user': "nagios",
                        'group': "nagios",
                        'pidfile': "/var/run/icinga/ido2db.pid",

                        'icinga_socket': {
                            'socket_type': "unix",
                            'socket_name': "/var/lib/icinga/ido.sock",
                            'socket_perm': "0755",
                            'tcp_port': "5668",
                            'use_ssl': 0,
                        },

                        'database': module_ido2db_database,
                        'ido2db_cfg': {
#                            'libdbi_driver_dir': "",
                            'max_systemcommands_age': 1440,
                            'max_servicechecks_age': 1440,
                            'max_hostchecks_age': 1440,
                            'max_eventhandlers_age': 10080,
                            'max_externalcommands_age': 10080,
                            'max_logentries_age': 44640,
                            'max_acknowledgements_age': 44640,
                            'max_notifications_age': 44640,
                            'max_contactnotifications_age': 44640,
                            'max_contactnotificationmethods_age': 44640,
                            'max_downtimehistory_age': 44640,
                            'trim_db_interval': 3600,
                            'housekeeping_thread_startup_delay': 300,
                            'debug_level': 0,
                            'debug_verbosity': 2,
                            'debug_file': "/var/log/icinga/ido2db.debug",
                            'max_debug_file_size': 100000000,
                            'debug_readable_timestamp': 0,
                            'oci_errors_to_syslog': 1,
                            'oracle_trace_level': 0,
                        },
                        'idomod_cfg': {
                            'instance_name': "default",
                            'output_buffer_items': 5000,
                            'buffer_file': "/var/lib/icinga/idomod.tmp",
                            'file_rotation_interval': 14400,
#                           'file_rotation_command': "",
                            'file_rotation_timeout': 60,
                            'reconnect_interval': 15,
                            'reconnect_warning_interval': 15,
                            'data_processing_options': 67108669,
                            'config_output_options': 2,
                            'dump_customvar_status': 0,
                            'debug_level': 0,
                            'debug_verbosity': 2,
                            'debug_file': "/var/log/icinga/idomod.debug",
                            'max_debug_file_size': 100000000,
                        },
                    },
                    'nagios-plugins': {
                        'package': ['nagios-plugins'],
                        'enabled': False,
                    },
                },


            })

        __salt__['mc_macros.update_local_registry'](
            'icinga', icinga_reg,
            registry_format='pack')
        return data
    return _settings()

def add_configuration_object_settings(type, file, attrs, **kwargs):
    '''Settings for the add_configuration_object macro'''
    icingaSettings = copy.deepcopy(__salt__['mc_icinga.settings']())
    extra = kwargs.pop('extra', {})
    kwargs.update(extra)
    kwargs.setdefault('type', type)
    kwargs.setdefault('file', file)
    kwargs.setdefault('attrs', attrs)
    kwargs.setdefault('state_name_salt', file.replace('/', '-').replace('.', '-').replace(':', '-').replace('_', '-'))
    icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings, kwargs)
    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
    icingaSettings['data'] = copy.deepcopy(icingaSettings)
    icingaSettings['data']['extra'] = copy.deepcopy(icingaSettings)
    icingaSettings['extra'] = copy.deepcopy(icingaSettings)
    return icingaSettings

def edit_configuration_object_settings(type, file, attr, value, **kwargs):
    '''Settings for the edit_configuration_object macro'''
    icingaSettings = copy.deepcopy(__salt__['mc_icinga.settings']())
    extra = kwargs.pop('extra', {})
    kwargs.update(extra)
    kwargs.setdefault('type', type)
    kwargs.setdefault('file', file)
    kwargs.setdefault('attr', attr)
    kwargs.setdefault('value', value)
    kwargs.setdefault('state_name_salt', file.replace('/', '-').replace('.', '-').replace(':', '-').replace('_', '-'))
    icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings, kwargs)
    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
    icingaSettings['data'] = copy.deepcopy(icingaSettings)
    icingaSettings['data']['extra'] = copy.deepcopy(icingaSettings)
    icingaSettings['extra'] = copy.deepcopy(icingaSettings)
    return icingaSettings

def add_auto_configuration_host_settings(hostname,
                                        attrs,
                                        ssh_user,
                                        ssh_addr,
                                        ssh_port,
                                        ssh_timeout,
                                        check_ssh,
                                        check_dns,
                                        check_dns_reverse,
                                        check_http,
                                        check_html,
                                        html,
                                        check_ntp_peer,
                                        check_ntp_time,
                                        mountpoint_root,
                                        mountpoint_var,
                                        mountpoint_srv,
                                        mountpoint_data,
                                        mountpoint_home,
                                        mountpoint_var_makina,
                                        mountpoint_var_www,
                                        check_mountpoints,
                                        check_raid,
                                        check_md_raid,
                                        check_megaraid_sas,
                                        check_3ware_raid,
                                        check_cciss,
                                        check_drbd,
                                        check_swap,
                                        check_cpuload,
                                        check_memory,
                                        check_procs,
                                        check_cron,
                                        check_debian_packages,
                                        check_solr,
                                        check_burp_backup_age,
                                        check_rdiff,
                                        check_ddos,
                                        check_haproxy_stats,
                                        check_postfixqueue,
                                        check_postfix_mailqueue,
                                        services_check_command_args,
                                        **kwargs):
    '''Settings for the add_auto_configuration_host macro'''
    icingaSettings = copy.deepcopy(__salt__['mc_icinga.settings']())
    extra = kwargs.pop('extra', {})
    kwargs.update(extra)
    kwargs.setdefault('type', 'host')
    kwargs.setdefault('hostname', hostname)
    kwargs.setdefault('attrs', attrs)
    kwargs.setdefault('ssh_user', ssh_user)
    kwargs.setdefault('ssh_addr', ssh_addr)
    kwargs.setdefault('ssh_port', ssh_port)
    kwargs.setdefault('ssh_timeout', ssh_timeout)
    kwargs.setdefault('check_ssh', check_ssh)

    # add dns between host_name and address value (and reverse)
    dns_hostname=''
    dns_address=''
    dns_inaddr=''
    if not 'address' in attrs:
        check_dns = False
        check_dns_reverse = False

    if check_dns or check_dns_reverse:
        address_splitted = attrs['address'].split('.')
        inaddr = '.'.join(address_splitted[::-1]) # tanslate a.b.c.d in d.c.b.a
        inaddr = inaddr + '.in-addr.arpa.'

        if 'host_name' in attrs:
            dns_hostname = attrs['host_name']
        else:
            dns_hostname = hostname

        if not dns_hostname.endswith('.'):
            dns_hostname = dns_hostname+'.'

        kwargs.setdefault('dns_hostname', dns_hostname)
        dns_address = attrs['address']
        kwargs.setdefault('dns_address', attrs['address'])
        dns_inaddr = inaddr
        kwargs.setdefault('dns_inaddr', inaddr)

    kwargs.setdefault('check_dns', check_dns)
    kwargs.setdefault('check_dns_reverse', check_dns_reverse)
    kwargs.setdefault('check_http', check_http)

    # transform the list in string with "-s" before each element
    for name, check in html.items():
        if isinstance(check['expected_strings'], list):
            expected_strings = check['expected_strings']
            # to avoid quotes conflicts (doesn't avoid code injection)
            expected_strings = [ value.replace('"', '\\\\"') for value in expected_strings ]
            html[name]['expected_strings'] = '-s "'+'" -s "'.join(expected_strings)+'"'

    kwargs.setdefault('html', html)
    kwargs.setdefault('check_html', check_html)
    kwargs.setdefault('check_ntp_peer', check_ntp_peer)
    kwargs.setdefault('check_ntp_time', check_ntp_time)

    mountpoints_path = {
        'mountpoint_root': "/",
        'mountpoint_var': "/var",
        'mountpoint_srv': "/srv",
        'mountpoint_data': "/data",
        'mountpoint_home': "/home",
        'mountpoint_var_makina': "/var/makina",
        'mountpoint_var_www': "/var/www",
    }
    mountpoints = dict()
    for mountpoint, path in mountpoints_path.items():
        if eval(mountpoint):
            mountpoints[mountpoint]=path

    kwargs.setdefault('check_mountpoints', check_mountpoints)
    kwargs.setdefault('mountpoints', mountpoints)

    kwargs.setdefault('check_raid', check_raid)
    kwargs.setdefault('check_md_raid', check_md_raid)
    kwargs.setdefault('check_megaraid_sas', check_megaraid_sas)
    kwargs.setdefault('check_3ware_raid', check_3ware_raid)
    kwargs.setdefault('check_cciss', check_cciss)
    kwargs.setdefault('check_drbd', check_drbd)
    kwargs.setdefault('check_swap', check_swap)
    kwargs.setdefault('check_cpuload', check_cpuload)
    kwargs.setdefault('check_memory', check_memory)
    kwargs.setdefault('check_procs', check_procs)
    kwargs.setdefault('check_cron', check_cron)
    kwargs.setdefault('check_debian_packages', check_debian_packages)
    kwargs.setdefault('check_solr', check_solr)
    kwargs.setdefault('check_burp_backup_age', check_burp_backup_age)
    kwargs.setdefault('check_rdiff', check_rdiff)
    kwargs.setdefault('check_ddos', check_ddos)
    kwargs.setdefault('check_haproxy_stats', check_haproxy_stats)
    kwargs.setdefault('check_postfixqueue', check_postfixqueue)
    kwargs.setdefault('check_postfix_mailqueue', check_postfix_mailqueue)

    # give the default values for commands parameters values
    # the keys are the services names, not the commands names (use the service filename)
    services_check_command_default_args = {
       'ssh': {
           'hostname': ssh_addr,
           'port': ssh_port,
           'timeout': 10,
       },
       'dns': {
           'default': {
               'hostname': dns_hostname,
               'other_args': "",
           }
       },
       'dns_reverse': {
           'port': 53,
           'query_address': dns_inaddr,
           'record_type': 'PTR',
           'expected_address': dns_hostname,
           'timeout': 10,
       },
       'http': {
           'port': 80,
           'hostname': hostname,
           'ip_address': attrs['address'],
           'timeout': 10,
       },
       'html': {
           'port': 80,
           'ip_address': attrs['address'],
           'warning': 1,
           'critical': 2,
           'timeout': 8,
       },
       'ntp_peer': {
           'port': 123,
           'hostname': attrs['address'],
           'timeout': 10,
       },
       'ntp_time': {
           'port': 123,
           'hostname': "pool.ntp.org",
           'timeout': 10,
       },
       'mountpoints': {
           'default': {
#              from ST_DISK_SPACE_/
               'warning': 80,
               'critical': 90,
           },
       },
       'raid': {},
       'md_raid': {},
       'megaraid_sas': {},
       '3ware_raid': {},
       'ccis': {},
       'drbd': {},
       'swap': {
           'warning': '10%',
           'critical': '5%',
       },
       'cpuload': {
           'other_args': "",
       },
       'memory': {
           'warning': 80,
           'critical': 90,
       },
       'procs': {
           'metric': "PROCS",
           'warning': 170,
           'critical': 200,
       },
       'cron': {},
       'debian_packages': {
           'timeout': 60,
       },
       'solr': {
#           'port':
#           'hostname':
#           'warning':
#           'critical':
       },
       'burp_backup_age': {
           # ssh values should be replaced with the values concerning the backup host.
           'ssh_user': ssh_user,
           'ssh_addr': ssh_addr,
           'ssh_port': ssh_port,
           'ssh_timeout': ssh_timeout,
           'hostname': hostname,
           'directory': "/backups",
           'warning': 1560,
           'critical': 1800,
       },
       'rdiff': {
           # ssh values should be replaced with the values concerning the backup host
           'ssh_user': ssh_user,
           'ssh_addr': ssh_addr,
           'ssh_port': ssh_port,
           'ssh_timeout': ssh_timeout,
           'repository': '/backups/'+hostname,
           'transferred_warning': 1,
           'cron_period': 1,
           'warning': 24,
           'critical': 48,
       },
       'ddos': {
           'warning': 3,
           'critical': 4,
       },
       'haproxy_stats': {
           'socket': "/var/run/haproxy.sock",
       },
       'postfixqueue': {
           'warning': 50,
           'critical': 100,
       },
    }

    # override the commands parameters values

    # override dns subdictionary
    if not 'dns' in services_check_command_args:
        services_check_command_args['dns'] =  services_check_command_default_args['dns']
    else:
        for name, dns in services_check_command_args['dns'].items():
            for key, value in services_check_command_default_args['dns']['default'].items():
                if not key in dns:
                    services_check_command_args['dns'][name][key]=value

    # override mountpoints subdictionaries

    # for each mountpoint, build the dictionary:
    # priority for values
    # services_check_command_default_args['mountpoints']['default'] # default values in default dictionary
    # services_check_command_default_args['mountpoints'][mountpoint] # specific values in default dictionary
    # services_check_command_args['mountpoints']['default'] # default value in overrided dictionary
    # services_check_command_args['mountpoints'][mountpoint] # specific value in overrided dictionary
    if 'mountpoints' not in services_check_command_args:
        services_check_command_args['mountpoints'] = {}

    # we can't merge default dictionary yet because priorities will not be respected
    if 'default' not in services_check_command_args['mountpoints']:
        services_check_command_args['mountpoints']['default'] = {}

    for mountpoint, path in mountpoints_path.items():
        if not mountpoint in services_check_command_args['mountpoints']:
            services_check_command_args['mountpoints'][mountpoint] = {}

        if not mountpoint in services_check_command_default_args['mountpoints']:
            services_check_command_default_args['mountpoints'][mountpoint] = services_check_command_default_args['mountpoints']['default']

        services_check_command_args['mountpoints'][mountpoint] = dict(services_check_command_default_args['mountpoints']['default'].items()
                                                                     +services_check_command_default_args['mountpoints'][mountpoint].items())

        services_check_command_args['mountpoints'][mountpoint] = dict(services_check_command_args['mountpoints'][mountpoint].items()
                                                                     +services_check_command_args['mountpoints']['default'].items())

        services_check_command_args['mountpoints'][mountpoint] = dict(services_check_command_args['mountpoints'][mountpoint].items()
                                                                     +services_check_command_args['mountpoints'][mountpoint].items())

    # merge default dictionaries in order to allow {{mountpoints.defaults.warning}} in jinja template
    if not 'default' in services_check_command_args['mountpoints']:
        services_check_command_args['mountpoints']['default'] = services_check_command_default_args['mountpoints']['default']
    else:
        services_check_command_args['mountpoints']['default'] = dict(services_check_command_default_args['mountpoints']['default'].items() 
                                                                   + services_check_command_args['mountpoints']['default'].items())

    # override others values
    if not isinstance(services_check_command_args, dict):
        services_check_command_args = {}

    for name, command in services_check_command_default_args.items():
        if not name in ['dns', 'mountpoints']:
            if not name in services_check_command_args:
                services_check_command_args[name] = {}
            services_check_command_args[name] = dict(services_check_command_default_args[name].items() + services_check_command_args[name].items())


    kwargs.setdefault('services_check_command_args', services_check_command_args)

    kwargs.setdefault('state_name_salt', hostname.replace('/', '-').replace('.', '-').replace(':', '-').replace('_', '-'))
    icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings, kwargs)
    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
    icingaSettings['data'] = copy.deepcopy(icingaSettings)
    icingaSettings['data']['extra'] = copy.deepcopy(icingaSettings)
    icingaSettings['extra'] = copy.deepcopy(icingaSettings)
    return icingaSettings

def dump():
    return mc_states.utils.dump(__salt__,__name)

#
