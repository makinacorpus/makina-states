# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga:

mc_icinga / icinga functions
============================

The first level of subdictionaries is for distinguish configuration
files. There is one subdictionary per configuration file.
The key used for subdictionary correspond
to the name of the file but the "." is replaced with a "_"

The subdictionary "modules" contains a subsubdictionary for each module.
In each module subdictionary, there is a subdictionary per file.
The key "enabled" in each module dictionary is for enabling or
disabling the module.

The "nginx" and "uwsgi" sub-dictionaries are given to macros
in \*\*kwargs parameter.

The key "package" is for listing packages installed between pre-install
and post-install hooks

The keys "has_pgsql" and "has_mysql" determine if a local postgresql
or mysql instance must be installed.
The default value is computed from default database parameters
If the connection is made through a unix pipe or with the localhost
hostname, the booleans are set to True.

'''

# Import python libs
import logging
import copy
import mc_states.api


__name = 'icinga'

log = logging.getLogger(__name__)


def objects():
    '''
    icinga objects settings

    this dictionary is the subdictionary of icinga.settings.objects
    but because of it is too big, we can't put it in the cache

    dictionary to configure objects
        directory
            directory in which objects will be stored.
            All the files in this directory are removed
            when salt is executed
        objects_definitions
            dictionary to store objects configuration like commands,
            contacts, timeperiods, ...
            each subdictionary is given to configuration_add_object macro
            as \*\*kwargs parameter
        purge_definitions
            list of files which will be deleted. It is used to delete a host
            or specific service the file paths are given relative to directory
            specified above (in the "directory" key) each element in the
            list is given to configuration_remove_object macro
            as \*\*kwargs parameter
        autoconfigured_hosts_definitions
            dictionary to store hosts auto configurations ;
            each subdictionary is given to configuration_add_auto_host
            macro as \*\*kwargs parameter


    '''
    locs = __salt__['mc_locations.settings']()
    data = __salt__['mc_pillar.yaml_load']('/srv/pillar/icinga.sls')
    if not data or not isinstance(data, dict):
        data = {}
    if 'objects_definitions' not in data:
        data['objects_definitions'] = {}
    if 'purge_definitions' not in data:
        data['purge_definitions'] = []
    if 'autoconfigured_hosts_definitions' not in data:
        data['autoconfigured_hosts_definitions'] = {}
    return data


def get_settings_for_object(target=None, obj=None, attr=None):
    '''
    expand the subdictionaries which are not cached
    in mc_icinga.settings.objects
    '''
    if 'purge_definitions' == target:
        res = objects()[target]
    else:
        res = objects()[target][obj]
        if attr:
            res = res[attr]
    return res


def settings():
    print('call settings')
    '''
    icinga settings

    location
        installation directory

    package
        list packages to install icinga
    has_pgsql
        install and configure a postgresql service in order to be used
        with ido2db module
    has_mysql
        install and configure a mysql service in order to be used with
        ido2db module
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
            directory in which objects will be stored.
        objects_definitions
            dictionary to store objects configuration like commands,
            contacts, timeperiods, ...
            each subdictionary is given to configuration_add_object
            macros as \*\*kwargs parameter
        autoconfigured_hosts_definitions
            dictionary to store hosts auto configurations ;
            each subdictionary is given to configuration_add_auto_host
            macro as \*\*kwargs parameter

    icinga_cfg
        dictionary to store values of icinga.cfg configuration file
    modules
        mklivestatus
            enabled
                enable mklivestatus module. If true, mklivestatus will
                be downloaded and built.
            socket
                file through wich mklivestatus will be available
            lib_file
                location for installing the module
            download
                url
                    url to download mklivestatus
                sha512sum
                    hash to verify that the downloaded file is not
                    corrupted


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
                domain name of virtualhost created to serve webpages
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
                    plugin used in uwsgi. with icinga we have to use the
                    "cgi" plugin
                async
                    number of asynchronous threads used by uwsgi
                    it seems that icinga-cgi doesn't work very well when
                    we use async (the webpages are not complete)
                ugreen
                    "true" or "false"
                threads
                    number of threads used by uwsgi
                socket
                    socket where uwsgi listen on. This value should be
                    equal to one in uwsgi_pass
                uid
                    uwsgi user
                gid
                    uwsgi group
                cgi
                    location where cgi files are located. This value
                    should be equal to one in cgi_dir
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
                dictionary to store connection parameters between
                icinga and ido2db module

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
               dictionary to store values of ido2db.cfg configuration
               file
           idomod_cfg
               dictionary to store values of idomod.cfg configuration
               file

        nagios-plugins
            enabled
                install nagios-plugins package which provides some
                standards check binaries
                for icinga
            package
                list of packages to install nagios-plugins

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        if grains["osrelease"] < "22.04":
            np = 'nagios-plugins'
        else:
            np = 'monitoring-plugins'
        icinga_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga', registry_format='pack')
        locs = __salt__['mc_locations.settings']()

        # do not store in cache
        # registry the whole conf, memory would explode
        # keep only the list of keys for each subdictionary
        # get_settings_for_object is the function to retrieve
        # a non cached subdictionary
        dict_objects = objects()
        dict_objects['objects_definitions'] = dict_objects[
            'objects_definitions'].keys()
        dict_objects['purge_definitions'] = []
        dict_objects['autoconfigured_hosts_definitions'] = dict_objects[
            'autoconfigured_hosts_definitions'].keys()

        # generate default password
        icinga_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga', registry_format='pack')

        password_ido = icinga_reg.setdefault('ido.db_password', __salt__[
            'mc_utils.generate_password']())
        password_cgi = icinga_reg.setdefault('cgi.root_account_password',
                                             __salt__[
                                                 'mc_utils.generate_password'
                                             ]())

        module_ido2db_database = {
            'type': "pgsql",
            'host': "localhost",
            'port': 5432,
            # 'socket': "",
            'user': "icinga_ido",
            'password': password_ido,
            'name': "icinga_ido",
            'prefix': "icinga_",
        }

        has_sgbd = ((('host' in module_ido2db_database)
                     and (module_ido2db_database['host']
                          in [
                              'localhost', '127.0.0.1', grains['host']]))
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
                # because the subdictionary is very big, we take it
                # from another function but we can copy/paste it here
                'objects': dict_objects,
                'icinga_cfg': {
                    'log_file': "/var/log/icinga/icinga.log",
                    'cfg_file': ["/etc/icinga/commands.cfg"],
                    'cfg_dir': ["/etc/icinga/objects/salt_generated/",
                                "/etc/icinga/modules"],
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
                    # 'global_host_event_handler': "",
                    # 'global_service_event_handler': "",
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
                    # 'host_perfdata_command': "",
                    # 'service_perfdata_command': "",
                    # 'host_perfdata_file': "",
                    # 'service_perfdata_file': "",
                    # 'host_perfdata_file_template': "",
                    # 'service_perfdata_file_template': "",
                    'host_perfdata_file_mode': "a",
                    'service_perfdata_file_mode': "a",
                    'host_perfdata_file_processing_interval': 0,
                    'service_perfdata_file_processing_interval': 0,
                    # 'host_perfdata_file_processing_command': "",
                    # 'service_perfdata_file_processing_command': "",
                    'host_perfdata_process_empty_result': 1,
                    'service_perfdata_process_empty_result': 1,
                    'allow_empty_hostgroup_assignment': 1,
                    'obsess_over_services': 0,
                    # 'ocsp_command': "",
                    'obsess_over_hosts': 0,
                    # 'ochp_command': "",
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
                    # 'use_timezone': "",
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
                    # for pnp4nagios
                    'broker': {
                        'enabled': True,
                        'icinga_cfg': {
                            'content': [
                                "process_performance_data=1",
                                ("broker_module=/usr/lib/pnp4nagios/npcdmod.o "
                                 "config_file=/etc/pnp4nagios/npcd.cfg"),
                            ]
                        }
                    },
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
                            'vh_content_source': "salt://makina-states/files/etc/nginx/includes/icinga-cgi.content.conf",
                            'vh_top_source': "salt://makina-states/files/etc/nginx/includes/icinga-cgi.top.conf",
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
                            # 'authorized_contactgroup_for_system_information': "",
                            'authorized_for_configuration_information': "icingaadmin",
                            # 'authorized_contactgroup_for_configuration_information': "",
                            'authorized_for_full_command_resolution': "icingaadmin",
                            # 'authorized_contactgroup_for_full_command_resolution': "",
                            'authorized_for_system_commands': "icingaadmin",
                            # 'authorized_contactgroup_for_system_commands': "",
                            'authorized_for_all_services': "icingaadmin",
                            'authorized_for_all_hosts': "icingaadmin",
                            # 'authorized_contactgroup_for_all_service': "",
                            # 'authorized_contactgroup_for_all_hosts': "",
                            'authorized_for_all_service_commands': "icingaadmin",
                            'authorized_for_all_host_commands': "icingaadmin",
                            # 'authorized_contactgroup_for_all_service_commands': "",
                            # 'authorized_contactgroup_for_all_host_commands', "",
                            # 'authorized_for_read_only': "",
                            # 'authorized_contactgroup_for_read_only': "",
                            # 'authorized_for_comments_read_only': "",
                            # 'authorized_contactgroup_for_comments_read_only': "",
                            # 'authorized_for_downtimes_read_only': "",
                            # 'authorized_contactgroup_for_downtimes_read_only': "",
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
                            # 'splunk_url': "",
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
                            # 'libdbi_driver_dir': "",
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
                            # 'file_rotation_command': "",
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
                        'package': [np],
                        'enabled': False,
                    },
                },


            })

        __salt__['mc_macros.update_local_registry'](
            'icinga', icinga_reg,
            registry_format='pack')
        return data

    print('end call settings')
    return _settings()


def replace_chars(s):
    res = s
    for char in list('/.:_'):
        res = res.replace(char, '-')
    return res


def add_configuration_object(filen=None,
                             typen=None,
                             attrs=None,
                             definition=None,
                             fromsettings=None,
                             get=False,
                             get_objects_file=None,
                             **kwargs):
    print('call add_configuration_object')
    '''Add the object file in the file's list to be added'''
    if get:
        if get_objects_file:
            return add_configuration_object.objects[get_objects_file]
        else:
            return add_configuration_object.objects
    elif typen and filen and attrs:
        if filen not in add_configuration_object.objects:
            add_configuration_object.objects[filen] = []
        add_configuration_object.objects[filen].append({
            'type': typen,
            'attrs': attrs,
            'definition': definition
        })
    elif fromsettings:
        if filen not in add_configuration_object.objects:
            add_configuration_object.objects[filen] = []
        add_configuration_object.objects[filen].append(
            {'fromsettings': fromsettings})
    print('end call add_configuration_object')


# global variable initialisation
add_configuration_object.objects = {}


def remove_configuration_object(filen=None, get=False, **kwargs):
    '''Add the file in the file's list to be removed'''
    if get:
        return remove_configuration_object.files
    elif filen:
        icingaSettings_complete = __salt__['mc_icinga.settings']()
        # append " \"file\"" to the global variable
        filename = '/'.join([icingaSettings_complete[
            'objects']['directory'], filen])
        # it doesn't avoid injection, just allow the '"' char in filename
        filename = filename.replace('"', '\"')
        remove_configuration_object.files += " \""+filename+"\""

# global variable initialisation
remove_configuration_object.files = ""


def edit_configuration_object_settings(filen,
                                       attr,
                                       value,
                                       auto_host,
                                       definition,
                                       **kwargs):
    '''Settings for edit_configuration_object macro'''
    # icingaSettings = copy.deepcopy(__salt__['mc_icinga.settings']())
    # save the ram (we get only useful values)
    icingaSettings_complete = __salt__['mc_icinga.settings']()
    icingaSettings = {}
    kwargs.setdefault('objects', {
        'directory': icingaSettings_complete['objects']['directory']
    })

    kwargs.setdefault('file', filen)
    kwargs.setdefault('attr', attr)
    kwargs.setdefault('value', value)
    kwargs.setdefault('auto_host', auto_host)
    kwargs.setdefault('definition', definition)

    kwargs.setdefault('state_name_salt', replace_chars(filen))

    icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings, kwargs)
    return icingaSettings


def add_auto_configuration_host_settings(hostname,
                                         hostgroup=False,
                                         attrs={},
                                         ssh_username='root',
                                         ssh_addr='',
                                         ssh_port=22,
                                         ssh_timeout=30,
                                         backup_burp_age=False,
                                         backup_rdiff=False,
                                         beam_process=False,
                                         celeryd_process=False,
                                         cron=False,
                                         ddos=False,
                                         debian_updates=False,
                                         dns_association_hostname=False,
                                         dns_association=False,
                                         dns_reverse_association=False,
                                         disk_space=False,
                                         disk_space_root=False,
                                         disk_space_var=False,
                                         disk_space_srv=False,
                                         disk_space_tmp=False,
                                         disk_space_data=False,
                                         disk_space_mnt_data=False,
                                         disk_space_home=False,
                                         disk_space_var_lxc=False,
                                         disk_space_var_makina=False,
                                         disk_space_var_mysql=False,
                                         disk_space_var_www=False,
                                         disk_space_backups=False,
                                         disk_space_backups_guidtz=False,
                                         disk_space_var_backups_bluemind=False,
                                         disk_space_var_spool_cyrus=False,
                                         disk_space_nmd_www=False,
                                         drbd=False,
                                         epmd_process=False,
                                         erp_files=False,
                                         fail2ban=False,
                                         gunicorn_process=False,
                                         haproxy=False,
                                         ircbot_process=False,
                                         load_avg=False,
                                         mail_cyrus_imap_connections=False,
                                         mail_imap=False,
                                         mail_imap_ssl=False,
                                         mail_pop=False,
                                         mail_pop_ssl=False,
                                         mail_pop_test_account=False,
                                         mail_server_queues=False,
                                         mail_smtp=False,
                                         megaraid_sas=False,
                                         memory=False,
                                         memory_hyperviseur=False,
                                         mysql_process=False,
                                         network=False,
                                         ntp_peers=False,
                                         ntp_time=False,
                                         only_one_nagios_running=False,
                                         postgres_port=False,
                                         postgres_process=False,
                                         prebill_sending=False,
                                         raid=False,
                                         sas=False,
                                         snmpd_memory_control=False,
                                         solr=False,
                                         ssh=False,
                                         supervisord_status=False,
                                         swap=False,
                                         tiles_generator_access=False,
                                         ware_raid=False,
                                         web_apache_status=False,
                                         web_openid=False,
                                         web=False,
                                         services_attrs={},
                                         **kwargs):
    print('call add_auto_configuration_host_settings')
    '''Settings for add_auto_configuration_host macro

       The dictionaries and lists used are:
            services
                list of services (the name are the same as arguments)
            services_loop
                list of services that can be defined several times
            mountpoints_path:
                dictionary to association disk_space argument with the
                system path
            services_default_attrs
                dictionary with the same structure as services_attrs
                containing the default
                values for each service
            check_command_args
                dictionary in which, each key corresponds to a check
                command and each value is the list of arguments
                (the arguments are taken in services_attrs dictionary)

        The function build two dictionaries "services_enabled" and
        "services_loop_enabled" in which
        each key corresponds to a service and each value is True or
        False, whever the service is enabled or not

        Then the function merges the two dictionaries:
        "services_default_attrs" with the "services_attrs".
        The missing values in "services_attrs" dictionary are taken from
        "services_default_attrs" dictionary.

        Then, the "check_command" values are build in "services_attrs"
        dictionary.
        The arguments (values associated to a "cmdarg\_" key) are
        added next to the command

        Finally, "host_name" or "hostgroup_name" key is added for each
        services of "services_attrs" dictionary
        and the "cmdarg\_" keys are removed.

        Only the arguments for CSSH (ssh_username, ssh_addr,
        ssh_port and ssh_timeout) don't begin with "cmdarg\_"
    '''
#    icingaSettings = copy.deepcopy(__salt__['mc_icinga.settings']())
#   save the ram (get only useful values)
    icingaSettings_complete = __salt__['mc_icinga.settings']()
    icingaSettings = {}
    kwargs.setdefault('objects', {
                      'directory': icingaSettings_complete[
                          'objects']['directory']
                      })

    kwargs.setdefault('hostname', hostname)
    kwargs.setdefault('hostgroup', hostgroup)

    if hostgroup:
        kwargs.setdefault('type', 'hostgroup')
        service_key_hostname = 'hostgroup_name'
    else:
        kwargs.setdefault('type', 'host')
        service_key_hostname = 'host_name'

    kwargs.setdefault('attrs', attrs)
    kwargs.setdefault('ssh_username', ssh_username)
    if not ssh_addr:
        ssh_addr = hostname
    kwargs.setdefault('ssh_addr', ssh_addr)
    kwargs.setdefault('ssh_port', ssh_port)
    kwargs.setdefault('ssh_timeout', ssh_timeout)

    services = [
        'backup_burp_age',
        'backup_rdiff',
        'beam_process',
        'celeryd_process',
        'cron',
        'ddos',
        'debian_updates',
        'dns_association_hostname',
        'drbd',
        'epmd_process',
        'erp_files',
        'fail2ban',
        'gunicorn_process',
        'haproxy',
        'ircbot_process',
        'load_avg',
        'mail_cyrus_imap_connections',
        'mail_imap',
        'mail_imap_ssl',
        'mail_pop',
        'mail_pop_ssl',
        'mail_pop_test_account',
        'mail_server_queues',
        'mail_smtp',
        'megaraid_sas',
        'memory',
        'memory_hyperviseur',
        'mysql_process',
        'ntp_peers',
        'ntp_time',
        'only_one_nagios_running',
        'postgres_port',
        'postgres_process',
        'prebill_sending',
        'raid',
        'sas',
        'snmpd_memory_control',
        'ssh',
        'supervisord_status',
        'swap',
        'tiles_generator_access',
        'ware_raid',
        'web_apache_status',
    ]
    services_enabled = dict()
    for service in services:
        services_enabled[service] = eval(service)

    kwargs.setdefault('services_enabled', services_enabled)

    # services for which a loop is used in the macro
    services_loop = [
        'dns_association',
        'dns_reverse_association',
        'disk_space',
        'network',
        'solr',
        'web_openid',
        'web',
    ]
    services_loop_enabled = dict()
    for service in services_loop:
        if eval(service):
            services_loop_enabled[service] = True
        else:
            services_loop_enabled[service] = False

    kwargs.setdefault('services_loop_enabled', services_loop_enabled)

    # values for disk_space service
    mountpoints_path = {
        'root': "/",
        'var': "/var",
        'srv': "/srv",
        'tmp': "/tmp",
        'data': "/data",
        'mnt_data': "/mnt/data",
        'home': "/home",
        'var_lxc': "/var/lxc",
        'var_makina': "/var/makina",
        'var_mysql': "/var/mysql",
        'var_www': "/var/www",
        'backups': "/backups",
        'backups_guidtz': "/backups/guidtz",
        'var_backups_bluemind': "/var/backups/bluemind",
        'var_spool_cyrus': "/var/spool/cyrus",
        'nmd_www': "",  # must be completed
    }
    disks_spaces = dict()
    for mountpoint, path in mountpoints_path.items():
        if eval('disk_space_'+mountpoint):
            disks_spaces[mountpoint] = path

    # default values for dns_association service
    dns_hostname = ''
    dns_address = ''

    if ((dns_association_hostname
        or dns_association
        or dns_reverse_association)
            and 'address' in attrs
            and 'host_name' in attrs):

        if 'host_name' in attrs:
            dns_hostname = attrs['host_name']
        else:
            dns_hostname = hostname

        if not dns_hostname.endswith('.'):
            dns_hostname = dns_hostname+'.'

        dns_address = attrs['address']

    # give the default values for commands parameters values
    # the keys are the services names, not the commands names
    services_default_attrs = {
        'backup_burp_age': {
            'service_description': "S_BACKUP_BURP_AGE",
            'use': "ST_BACKUP_DAILY_ALERT",
            'check_command': "CSSH_BACKUP_BURP",

            'cmdarg_ssh_username': "root",
            'cmdarg_ssh_addr': "backup.makina-corpus.net",
            'cmdarg_ssh_port': "22",
            'cmdarg_ssh_timeout': 10,
            'cmdarg_warning': 1560,
            'cmdarg_critical': 1800,
        },
        'backup_rdiff': {
            'service_description': "S_BACKUP_RDIFF",
            'use': "ST_BACKUP_DAILY_ALERT",
            'check_command': "CSSH_BACKUP",

            'cmdarg_ssh_username': "root",
            'cmdarg_ssh_addr': "backup.makina-corpus.net",
            'cmdarg_ssh_port': "22",
            'cmdarg_ssh_timeout': 10,
            'cmdarg_command': "/root/admin_scripts/nagios/check_rdiff -r /data/backups/phpnet6 -w 24 -c 48 -l 2048 -p 24"
        },
        'beam_process': {
            'service_description': "Check beam proces",
            'use': "ST_ALERT",
            'notification_options': "w,c,r",
            'notifications_enabled': 1,
            'check_command': "C_SNMP_PROCESS",

            'cmdarg_process': "beam",
            'cmdarg_warning': 0,
            'cmdarg_critical': 0,
        },
        'celeryd_process': {
            'service_description': "Check celeryd process",
            'use': "ST_ALERT",
            'notification_options': "w,c,r",
            'notifications_enabled': 1,
            'check_command': "C_SNMP_PROCESS",

            'cmdarg_process': "python",
            'cmdarg_warning': 1,
            'cmdarg_critical': 0,
        },
        'cron': {
            'service_description': "S_PROC_CRON",
            'use': "ST_SSH_PROC_CRON",
            'check_command': "CSSH_CRON",
        },
        'ddos': {
            'service_description': "DDOS",
            'use': "ST_ALERT",
            'check_command': "CSSH_DDOS",

            'cmdarg_warning': 50,
            'cmdarg_critical': 60,
        },
        'debian_updates': {
            'service_description': "S_DEBIAN_UPDATES",
            'use': "ST_DAILY_NOALERT",
            'check_command': "CSSH_DEBIAN_UPDATES",
        },
        'dns_association_hostname': {
            'service_description': "DNS_ASSOCIATION_hostname",
            'use': "ST_DNS_ASSOCIATION_hostname",
            'check_command': "C_DNS_EXTERNE_ASSOCIATION",
            'cmdarg_hostname': dns_hostname,
            'cmdarg_dns_address': dns_address,
            'cmdarg_other_args': "",
        },
        'dns_association': {
            'default': {
                # default service_description is a prefix (see below)
                'service_description': "DNS_ASSOCIATION_",
                'use': "ST_DNS_ASSOCIATION",
                'check_command': "C_DNS_EXTERNE_ASSOCIATION",
                'cmdarg_hostname': dns_hostname,
                'cmdarg_dns_address': dns_address,
                'cmdarg_other_args': "",
            }
        },
        'dns_reverse_association': {
            'default': {
                'service_description': "DNS_REVERSE_ASSOCIATION_",
                'use': "ST_DNS_ASSOCIATION",
                'check_command': "C_DNS_EXTERNE_REVERSE_ASSOCIATION",
                # 'cmdarg_inaddr': ""  # generated below
                                       # from dns_association dictionary
                #  'cmdarg_hostname': ""
                'cmdarg_other_args': "",
            },
        },
        'disk_space': {
            'default': {
                # it is prefix
                'service_description': "DISK_SPACE_",
                'use': "ST_DISK_SPACE_",
                'check_command': "C_SNMP_DISK",

                'cmdarg_warning': 80,
                'cmdarg_critical': 90,
            },
        },
        'drbd': {
            'service_description': "CHECK_DRBD",
            'use': "ST_ALERT",
            'icon_image': "services/heartbeat.png",
            'check_command': "CSSH_DRBD",

            'cmdarg_command': "'/root/admin_scripts/nagios/check_drbd -d  0,1'",
        },
        'epmd_process': {
            'service_description': "Check epmd process",
            'use': "ST_ALERT",
            'notification_options': "w,c,r",
            'notifications_enabled': 1,
            'check_command': "C_SNMP_PROCESS",

            'cmdarg_process': "epmd",
            'cmdarg_warning': 0,
            'cmdarg_critical': 0,
        },
        'erp_files': {
            'service_description': "CHECK_ERP_FILES",
            'use': "ST_ALERT",
            'check_command': "CSSH_CUSTOM",

            'cmdarg_command': "/var/makina/alma-job/job/supervision/check_erp_files.sh",
        },
        'fail2ban': {
            'service_description': "S_FAIL2BAN",
            'use': "ST_ROOT",
            'notifications_enabled': 1,
            'check_command': "C_SNMP_PROCESS",

            'cmdarg_process': "fail2ban-server",
            'cmdarg_warning': 0,
            'cmdarg_critical': 0,
        },
       'gunicorn_process': {
           'service_description': "Check gunicorn process",
           'use': "ST_ALERT",
           'notification_options': "w,c,r",
           'notifications_enabled': 1,
           'check_command': "C_SNMP_PROCESS",

           'cmdarg_process': "gunicorn_django",
           'cmdarg_warning': 0,
           'cmdarg_critical': 0,
        },
        'haproxy': {
            'service_description': "haproxy_stats",
            'use': "ST_ALERT",
            'check_command': "CSSH_HAPROXY",

            'cmdarg_command': "/root/admin_scripts/nagios/check_haproxy_stats.pl -p web -w 80 -c 90",
        },
        'ircbot_process': {
            'service_description': "S_IRCBOT_PROCESS",
            'use': "ST_HOURLY_ALERT",
            'check_command': "C_PROCESS_IRCBOT_RUNNING",
        },
        'load_avg': {
            'service_description': "LOAD_AVG",
            'use': "ST_LOAD_AVG",
            'check_command': "C_SNMP_LOADAVG",

            'cmdarg_other_args': "",
        },
        'mail_cyrus_imap_connections': {
            'service_description': "S_MAIL_CYRUS_IMAP_CONNECTIONS",
            'use': "ST_ALERT",
            'check_command': "CSSH_CYRUS_CONNECTIONS",

            'cmdarg_warning': 300,
            'cmdarg_critical': 900,
        },
       'mail_imap': {
           'service_description': "S_MAIL_IMAP",
           'use': "ST_ALERT",
           'check_command': "C_MAIL_IMAP",

           'cmdarg_warning': 1,
           'cmdarg_critical': 3,
        },
        'mail_imap_ssl': {
            'service_description': "S_MAIL_IMAP_SSL",
            'use': "ST_ALERT",
            'check_command': "C_MAIL_IMAP_SSL",

            'cmdarg_warning': 1,
            'cmdarg_critical': 3,
        },
        'mail_pop': {
            'service_description': "S_MAIL_POP",
            'use': "ST_ALERT",
            'check_command': "C_MAIL_POP",

            'cmdarg_warning': 1,
            'cmdarg_critical': 3,
        },
       'mail_pop_ssl': {
            'service_description': "S_MAIL_POP_SSL",
            'use': "ST_ALERT",
            'check_command': "C_MAIL_POP_SSL",

            'cmdarg_warning': 1,
            'cmdarg_critical': 3,
        },
        'mail_pop_test_account': {
            'service_description': "S_MAIL_POP3_TEST_ACCOUNT",
            'use': "ST_ALERT",
            'check_command': "C_POP3_TEST_SIZE_AND_DELETE",

            'cmdarg_warning1': 52488,
            'cmdarg_critical1': 1048576,
            'cmdarg_warning2': 100,
            'cmdarg_critical2': 2000,
            'cmdarg_mx': "@makina-corpus.com",
        },
        'mail_server_queues': {
            'service_description': "S_MAIL_SERVER_QUEUES",
            'use': "ST_ALERT",
            'check_command': "CSSH_MAILQUEUE",

            'cmdarg_warning': 50,
            'cmdarg_critical': 100,
        },
        'mail_smtp': {
            'service_description': "S_MAIL_SMTP",
            'use': "ST_ALERT",
            'check_command': "C_MAIL_SMTP",

            'cmdarg_warning': 1,
            'cmdarg_critical': 3,
        },
        'megaraid_sas': {
            'service_description': "CHECK_MEGARAID_SAS",
            'use': "ST_ALERT",
            'check_command': "CSSH_MEGARAID_SAS",

            'cmdarg_command': "'/root/admin_scripts/nagios/check_megaraid_sas'",
        },
        'memory': {
            'service_description': "MEMORY",
            'use': "ST_MEMORY",
            'check_command': "C_SNMP_MEMORY",

            'cmdarg_warning': 80,
            'cmdarg_critical': 90,
        },
        'memory_hyperviseur': {
            'service_description': "MEMORY_HYPERVISEUR",
            'use': "ST_MEMORY_HYPERVISEUR",
            'check_command': "C_SNMP_MEMORY",

            'cmdarg_warning': 95,
            'cmdarg_critical': 99,
        },
        'mysql_process': {
            'service_description': "S_MYSQL_PROCESS",
            'use': "ST_ALERT",
            'check_command': "C_SNMP_PROCESS",

            'cmdarg_process': "mysql",
            'cmdarg_warning': 0,
            'cmdarg_critical': 0,
        },
        'network': {
            'default': {
                # prefix
                'service_description': "NETWORK_",
                'use': "ST_NETWORK_",
                'check_command': "C_SNMP_NETWORK",

                'cmdarg_interface': "eth0",
                'cmdarg_other_args': "",
            },
        },
        'ntp_peers': {
           'service_description': "S_NTP_PEERS",
           'use': "ST_ROOT",
           'check_command': "CSSH_NTP_PEER",
        },
        'ntp_time': {
            'service_description': "S_NTP_TIME",
            'use': "ST_ROOT",
            'check_command': "CSSH_NTP_TIME",
        },
        'only_one_nagios_running': {
            'service_description': "S_ONLY_ONE_NAGIOS_RUNNING",
            'use': "ST_HOURLY_ALERT",
            'check_command': "C_CHECK_ONE_NAGIOS_ONLY",
        },
        'postgres_port': {
            'service_description': "S_POSTGRESQL_PORT",
            'use': "ST_ROOT",
            'icon_image': "services/sql4.png",
            'check_command': "check_tcp",

            'cmdarg_port': 5432,
            'cmdarg_warning': 2,
            'cmdarg_critical': 8,
        },
        'postgres_process': {
            'service_description': "S_POSTGRESQL_PROCESS",
            'use': "ST_ALERT",
            'icon_image': "services/sql4.png",
            'check_command': "C_SNMP_PROCESS",

            'cmdarg_process': "postgres",
            'cmdarg_warning': 0,
            'cmdarg_critical': 0,
        },
        'prebill_sending': {
            'service_description': "CHECK_PREBILL_SENDING",
            'use': "ST_ALERT",
            'check_command': "CSSH_CUSTOM",

            'cmdarg_command': "/var/makina/alma-job/job/supervision/check_prebill_sending.sh",
        },
        'raid': {
            'service_description': "CHECK_RAID",
            'use': "ST_ALERT",
            'check_command': "CSSH_RAID_SOFT",

            'cmdarg_command': "'/root/admin_scripts/nagios/check_md_raid'",
        },
        'sas': {
            'service_description': "S_SAS",
            'use': "ST_ROOT",
            'check_command': "CSSH_SAS2IRCU",

            'cmdarg_command': "/root/admin_scripts/check_nagios/check_sas2ircu/check_sas2ircu",
        },
        'snmpd_memory_control': {
            'service_description': "S_SNMPD_MEMORY_CONTROL",
            'use': "ST_ALERT",
            'check_command': "C_SNMP_PROCESS_WITH_MEM",

            'cmdarg_process': "snmpd",
            'cmdarg_warning': "0,1",
            'cmdarg_critical': "0,1",
            'cmdarg_memory': "256,512",
        },
        'solr': {
            'default': {
                'service_description': "SOLR_",
                'use': "ST_WEB_PUBLIC",
                'check_command': "C_HTTP_STRING_SOLR",

                'cmdarg_hostname': "h",
                'cmdarg_port': 80,
                'cmdarg_url': "/",
                'cmdarg_warning': 1,
                'cmdarg_critical': 5,
                'cmdarg_timeout': 8,
                'cmdarg_strings': [],
                'cmdarg_other_args': "",
            },
        },
        'ssh': {
            'service_description': "S_SSH",
            'use': "ST_ROOT",
            'check_command': "check_tcp",

            'cmdarg_port': 22,
            'cmdarg_warning': 1,
            'cmdarg_critical': 4,
        },
        'supervisord_status': {
            'service_description': "S_SUPERVISORD_STATUS",
            'use': "ST_ALERT",
            'check_command': "CSSH_SUPERVISOR",

            'cmdarg_command': "/home/zope/adria/rcse/production-2014-01-23-14-27-01/bin/supervisorctl",
        },
        'swap': {
            'service_description': "CHECK_SWAP",
            'use': "ST_ALERT",
            'check_command': "CSSH_RAID_SOFT",

            'cmdarg_command': "'/root/admin_scripts/nagios/check_swap -w 80%% -c 50%%'",
        },
        'tiles_generator_access': {
            'service_description': "Check tiles generator access",
            'use': "ST_ALERT",
            'notification_options': "w,c,r",
            'notifications_enabled': 1,
            'check_command': "check_http_vhost_uri",

            'cmdarg_hostname': "vdm.makina-corpus.net",
            'cmdarg_url': "/vdm-tiles/status/",
        },
        'ware_raid': {
            'service_description': "CHECK_3WARE_RAID",
            'use': "ST_ALERT",
            'check_command': "CSSH_RAID_3WARE",

            'cmdarg_command': "/root/admin_scripts/nagios/check_3ware_raid",
        },
        'web_apache_status': {
            'service_description': "WEB_APACHE_STATUS",
            'use': "ST_WEB_APACHE_STATUS",
            'check_command': "C_APACHE_STATUS",

            'cmdarg_warning': 4,
            'cmdarg_critical': 2,
            'cmdarg_other_args': "",
        },
        'web_openid': {
            'default': {
                'service_description': "WEB_OPENID_",
                'use': "ST_WEB_PUBLIC",
                'check_command': "C_HTTPS_OPENID_REDIRECT",

                'cmdarg_hostname': hostname,
                'cmdarg_url': "/",
                'cmdarg_warning': 1,
                'cmdarg_critical': 5,
                'cmdarg_timeout': 8,
            },
        },
        'web': {
            'default': {
                'service_description': "WEB_",
                'cmdarg_hostname': hostname,
                'use': "ST_WEB_PUBLIC",
                'check_command': "C_HTTP_STRING",

                'cmdarg_url': "/",
                'cmdarg_warning': 2,
                'cmdarg_critical': 3,
                'cmdarg_timeout': 8,
                'cmdarg_strings': [],
                'cmdarg_other_args': "",
            },
        },
    }

    # add the services_attrs 'default' in all services
    # in services_default_attrs
    # in order to add directives for all services
    # (like contact_groups)
    if 'default' in services_attrs:
        for name, service in services_default_attrs.items():
            if name not in services_attrs:
                services_attrs[name] = {}
            if name not in ['dns_association',
                            'dns_reverse_association',
                            'disk_space',
                            'network',
                            'solr',
                            'web_openid',
                            'web']:
                services_default_attrs[name] = dict(
                    services_default_attrs[name].items()
                    + services_attrs['default'].items()
                )
            else:
                services_default_attrs[name]['default'] = dict(
                    services_default_attrs[name]['default'].items()
                    + services_attrs['default'].items()
                )
        services_attrs.pop('default', None)

    # override the commands parameters values
    # we complete the services_attrs dictionary with values
    # from services_default_attrs

    # override dns_association subdictionary
    if 'dns_association' not in services_attrs:
        services_attrs['dns_association'] = services_default_attrs[
            'dns_association']
        services_attrs['dns_association']['default'][
            'service_description'] = services_default_attrs[
                'dns_association']['default']['service_description']+'default'
    else:
        for name, dns in services_attrs['dns_association'].items():
            # generate the service_description if not given
            if 'service_description' not in dns:
                services_attrs['dns_association'][name][
                    'service_description'] = services_default_attrs[
                        'dns_association']['default'][
                            'service_description']+name
            for key, value in services_default_attrs[
                    'dns_association']['default'].items():
                if key not in dns:
                    services_attrs['dns_association'][name][key] = value

    # override dns_reverse_assocation subdictionary
    if 'dns_reverse_association' not in services_attrs:
        services_attrs['dns_reverse_association'] = {}
        # the dictionary is not set, we generate it from dns_association
        # dictionary (we suppose all ips are ipv4 that is bad):
        for name, dns in services_attrs['dns_association'].items():
            services_attrs['dns_reverse_association'][
                name] = copy.deepcopy(
                    services_default_attrs[
                        'dns_reverse_association']['default']
                )
            services_attrs['dns_reverse_association'][
                name]['service_description'] = services_default_attrs[
                    'dns_reverse_association'][
                        'default']['service_description']+name

            address_splitted = dns['cmdarg_dns_address'].split('.')
            # tanslate a.b.c.d in d.c.b.a
            inaddr = '.'.join(address_splitted[::-1])
            inaddr = inaddr + '.in-addr.arpa.'
            services_attrs['dns_reverse_association'][name][
                'cmdarg_inaddr'] = inaddr
            services_attrs['dns_reverse_association'][name][
                'cmdarg_hostname'] = dns['cmdarg_hostname']
    else:
        # the dictionary is set, we merging normally
        for name, dns in services_attrs['dns_reverse_association'].items():
            if 'service_description' not in dns:
                services_attrs['dns_reverse_association'][
                    name]['service_description'] = services_default_attrs[
                        'dns_association'][name][
                            'service_reverse_description']+name
            for key, value in services_default_attrs[
                    'dns_reverse_association']['default'].items():
                if key not in dns:
                    services_attrs['dns_reverse_association'][name][
                        key] = value

    # override network subdictionary
    if 'network' not in services_attrs:
        services_attrs['network'] = services_default_attrs['network']
        services_attrs['network']['default'][
            'service_description'] = services_default_attrs[
            'network']['default']['service_description']+'default'
        services_attrs['network']['default'][
            'use'] = services_default_attrs['network']['default'][
                'use']+services_default_attrs['network']['default'][
                    'cmdarg_interface'].upper()
    else:
        for name, network in services_attrs['network'].items():
            # generate the service_description if not given
            if 'service_description' not in network:
                if 'cmdarg_interface' in services_attrs['network'][name]:
                    services_attrs['network'][
                        name]['service_description'] = services_default_attrs[
                            'network']['default']['service_description']
                    + services_attrs['network'][
                        name]['cmdarg_interface'].upper()
                else:
                    services_attrs['network'][
                        name]['service_description'] = services_default_attrs[
                            'network']['default']['service_description']
                    + services_default_attrs['network'][
                        'default']['cmdarg_interface'].upper()
            if 'use' not in network:
                if 'cmdarg_interface' in services_attrs['network'][name]:
                    services_attrs['network'][
                        name]['use'] = services_default_attrs['network'][
                            'default']['use']+services_attrs['network'][
                                name]['cmdarg_interface'].upper()
                else:
                    services_attrs['network'][
                        name]['use'] = services_default_attrs['network'][
                            'default']['use']
                    + services_default_attrs['network'][
                        'default']['cmdarg_interface'].upper()

            for key, value in services_default_attrs['network'][
                    'default'].items():
                if key not in network:
                    services_attrs['network'][name][key] = value

    # override solr subdictionary
    if 'solr' not in services_attrs:
        services_attrs['solr'] = services_default_attrs['solr']
        services_attrs['solr'][
            'default']['service_description'] = services_default_attrs['solr'][
                'default']['service_description']+'default'
    else:
        for name, solr in services_attrs['solr'].items():
            # generate the service_description if not given
            if 'service_description' not in solr:
                services_attrs['solr'][
                    name]['service_description'] = services_default_attrs[
                        'solr']['default']['service_description']+name
            for key, value in services_default_attrs['solr'][
                    'default'].items():
                if key not in solr:
                    services_attrs['solr'][name][key] = value
            # transform list of values in string
            # ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_attrs['solr'][name]['cmdarg_strings'],
                          list):
                str_list = services_attrs['solr'][name]['cmdarg_strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [value.replace('"', '\\\\"') for value in str_list]
                services_attrs['solr'][
                    name]['cmdarg_strings'] = '"'+'" -s "'.join(str_list)+'"'

    # override web_openid subdictionary
    if 'web_openid' not in services_attrs:
        services_attrs['web_openid'] = services_default_attrs['web_openid']
        services_attrs['web_openid'][
            'default']['service_description'] = services_default_attrs[
                'web_openid']['default']['service_description']+'default'
    else:
        for name, web_openid in services_attrs['web_openid'].items():
            # generate the service_description if not given
            if 'service_description' not in web_openid:
                services_attrs['web_openid'][
                    name]['service_description'] = services_default_attrs[
                        'web_openid']['default']['service_description']+name
            for key, value in services_default_attrs['web_openid'][
                    'default'].items():
                if key not in web_openid:
                    services_attrs['web_openid'][name][key] = value

    # override web subdictionary
    if 'web' not in services_attrs:
        services_attrs['web'] = services_default_attrs['web']
        services_attrs['web'][
            'default']['service_description'] = services_default_attrs[
                'web']['default']['service_description']+'default'
    else:
        for name, web in services_attrs['web'].items():
            # generate the service_description if not given
            if 'service_description' not in web:
                services_attrs['web'][
                    name]['service_description'] = services_default_attrs[
                        'web']['default']['service_description']+name
            for key, value in services_default_attrs['web'][
                    'default'].items():
                if key not in web:
                    services_attrs['web'][name][key] = value
            # transform list of values in string
            # ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_attrs['web'][name]['cmdarg_strings'], list):
                str_list = services_attrs['web'][name]['cmdarg_strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [value.replace('"', '\\\\"') for value in str_list]
                services_attrs['web'][
                    name]['cmdarg_strings'] = '"'+'" -s "'.join(str_list)+'"'

    # override mountpoints subdictionaries
    # for each disk_space, build the dictionary:
    # priority for values
    # services_default_attrs['disk_space'][
    #    'default'] # default values in default dictionary
    # services_default_attrs['disk_space'][
    #    mountpoint] # specific values in default dictionary
    # services_attrs['disk_space'][
    #    'default'] # default value in overrided dictionary
    # services_attrs['disk_space'][
    #    mountpoint] # specific value in overrided dictionary
    if 'disk_space' not in services_attrs:
        services_attrs['disk_space'] = {}
    # we can't merge default dictionary yet because
    # priorities will not be respected
    if 'default' not in services_attrs['disk_space']:
        services_attrs['disk_space']['default'] = {}

    for mountpoint, path in mountpoints_path.items():
        if mountpoint in disks_spaces:  # the check is enabled
            if mountpoint not in services_default_attrs['disk_space']:
                services_default_attrs['disk_space'][
                    mountpoint] = copy.deepcopy(
                    services_default_attrs['disk_space']['default']
                )

            services_attrs['disk_space'][mountpoint] = dict(
                services_default_attrs['disk_space']['default'].items()
                + services_default_attrs['disk_space'][mountpoint].items()
            )

            services_attrs['disk_space'][mountpoint] = dict(
                services_attrs['disk_space'][mountpoint].items()
                + services_attrs['disk_space']['default'].items()
            )

            services_attrs['disk_space'][mountpoint] = dict(
                services_attrs['disk_space'][mountpoint].items()
                + services_attrs['disk_space'][mountpoint].items()
            )

            if services_attrs['disk_space'][
                mountpoint]['service_description'] == services_default_attrs[
                    'disk_space']['default']['service_description']:
                services_attrs['disk_space'][
                    mountpoint]['service_description'] = services_attrs[
                        'disk_space'][mountpoint]['service_description']
                + disks_spaces[mountpoint].upper()
            if services_attrs['disk_space'][
                mountpoint]['use'] == services_default_attrs[
                    'disk_space']['default']['use']:
                services_attrs['disk_space'][
                    mountpoint]['use'] = services_attrs['disk_space'][
                        mountpoint]['use']
                + disks_spaces[
                    mountpoint].replace('/', '_').replace('_', '/', 1).upper()
            services_attrs['disk_space'][
                mountpoint]['cmdarg_path'] = disks_spaces[mountpoint]

    # remove default dictionary
    if 'default' in services_attrs['disk_space']:
        services_attrs['disk_space'].pop('default', None)

    # override others values (type are string or int)
    if not isinstance(services_attrs, dict):
        services_attrs = {}

    for name, command in services_default_attrs.items():
        if name not in ['dns_association',
                        'dns_reverse_association',
                        'disk_space',
                        'network',
                        'solr',
                        'web_openid',
                        'web']:
            if name not in services_attrs:
                services_attrs[name] = {}
            services_attrs[name] = dict(
                services_default_attrs[name].items()
                + services_attrs[name].items()
            )

    # generate the complete check command (we can't do a loop before
    # we have to give the good order for arguments)
    cssh_params = ['ssh_username', 'ssh_addr', 'ssh_port', 'ssh_timeout']

    check_command_args = {
        'CSSH_BACKUP_BURP': ['ssh_username', 'ssh_addr', 'ssh_port',
                             'warning', 'critical'],
        'CSSH_BACKUP': ['ssh_username', 'ssh_addr', 'ssh_port',
                        'warning', 'critical'],
        'C_SNMP_PROCESS': ['process', 'warning', 'critical'],
        'CSSH_CRON': cssh_params,
        'CSSH_DDOS': cssh_params+['warning', 'critical'],
        'CSSH_DEBIAN_UPDATES': cssh_params,
        'C_DNS_EXTERNE_ASSOCIATION': ['hostname', 'other_args'],
        'C_DNS_EXTERNE_REVERSE_ASSOCIATION': ['inaddr', 'hostname',
                                              'other_args'],
        'C_SNMP_DISK': ['path', 'warning', 'critical'],
        'CSSH_DRBD': cssh_params+['command'],
        'CSSH_CUSTOM': cssh_params+['command'],
        'CSSH_HAPROXY': cssh_params+['command'],
        'C_PROCESS_IRCBOT_RUNNING': [],
        'C_SNMP_LOADAVG': ['other_args'],
        'CSSH_CYRUS_CONNECTIONS': cssh_params+['warning', 'critical'],
        'C_MAIL_IMAP': ['warning', 'critical'],
        'C_MAIL_IMAP_SSL': ['warning', 'critical'],
        'C_MAIL_POP': ['warning', 'critical'],
        'C_MAIL_POP_SSL': ['warning', 'critical'],
        'C_POP3_TEST_SIZE_AND_DELETE': ['warning1', 'critical1',
                                        'warning2', 'critical2', 'mx'],
        'CSSH_MAILQUEUE': cssh_params+['warning', 'critical'],
        'C_MAIL_SMTP': ['warning', 'critical'],
        'CSSH_MEGARAID_SAS': cssh_params+['command'],
        'C_SNMP_MEMORY': ['warning', 'critical'],
        'C_SNMP_NETWORK': ['interface', 'other_args'],
        'CSSH_NTP_PEER': cssh_params,
        'CSSH_NTP_TIME': cssh_params,
        'C_CHECK_ONE_NAGIOS_ONLY': [],
        'check_tcp': ['port', 'warning', 'critical'],
        'CSSH_RAID_SOFT': cssh_params+['command'],
        'CSSH_SAS2IRCU': cssh_params+['command'],
        'C_SNMP_PROCESS_WITH_MEM': ['process', 'warning',
                                    'critical', 'memory'],
        'C_HTTP_STRING_SOLR': ['hostname', 'port', 'warning',
                               'critical', 'timeout', 'strings', 'other_args'],
        'CSSH_SUPERVISOR': cssh_params + ['command'],
        'check_http_vhost_uri': ['hostname', 'url'],
        'CSSH_RAID_3WARE': cssh_params + ['command'],
        'C_APACHE_STATUS': ['warning', 'critical', 'other_args'],
        'C_HTTPS_OPENID_REDIRECT': ['hostname', 'url', 'warning',
                                    'critical', 'timeout'],
        'C_HTTP_STRING': ['hostname', 'url', 'warning', 'critical',
                          'timeout', 'strings', 'other_args'],
        'C_HTTP_STRING_AUTH': ['hostname', 'url', 'warning', 'critical',
                               'timeout', 'strings', 'other_args'],
        'C_HTTP_STRING_ONLY': ['hostname', 'url', 'warning', 'critical',
                               'timeout', 'strings', 'other_args'],
        'C_HTTPS_STRING_ONLY': ['hostname', 'url', 'warning', 'critical',
                                'timeout', 'strings', 'other_args'],
        'C_CHECK_LABORANGE_LOGIN': ['hostname', 'url', 'warning', 'critical',
                                    'timeout', 'strings', 'other_args'],
        'C_CHECK_LABORANGE_STATS': ['hostname', 'url', 'warning', 'critical',
                                    'timeout', 'strings', 'other_args'],
        'check_https': ['hostname', 'url', 'warning', 'critical',
                        'timeout', 'strings', 'other_args'],
    }

    cmdarg_prefix = "cmdarg_"

    # build the check command with args
    for service in services:
        if service in services_attrs:
            if ('check_command' in services_attrs[service]
                    and '!' not in services_attrs[service]['check_command']):

                args = [str(services_attrs[service]['check_command'])]

                for arg in check_command_args[services_attrs[
                        service]['check_command']]:
                    # case of ssh params because we look for ssh_username
                    # not cmdarg_ssh_username
                    if arg in cssh_params:
                        if arg in services_attrs[service]:
                            args.append(str(services_attrs[service][arg]))
                        else:
                            args.append(str(eval(arg)))
                    else:
                        if cmdarg_prefix+arg in services_attrs[service]:
                            args.append(
                                str(services_attrs[service]['cmdarg_'+arg])
                            )
                        else:
                            # by default, a non specified arg take
                            # an empty value
                            args.append('')
                services_attrs[service]['check_command'] = "!".join(args)

    for service in services_loop:
        if service in services_attrs:
            for subservice in services_attrs[service]:
                if ('check_command' in services_attrs[service][subservice]
                    and '!' not in services_attrs[service][
                        subservice]['check_command']):

                    args = [str(services_attrs[service][
                        subservice]['check_command'])]

                    for arg in check_command_args[
                        services_attrs[service][subservice]['check_command']
                    ]:
                        # case of ssh params because we look for
                        # ssh_username not cmdarg_ssh_username
                        if arg in cssh_params:
                            if arg in services_attrs[service][subservice]:
                                args.append(
                                    str(services_attrs[service][
                                        subservice][arg])
                                )
                            else:
                                args.append(str(eval(arg)))
                        else:
                            if cmdarg_prefix+arg in services_attrs[
                                    service][subservice]:
                                args.append(
                                    str(services_attrs[service][
                                        subservice]['cmdarg_'+arg])
                                )
                            else:
                                args.append('')
                    services_attrs[service][
                        subservice]['check_command'] = "!".join(args)

    # add the host_name or hostgroup_name in each service and
    # remove directives begining with "cmdarg_"

    for service in services:
        if service in services_attrs:
            # for arg in copy.deepcopy(services_attrs[service]):
            for arg, v in services_attrs[service].items():
                if arg.startswith(cmdarg_prefix):
                    services_attrs[service].pop(arg, None)
            services_attrs[service][service_key_hostname] = hostname

    for service in services_loop:
        if service in services_attrs:
            for subservice in services_attrs[service]:
                # for arg in copy.deepcopy(services_attrs[
                # service][subservice]):
                for arg, v in services_attrs[
                        service][subservice].items():
                    if arg.startswith(cmdarg_prefix):
                        services_attrs[service][subservice].pop(arg, None)
                services_attrs[service][
                    subservice][service_key_hostname] = hostname

    kwargs.setdefault('services_attrs', services_attrs)

    icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings, kwargs)
    print('end call add_auto_configuration_host_settings')
    return icingaSettings


def add_auto_configuration_host(hostname=None,
                                hostgroup=False,
                                attrs={},
                                ssh_username='root',
                                ssh_addr='',
                                ssh_port=22,
                                ssh_timeout=30,
                                backup_burp_age=False,
                                backup_rdiff=False,
                                beam_process=False,
                                celeryd_process=False,
                                cron=False,
                                ddos=False,
                                debian_updates=False,
                                dns_association_hostname=False,
                                dns_association=False,
                                dns_reverse_association=False,
                                disk_space=False,
                                disk_space_root=False,
                                disk_space_var=False,
                                disk_space_srv=False,
                                disk_space_tmp=False,
                                disk_space_data=False,
                                disk_space_mnt_data=False,
                                disk_space_home=False,
                                disk_space_var_lxc=False,
                                disk_space_var_makina=False,
                                disk_space_var_mysql=False,
                                disk_space_var_www=False,
                                disk_space_backups=False,
                                disk_space_backups_guidtz=False,
                                disk_space_var_backups_bluemind=False,
                                disk_space_var_spool_cyrus=False,
                                disk_space_nmd_www=False,
                                drbd=False,
                                epmd_process=False,
                                erp_files=False,
                                fail2ban=False,
                                gunicorn_process=False,
                                haproxy=False,
                                ircbot_process=False,
                                load_avg=False,
                                mail_cyrus_imap_connections=False,
                                mail_imap=False,
                                mail_imap_ssl=False,
                                mail_pop=False,
                                mail_pop_ssl=False,
                                mail_pop_test_account=False,
                                mail_server_queues=False,
                                mail_smtp=False,
                                megaraid_sas=False,
                                memory=False,
                                memory_hyperviseur=False,
                                mysql_process=False,
                                network=False,
                                ntp_peers=False,
                                ntp_time=False,
                                only_one_nagios_running=False,
                                postgres_port=False,
                                postgres_process=False,
                                prebill_sending=False,
                                raid=False,
                                sas=False,
                                snmpd_memory_control=False,
                                solr=False,
                                ssh=False,
                                supervisord_status=False,
                                swap=False,
                                tiles_generator_access=False,
                                ware_raid=False,
                                web_apache_status=False,
                                web_openid=False,
                                web=False,
                                services_attrs={},
                                fromsettings=None,
                                get=False,
                                **kwargs):

    print('call add_auto_configuration_host')
    print('end call add_auto_configuration_host')
    if get:
        if hostname:
            return add_auto_configuration_host.objects[hostname]
        else:
            return add_auto_configuration_host.objects
    else:
        # we need some variables to write the state

        # if fromsettings is used, we need to get some arguments values
        if fromsettings:
            host = get_settings_for_object('autoconfigured_hosts_definitions',
                                           fromsettings)
            if 'hostgroup' in host:
                hostgroup = host['hostgroup']

        # icingaSettings = copy.deepcopy(__salt__['mc_icinga.settings']())
        # save the ram (get only useful values)
        icingaSettings_complete = __salt__['mc_icinga.settings']()
        icingaSettings = {}
        kwargs.setdefault('objects', {
            'directory': icingaSettings_complete['objects']['directory']
        })
        kwargs.setdefault('hostname', hostname)
        kwargs.setdefault('hostgroup', hostgroup)
        if hostgroup:
            kwargs.setdefault('type', 'hostgroup')
            service_subdirectory = 'hostgroups'
            service_key_hostname = 'hostgroup_name'
        else:
            kwargs.setdefault('type', 'host')
            service_subdirectory = 'hosts'
            service_key_hostname = 'host_name'
        # we set the filename here
        filen = '/'.join([service_subdirectory, hostname+'.cfg'])
        kwargs.setdefault('file', filen)
        kwargs.setdefault('state_name_salt', replace_chars(filen))
        icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings,
                                                         kwargs)

        # we remember the host to add:

        if fromsettings:
            add_auto_configuration_host.objects[hostname] = {
                'fromsettings': fromsettings
            }
        else:
            add_auto_configuration_host.objects[hostname] = {
                'hostname': hostname,
                'hostgroup': hostgroup,
                'attrs': attrs,
                'ssh_username': ssh_username,
                'ssh_addr': ssh_addr,
                'ssh_port': ssh_port,
                'ssh_timeout': ssh_timeout,
                'backup_burp_age': backup_burp_age,
                'backup_rdiff': backup_rdiff,
                'beam_process': beam_process,
                'celeryd_process': celeryd_process,
                'cron': cron,
                'ddos': ddos,
                'debian_updates': debian_updates,
                'dns_association_hostname': dns_association_hostname,
                'dns_association': dns_association,
                'dns_reverse_association': dns_reverse_association,
                'disk_space': disk_space,
                'disk_space_root': disk_space_root,
                'disk_space_var': disk_space_var,
                'disk_space_srv': disk_space_srv,
                'disk_space_tmp': disk_space_tmp,
                'disk_space_data': disk_space_data,
                'disk_space_mnt_data': disk_space_mnt_data,
                'disk_space_home': disk_space_home,
                'disk_space_var_lxc': disk_space_var_lxc,
                'disk_space_var_makina': disk_space_var_makina,
                'disk_space_var_mysql': disk_space_var_mysql,
                'disk_space_var_www': disk_space_var_www,
                'disk_space_backups': disk_space_backups,
                'disk_space_backups_guidtz': disk_space_backups_guidtz,
                'disk_space_var_backups_bluemind': disk_space_var_backups_bluemind,
                'disk_space_var_spool_cyrus': disk_space_var_spool_cyrus,
                'disk_space_nmd_www': disk_space_nmd_www,
                'drbd': drbd,
                'epmd_process': epmd_process,
                'erp_files': erp_files,
                'fail2ban': fail2ban,
                'gunicorn_process': gunicorn_process,
                'haproxy': haproxy,
                'ircbot_process': ircbot_process,
                'load_avg': load_avg,
                'mail_cyrus_imap_connections': mail_cyrus_imap_connections,
                'mail_imap': mail_imap,
                'mail_imap_ssl': mail_imap_ssl,
                'mail_pop': mail_pop,
                'mail_pop_ssl': mail_pop_ssl,
                'mail_pop_test_account': mail_pop_test_account,
                'mail_server_queues': mail_server_queues,
                'mail_smtp': mail_smtp,
                'megaraid_sas': megaraid_sas,
                'memory': memory,
                'memory_hyperviseur': memory_hyperviseur,
                'mysql_process': mysql_process,
                'network': network,
                'ntp_peers': ntp_peers,
                'ntp_time': ntp_time,
                'only_one_nagios_running': only_one_nagios_running,
                'postgres_port': postgres_port,
                'postgres_process': postgres_process,
                'prebill_sending': prebill_sending,
                'raid': raid,
                'sas': sas,
                'snmpd_memory_control': snmpd_memory_control,
                'solr': solr,
                'ssh': ssh,
                'supervisord_status': supervisord_status,
                'swap': swap,
                'tiles_generator_access': tiles_generator_access,
                'ware_raid': ware_raid,
                'web_apache_status': web_apache_status,
                'web_openid': web_openid,
                'web': web,
                'services_attrs': services_attrs,
            }
        return icingaSettings

# global variable initialisation
add_auto_configuration_host.objects = {}


def clean_global_variables():
    '''
    Function to remove global variables
    # TODO: find how to call this function
    '''
    del add_configuration_object.objects
    del remove_configuration_object.files
    del add_auto_configuration_host.objects


#
