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
                'icinga_cfg': {
                    'log_file': "/var/log/icinga/icinga.log",
                    'cfg_file': ["/etc/icinga/commands.cfg"],
                    'cfg_dir': ["/etc/nagios-plugins/config"
                               ,"/etc/icinga/objects/"
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
                    'enable_environment_macros': 1,
                    'free_child_process_memory': 1,
                    'child_processes_fork_twice': 1,
                    'debug_level': 0,
                    'debug_verbosity': 2,
                    'debug_file': "/var/log/icinga/icinga.debug",
                    'max_debug_file_size': 100000000,
                    'event_profiling_enabled': 0,
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
                            'statusmap_background_image': "smbackground.gd2",
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
                        'enabled': True,
                    },
                },


            })

        __salt__['mc_macros.update_local_registry'](
            'icinga', icinga_reg,
            registry_format='pack')
        return data
    return _settings()

def add_configuration_settings(objects, directory, keys_mapping, accumulated_values, **kwargs):
    '''Settings for the add_configuration macro'''
    icingaSettings = copy.deepcopy(__salt__['mc_icinga.settings']())
    extra = kwargs.pop('extra', {})
    kwargs.update(extra)

    # we add the directory for each value of files_mapping 
    directory_abs=directory
    if not directory.startswith('/'):
        directory_abs=data['configuration_directory']+'/'+directory

    # we hash objects dictionary in order to have a unique value
    # it is used for naming states
    def make_hash(o):
        if isinstance(o, (set, tuple, list)):
            return tuple([make_hash(e) for e in o])
        elif not isinstance(o, dict):
            return hash(o)
        new_o = copy.deepcopy(o)
        for k, v in new_o.items():
            new_o[k] = make_hash(v)

        return hash(tuple(frozenset(sorted(new_o.items()))))

    objects_hash = abs(make_hash(objects))

    kwargs.setdefault('objects', objects)
    kwargs.setdefault('objects_hash', objects_hash)
    kwargs.setdefault('directory', directory_abs)
    kwargs.setdefault('keys_mapping', keys_mapping)
    kwargs.setdefault('accumulated_values', accumulated_values)
    icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings, kwargs)
    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
    icingaSettings['data'] = copy.deepcopy(icingaSettings)
    icingaSettings['data']['extra'] = copy.deepcopy(icingaSettings)
    icingaSettings['extra'] = copy.deepcopy(icingaSettings)
    return icingaSettings


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
