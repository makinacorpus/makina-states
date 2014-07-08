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

def settings():
    '''
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        icinga_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga2', registry_format='pack')
        locs = __salt__['mc_locations.settings']()

        # generate default password
        icinga_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga2', registry_format='pack')

        password_ido = icinga_reg.setdefault('ido.db_password'
                                        , __salt__['mc_utils.generate_password']())
        password_cgi = icinga_reg.setdefault('cgi.root_account_password'
                                        , __salt__['mc_utils.generate_password']())

        module_ido2db_database = {
            'type': "pgsql",
            'host': "localhost",
            'port': 5432,
#            'socket': "",
            'user': "icinga2_ido",
            'password': password_ido,
            'name': "icinga2_ido",
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

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga', {
                'package': ['icinga2-bin', 'icinga2-common', 'icinga2-doc'],
                'has_pgsql': ('pgsql' == module_ido2db_database['type']
                              and has_sgbd),
                'has_mysql': ('mysql' == module_ido2db_database['type']
                              and has_sgbd),
                'user': "nagios",
                'group': "nagios",
                'pidfile': "/var/run/icinga2/icinga2.pid",
                'configuration_directory': locs['conf_dir']+"/icinga2",
                'niceness': 5,
                'objects': "",
                'icinga_conf': {
                    'include': ['"constants.conf"', '"zones.conf"', '<itl>', '<plugins>', '"features-enabled/*.conf"'],
                    'include_recursive': ['"conf.d"'],
                },
                'constants_conf': {
                    'PluginDir': "\"/usr/lib/nagios/plugins\"",
                    'ZoneName': "NodeName",
                },
                'zones_conf': {
                    'object Endpoint NodeName': {
                        'host': "NodeName",
                    },
                    'object Zone ZoneName': {
                        'endpoints': "[ NodeName ]",
                    },
                },
                'modules': {
                    'mklivestatus': {
                        'enabled': True,
                        'socket': "/var/lib/icinga/rw/live",
                        'lib_file': "/usr/lib/icinga/livestatus.o",
                    },
                    'cgi': {
                        'package': ['icinga2-classicui'],
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
                        'package': ['icinga2-ido-'+module_ido2db_database['type']],
                        'enabled': True,
                        'user': "nagios",
                        'group': "nagios",
                        'pidfile': "/var/run/icinga2/ido2db.pid",

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
    #icingaSettings['data'] = copy.deepcopy(icingaSettings)
    #icingaSettings['data']['extra'] = copy.deepcopy(icingaSettings)
    #icingaSettings['extra'] = copy.deepcopy(icingaSettings)
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
    #icingaSettings['data'] = copy.deepcopy(icingaSettings)
    #icingaSettings['data']['extra'] = copy.deepcopy(icingaSettings)
    #icingaSettings['extra'] = copy.deepcopy(icingaSettings)
    return icingaSettings

def add_auto_configuration_host_settings(hostname,
                                         hostgroup,
                                         attrs,
                                         ssh_user,
                                         ssh_addr,
                                         ssh_port,
                                         ssh_timeout,
                                         backup_burp_age,
                                         backup_rdiff,
                                         beam_process,
                                         celeryd_process,
                                         cron,
                                         ddos,
                                         debian_updates,
                                         dns_association,
                                         dns_reverse_association,
                                         disk_space,
                                         disk_space_root,
                                         disk_space_var,
                                         disk_space_srv,
                                         disk_space_data,
                                         disk_space_home,
                                         disk_space_var_makina,
                                         disk_space_var_www,
                                         drbd,
                                         epmd_process,
                                         erp_files,
                                         fail2ban,
                                         gunicorn_process,
                                         haproxy,
                                         ircbot_process,
                                         load_avg,
                                         mail_cyrus_imap_connections,
                                         mail_imap,
                                         mail_imap_ssl,
                                         mail_pop,
                                         mail_pop_ssl,
                                         mail_pop_test_account,
                                         mail_server_queues,
                                         mail_smtp,
                                         md_raid,
                                         megaraid_sas,
                                         memory,
                                         memory_hyperviseur,
                                         mysql_process,
                                         network,
                                         ntp_peers,
                                         ntp_time,
                                         only_one_nagios_running,
                                         postgres_port,
                                         postgres_process,
                                         prebill_sending,
                                         raid,
                                         sas,
                                         snmpd_memory_control,
                                         solr,
                                         ssh,
                                         supervisord_status,
                                         swap,
                                         tiles_generator_access,
                                         ware_raid,
                                         web_apache_status,
                                         web_openid,
                                         web,
                                         services_check_command_args,
                                         **kwargs):
    '''Settings for the add_auto_configuration_host macro'''
    icingaSettings = copy.deepcopy(__salt__['mc_icinga.settings']())
    extra = kwargs.pop('extra', {})
    kwargs.update(extra)
    kwargs.setdefault('type', 'host')
    kwargs.setdefault('hostname', hostname)
    kwargs.setdefault('hostgroup', hostgroup)

    if hostgroup:
        kwargs.setdefault('type', 'hostgroup')
        kwargs.setdefault('service_key_hostname', 'hostgroup_name')
        kwargs.setdefault('service_subdirectory', 'hostgroups')
    else:
        kwargs.setdefault('type', 'host')
        kwargs.setdefault('service_key_hostname', 'host_name')
        kwargs.setdefault('service_subdirectory', 'hosts')

    kwargs.setdefault('attrs', attrs)
    kwargs.setdefault('ssh_user', ssh_user)
    if ssh_addr:
       kwargs.setdefault('ssh_addr', ssh_addr)
    else:
       kwargs.setdefault('ssh_addr', hostname)
    kwargs.setdefault('ssh_port', ssh_port)
    kwargs.setdefault('ssh_timeout', ssh_timeout)




    kwargs.setdefault('backup_burp_age', backup_burp_age)
    kwargs.setdefault('backup_rdiff', backup_rdiff)
    kwargs.setdefault('beam_process', beam_process)
    kwargs.setdefault('celeryd_process', celeryd_process)
    kwargs.setdefault('cron', cron)
    kwargs.setdefault('ddos', ddos)
    kwargs.setdefault('debian_updates', debian_updates)
    kwargs.setdefault('dns_association', dns_association)
    kwargs.setdefault('dns_reverse_association', dns_reverse_association)
    kwargs.setdefault('disk_space', disk_space)
    kwargs.setdefault('drbd', drbd)
    kwargs.setdefault('epmd_process', epmd_process)
    kwargs.setdefault('erp_files', erp_files)
    kwargs.setdefault('fail2ban', fail2ban)
    kwargs.setdefault('gunicorn_process', gunicorn_process)
    kwargs.setdefault('haproxy', haproxy)
    kwargs.setdefault('ircbot_process', ircbot_process)
    kwargs.setdefault('load_avg', load_avg)
    kwargs.setdefault('mail_cyrus_imap_connections', mail_cyrus_imap_connections)
    kwargs.setdefault('mail_imap', mail_imap)
    kwargs.setdefault('mail_imap_ssl', mail_imap_ssl)
    kwargs.setdefault('mail_pop', mail_pop)
    kwargs.setdefault('mail_pop_ssl', mail_pop_ssl)
    kwargs.setdefault('mail_pop_test_account', mail_pop_test_account)
    kwargs.setdefault('mail_server_queues', mail_server_queues)
    kwargs.setdefault('mail_smtp', mail_smtp)
    kwargs.setdefault('md_raid', md_raid)
    kwargs.setdefault('megaraid_sas', megaraid_sas)
    kwargs.setdefault('memory', memory)
    kwargs.setdefault('memory_hyperviseur', memory_hyperviseur)
    kwargs.setdefault('mysql_process', mysql_process)
    kwargs.setdefault('network', network)
    kwargs.setdefault('ntp_peers', ntp_peers)
    kwargs.setdefault('ntp_time', ntp_time)
    kwargs.setdefault('only_one_nagios_running', only_one_nagios_running)
    kwargs.setdefault('postgres_port', postgres_port)
    kwargs.setdefault('postgres_process', postgres_process)
    kwargs.setdefault('prebill_sending', prebill_sending)
    kwargs.setdefault('raid', raid)
    kwargs.setdefault('sas', sas)
    kwargs.setdefault('snmpd_memory_control', snmpd_memory_control)
    kwargs.setdefault('solr', solr)
    kwargs.setdefault('ssh', ssh)
    kwargs.setdefault('supervisord_status', supervisord_status)
    kwargs.setdefault('swap', swap)
    kwargs.setdefault('tiles_generator_access', tiles_generator_access)
    kwargs.setdefault('ware_raid', ware_raid)
    kwargs.setdefault('web_apache_status', web_apache_status)
    kwargs.setdefault('web_openid', web_openid)
    kwargs.setdefault('web', web)

    # default values for dns_association service
    dns_hostname=''
    dns_address=''

    if dns_association or dns_reverse and 'address' in attrs and 'host_name' in attrs:
        if 'host_name' in attrs:
            dns_hostname = attrs['host_name']
        else:
            dns_hostname = hostname

        if not dns_hostname.endswith('.'):
            dns_hostname = dns_hostname+'.'

        dns_address = attrs['address']

    # values for disk_space service
    mountpoints_path = {
        'disk_space_root': "/",
        'disk_space_var': "/var",
        'disk_space_srv': "/srv",
        'disk_space_data': "/data",
        'disk_space_home': "/home",
        'disk_space_var_makina': "/var/makina",
        'disk_space_var_www': "/var/www",
    }
    disks_spaces = dict()
    for mountpoint, path in mountpoints_path.items():
        if eval(mountpoint):
            disks_spaces[mountpoint]=path

    kwargs.setdefault('disks_spaces', disks_spaces)


    # give the default values for commands parameters values
    # the keys are the services names, not the commands names (use the service filename)
    services_check_command_default_args = {
       'backup_burp_age': {
           'ssh_user': "root",
           'ssh_addr': "backup.makina-corpus.net",
           'ssh_port': "22",
           'ssh_timeout': 10,
           'warning': 1560,
           'critical': 1800,
       },
       'backup_rdiff': {
           'ssh_user': "root",
           'ssh_addr': "backup.makina-corpus.net",
           'ssh_port': "22",
           'ssh_timeout': 10,
           'command': "/root/admin_scripts/nagios/check_rdiff -r /data/backups/phpnet6 -w 24 -c 48 -l 2048 -p 24"
       },
       'beam_process': {
           'process': "beam",
           'warning': 0,
           'critical': 0,
       },
       'celeryd_process': {
           'process': "python",
           'warning': 1,
           'critical': 0,
       },
       'cron': {},
       'ddos': {
           'warning': 50,
           'critical': 60,
       },
       'debian_updates': {},
       'dns_association': {
           'default': {
               'hostname': dns_hostname,
               'dns_address': dns_address,
               'other_args': "",
           }
       },
       'disk_space': {
           'default': {
               'warning': 80,
               'critical': 90,
           },
       },
       'drbd': {
           'command': "'/root/admin_scripts/nagios/check_drbd -d  0,1'",
       },
       'epmd_process': {
           'process': "epmd",
           'warning': 0,
           'critical': 0,
       },
       'erp_files': {
           'command': "/var/makina/alma-job/job/supervision/check_erp_files.sh",
       },
       'fail2ban': {
           'process': "fail2ban-server",
           'warning': 0,
           'critical': 0,
       },
       'gunicorn_process': {
           'process': "gunicorn_django",
           'warning': 0,
           'critical': 0,
       },
       'haproxy': {
           'command': "/root/admin_scripts/nagios/check_haproxy_stats.pl -p web -w 80 -c 90",
       },
       'ircbot_process': {},
       'load_avg': {
           'other_args': "",
       },
       'mail_cyrus_imap_connections': {
           'warning': 300,
           'critical': 900,
       },
       'mail_imap': {
           'warning': 1,
           'critical': 3,
       },
       'mail_imap_ssl': {
           'warning': 1,
           'critical': 3,
       },
       'mail_pop': {
           'warning': 1,
           'critical': 3,
       },
       'mail_pop_ssl': {
           'warning': 1,
           'critical': 3,
       },
       'mail_pop_test_account': {
           'warning1': 52488,
           'critical1': 1048576,
           'warning2': 100,
           'critical2': 2000,
           'mx': "@makina-corpus.com",
       },
       'mail_server_queues': {
           'warning': 50,
           'critical': 100,
       },
       'mail_smtp': {
           'warning': 1,
           'critical': 3,
       },
       'md_raid': {
           'command': "/root/admin_scripts/nagios/check_md_raid",
       },
       'megaraid_sas': {
           'command': "/root/admin_scripts/nagios/check_megaraid_sas",
       },
       'memory': {
           'warning': 80,
           'critical': 90,
       },
       'memory_hyperviseur': {
           'warning': 95,
           'critical': 99,
       },
       'mysql_process': {
           'process': "mysql",
           'warning': 0,
           'critical': 0,
       },
       'network': {
           'default': {
               'interface': "eth0",
               'other_args': "",
           },
       },
       'ntp_peers': {},
       'ntp_time': {},
       'only_one_nagios_running': {},
       'postgres_port': {
           'port': 5432,
           'warning': 2,
           'critical': 8,
       },
       'postgres_process': {
           'process': "postgres",
           'warning': 0,
           'critical': 0,
       },
       'prebill_sending': {
           'command': "/var/makina/alma-job/job/supervision/check_prebill_sending.sh",
       },
       'raid': {
           'command': "'/root/admin_scripts/nagios/check_md_raid'",
       },
       'sas': {
           'command': "/root/admin_scripts/check_nagios/check_sas2ircu/check_sas2ircu",
       },
       'snmpd_memory_control': {
           'process': "snmpd",
           'warning': "0,1",
           'critical': "0,1",
           'memory': "256,512",
       },
       'solr': {
           'default': {
               'hostname': "h",
               'port': 80,
               'url': "/",
               'warning': 1,
               'critical': 5,
               'timeout': 8,
               'strings': [],
               'other_args': "",
           },
       },
       'ssh': {
           'port': 22,
           'warning': 1,
           'critical': 4,
       },
       'supervisord_status': {
           'command': "/home/zope/adria/rcse/production-2014-01-23-14-27-01/bin/supervisorctl",
       },
       'swap': {
           'command': "'/root/admin_scripts/nagios/check_swap -w 80%% -c 50%%'",
       },
       'tiles_generator_access': {
           'hostname': "vdm.makina-corpus.net",
           'url': "/vdm-tiles/status/",
       },
       'ware_raid': {
           'command': "/root/admin_scripts/nagios/check_3ware_raid",
       },
       'web_apache_status': {
           'warning': 4,
           'critical': 2,
           'other_args': "",
       },
       'web_openid': {
           'default': {
               'hostname': hostname,
               'url': "/",
               'warning': 1,
               'critical': 5,
               'timeout': 8,
           },
       },
       'web': {
           'default': {
               'hostname': hostname,
               'url': "/",
               'warning': 2,
               'critical': 3,
               'timeout': 8,
               'strings': [],
               'use_type': "_PUBLIC",
               'authentication': False,
               'only': False,
               'ssl': False,
               'other_args': "",
           },
       },

    }

    # override the commands parameters values

    # override dns_association subdictionary
    if not 'dns_association' in services_check_command_args:
        services_check_command_args['dns_association'] =  services_check_command_default_args['dns_association']
    else:
        for name, dns in services_check_command_args['dns_association'].items():
            for key, value in services_check_command_default_args['dns_association']['default'].items():
                if not key in dns:
                    services_check_command_args['dns_association'][name][key]=value
            address_splitted = dns['hostname'].split('.')
            inaddr = '.'.join(address_splitted[::-1]) # tanslate a.b.c.d in d.c.b.a
            inaddr = inaddr + '.in-addr.arpa.'
            services_check_command_args['dns_association'][name]['inaddr']=inaddr


    # override network subdictionary
    if not 'network' in services_check_command_args:
        services_check_command_args['network'] =  services_check_command_default_args['network']
    else:
        for name, network in services_check_command_args['network'].items():
            for key, value in services_check_command_default_args['network']['default'].items():
                if not key in network:
                    services_check_command_args['network'][name][key]=value

    # override solr subdictionary
    if not 'solr' in services_check_command_args:
        services_check_command_args['solr'] =  services_check_command_default_args['solr']
    else:
        for name, solr in services_check_command_args['solr'].items():
            for key, value in services_check_command_default_args['solr']['default'].items():
                if not key in solr:
                    services_check_command_args['solr'][name][key]=value
            # transform list of values in string ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_check_command_args['solr'][name]['strings'], list):
                str_list = services_check_command_args['solr'][name]['strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [ value.replace('"', '\\\\"') for value in str_list ]
                services_check_command_args['solr'][name]['strings']='"'+'" -s "'.join(str_list)+'"'

    # override web_openid subdictionary
    if not 'web_openid' in services_check_command_args:
        services_check_command_args['web_openid'] =  services_check_command_default_args['web_openid']
    else:
        for name, web_openid in services_check_command_args['web_openid'].items():
            for key, value in services_check_command_default_args['web_openid']['default'].items():
                if not key in web_openid:
                    services_check_command_args['web_openid'][name][key]=value

    # override web subdictionary
    if not 'web' in services_check_command_args:
        services_check_command_args['web'] =  services_check_command_default_args['web']
    else:
        for name, web in services_check_command_args['web'].items():
            for key, value in services_check_command_default_args['web']['default'].items():
                if not key in web:
                    services_check_command_args['web'][name][key]=value
            # transform list of values in string ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_check_command_args['web'][name]['strings'], list):
                str_list = services_check_command_args['web'][name]['strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [ value.replace('"', '\\\\"') for value in str_list ]
                services_check_command_args['web'][name]['strings']='"'+'" -s "'.join(str_list)+'"'

            # build the command
            if services_check_command_args['web'][name]['ssl']:
                cmd = "C_HTTPS_STRING"
            else:
                cmd = "C_HTTP_STRING"
            if services_check_command_args['web'][name]['authentication']:
                cmd = cmd + "_AUTH"
            if services_check_command_args['web'][name]['only']:
                cmd = cmd + "_ONLY"

            services_check_command_args['web'][name]['command'] = cmd

    # override mountpoints subdictionaries


    # for each disk_space, build the dictionary:
    # priority for values
    # services_check_command_default_args['disk_space']['default'] # default values in default dictionary
    # services_check_command_default_args['disk_space'][mountpoint] # specific values in default dictionary
    # services_check_command_args['disk_space']['default'] # default value in overrided dictionary
    # services_check_command_args['disk_space'][mountpoint] # specific value in overrided dictionary
    if 'disk_space' not in services_check_command_args:
        services_check_command_args['disk_space'] = {}
    # we can't merge default dictionary yet because priorities will not be respected
    if 'default' not in services_check_command_args['disk_space']:
        services_check_command_args['disk_space']['default'] = {}

    for mountpoint, path in mountpoints_path.items():
        if not mountpoint in services_check_command_args['disk_space']:
            services_check_command_args['disk_space'][mountpoint] = {}

        if not mountpoint in services_check_command_default_args['disk_space']:
            services_check_command_default_args['disk_space'][mountpoint] = services_check_command_default_args['disk_space']['default']

        services_check_command_args['disk_space'][mountpoint] = dict(services_check_command_default_args['disk_space']['default'].items()
                                                                     +services_check_command_default_args['disk_space'][mountpoint].items())

        services_check_command_args['disk_space'][mountpoint] = dict(services_check_command_args['disk_space'][mountpoint].items()
                                                                     +services_check_command_args['disk_space']['default'].items())

        services_check_command_args['disk_space'][mountpoint] = dict(services_check_command_args['disk_space'][mountpoint].items()
                                                                     +services_check_command_args['disk_space'][mountpoint].items())

    # merge default dictionaries in order to allow {{mountpoints.defaults.warning}} in jinja template
    if not 'default' in services_check_command_args['disk_space']:
        services_check_command_args['disk_space']['default'] = services_check_command_default_args['disk_space']['default']
    else:
        services_check_command_args['disk_space']['default'] = dict(services_check_command_default_args['disk_space']['default'].items() 
                                                                   + services_check_command_args['disk_space']['default'].items())

    # override others values (type are string or int)
    if not isinstance(services_check_command_args, dict):
        services_check_command_args = {}

    for name, command in services_check_command_default_args.items():
        if not name in ['dns_association', 'mountpoints', 'network', 'solr', 'web_openid', 'web']:
            if not name in services_check_command_args:
                services_check_command_args[name] = {}
            services_check_command_args[name] = dict(services_check_command_default_args[name].items() + services_check_command_args[name].items())


    kwargs.setdefault('services_check_command_args', services_check_command_args)

    kwargs.setdefault('state_name_salt', hostname.replace('/', '-').replace('.', '-').replace(':', '-').replace('_', '-'))
    icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings, kwargs)
    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
    #icingaSettings['data'] = copy.deepcopy(icingaSettings)
    #icingaSettings['data']['extra'] = copy.deepcopy(icingaSettings)
    #icingaSettings['extra'] = copy.deepcopy(icingaSettings)
    return icingaSettings

def dump():
    return mc_states.utils.dump(__salt__,__name)

#
