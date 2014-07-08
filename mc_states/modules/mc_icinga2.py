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

__name = 'icinga2'

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
        }

        has_sgbd = ((('host' in module_ido2db_database) 
                     and (module_ido2db_database['host']
                          in  [
                              'localhost', '127.0.0.1', grains['host']
                          ]))
                    or ('socket' in module_ido2db_database))

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga', {
                'package': ['icinga2-bin', 'icinga2-common', 'icinga2-doc'],
                'has_pgsql': ('pgsql' == module_ido2db_database['type']
                              and has_sgbd),
                'has_mysql': ('mysql' == module_ido2db_database['type']
                              and has_sgbd),
                'user': "nagios",
                'group': "nagios",
                'cmdgroup': "www-data",
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
                            'domain': "icinga2-cgi.localhost",
                            'doc_root': "/usr/share/icinga2/classicui/",
                            'vh_content_source': "salt://makina-states/files/etc/nginx/sites-available/icinga2-cgi.content.conf",
                            'vh_top_source': "salt://makina-states/files/etc/nginx/sites-available/icinga2-cgi.top.conf",
                            'icinga_cgi': {
                                'web_directory': "/icinga2-classicui",
                                'realm': "Authentication",
                                'htpasswd_file': "/etc/icinga2/classicui/htpasswd.users",
                                'htdocs_dir': "/usr/share/icinga2/classicui/",
                                'images_dir': "/usr/share/icinga2/classicui/images/$1",
                                'styles_dir': "/usr/share/icinga2/classicui/stylesheets/$1",
                                'cgi_dir': "/usr/lib/cgi-bin/",
                                'uwsgi_pass': "127.0.0.1:3030",
                            },
                        },
                        'uwsgi': {
                            'config_name': "icinga2.ini",
                            'config_file': "salt://makina-states/files/etc/uwsgi/apps-available/icinga2-cgi.ini",
                            'enabled': True,
                            'master': "true",
                            'plugins': "cgi",
                            'async': 20,
                            'ugreen': True,
                            'threads': 5,
                            'socket': "127.0.0.1:3030",
                            'uid': "www-data",
                            'gid': "www-data",
                            'cgi': "/cgi-bin/icinga2-classicui/=/usr/lib/cgi-bin/icinga2-classicui/",
                            'cgi_allowed_ext': ".cgi",
                        },
                        'cgi_cfg': {
                            'standalone_installation': "1",
                            'physical_html_path': "/usr/share/icinga2/classicui/",
                            'url_html_path': "/icinga2-classicui",
                            'url_stylesheets_path': "/icinga2-classicui/stylesheets",
                            'http_charset': "utf-8",
                            'refresh_rate': 30,
                            'refresh_type': 1,
                            'escape_html_tags': 1,
                            'result_limit': 50,
                            'show_tac_header': 1,
                            'use_pending_states': 1,
                            'first_day_of_week': 0,
                            'suppress_maintenance_downtime': 0,
                            'action_url_target': "main",
                            'notes_url_target': "main",
                            'use_authentication': 1,
                            'use_ssl_authentication': 0,
                            'lowercase_user_name': 0,
                            'authorized_for_system_information': "icingaadmin",
                            'authorized_for_configuration_information': "icingaadmin",
                            'authorized_for_full_command_resolution': "icingaadmin",
                            'authorized_for_system_commands': "icingaadmin",
                            'authorized_for_all_services': "icingaadmin",
                            'authorized_for_all_hosts': "icingaadmin",
                            'authorized_for_all_service_commands': "icingaadmin",
                            'authorized_for_all_host_commands': "icingaadmin",
                            'show_all_services_host_is_authorized_for': 1,
                            'show_partial_hostgroups': 0,
                            'show_partial_servicegroups': 0,
                            'default_statusmap_layout': 5,
                            'status_show_long_plugin_output': 0,
                            'display_status_totals': 0,
                            'highlight_table_rows': 1,
                            'add_notif_num_hard': 28,
                            'add_notif_num_soft': 0,
                            'use_logging': 0,
                            'cgi_log_file': "/var/log/icinga/gui/icinga-cgi.log",
                            'cgi_log_rotation_method': "d",
                            'cgi_log_archive_path': "/var/log/icinga/gui",
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
                            'object_cache_file': "/var/cache/icinga2/objects.cache",
                            'status_file': "/var/cache/icinga2/status.dat",
                            'resource_file': "/etc/icinga/resource.cfg",
                            'command_file': "/var/run/icinga2/cmd/icinga2.cmd",
                            'check_external_commands': 1,
                            'interval_length': 60,
                            'status_update_interval': 10,
                            'log_file': "/var/log/icinga2/compat/icinga.log",
                            'log_rotation_method': "h",
                            'log_archive_path': "/var/log/icinga2/compat/archives",
                            'date_format': "us",
                        },
                    },
                    'ido2db': {
                        'package': ['icinga2-ido-'+module_ido2db_database['type']],
                        'enabled': True,
                        'user': "nagios",
                        'group': "nagios",
                        'pidfile': "/var/run/icinga2/ido2db.pid",
                        'database': module_ido2db_database,
                    },
                    'nagios-plugins': {
                        'package': ['nagios-plugins'],
                        'enabled': False,
                    },
                },


            })

        __salt__['mc_macros.update_local_registry'](
            'icinga2', icinga_reg,
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
                                         services_attrs,
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
    services_default_attrs = {
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
    if not 'dns_association' in services_attrs:
        services_attrs['dns_association'] =  services_default_attrs['dns_association']
    else:
        for name, dns in services_attrs['dns_association'].items():
            for key, value in services_default_attrs['dns_association']['default'].items():
                if not key in dns:
                    services_attrs['dns_association'][name][key]=value
            address_splitted = dns['hostname'].split('.')
            inaddr = '.'.join(address_splitted[::-1]) # tanslate a.b.c.d in d.c.b.a
            inaddr = inaddr + '.in-addr.arpa.'
            services_attrs['dns_association'][name]['inaddr']=inaddr


    # override network subdictionary
    if not 'network' in services_attrs:
        services_attrs['network'] =  services_default_attrs['network']
    else:
        for name, network in services_attrs['network'].items():
            for key, value in services_default_attrs['network']['default'].items():
                if not key in network:
                    services_attrs['network'][name][key]=value

    # override solr subdictionary
    if not 'solr' in services_attrs:
        services_attrs['solr'] =  services_default_attrs['solr']
    else:
        for name, solr in services_attrs['solr'].items():
            for key, value in services_default_attrs['solr']['default'].items():
                if not key in solr:
                    services_attrs['solr'][name][key]=value
            # transform list of values in string ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_attrs['solr'][name]['strings'], list):
                str_list = services_attrs['solr'][name]['strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [ value.replace('"', '\\\\"') for value in str_list ]
                services_attrs['solr'][name]['strings']='"'+'" -s "'.join(str_list)+'"'

    # override web_openid subdictionary
    if not 'web_openid' in services_attrs:
        services_attrs['web_openid'] =  services_default_attrs['web_openid']
    else:
        for name, web_openid in services_attrs['web_openid'].items():
            for key, value in services_default_attrs['web_openid']['default'].items():
                if not key in web_openid:
                    services_attrs['web_openid'][name][key]=value

    # override web subdictionary
    if not 'web' in services_attrs:
        services_attrs['web'] =  services_default_attrs['web']
    else:
        for name, web in services_attrs['web'].items():
            for key, value in services_default_attrs['web']['default'].items():
                if not key in web:
                    services_attrs['web'][name][key]=value
            # transform list of values in string ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_attrs['web'][name]['strings'], list):
                str_list = services_attrs['web'][name]['strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [ value.replace('"', '\\\\"') for value in str_list ]
                services_attrs['web'][name]['strings']='"'+'" -s "'.join(str_list)+'"'

            # build the command
            if services_attrs['web'][name]['ssl']:
                cmd = "C_HTTPS_STRING"
            else:
                cmd = "C_HTTP_STRING"
            if services_attrs['web'][name]['authentication']:
                cmd = cmd + "_AUTH"
            if services_attrs['web'][name]['only']:
                cmd = cmd + "_ONLY"

            services_attrs['web'][name]['command'] = cmd

    # override mountpoints subdictionaries


    # for each disk_space, build the dictionary:
    # priority for values
    # services_default_attrs['disk_space']['default'] # default values in default dictionary
    # services_default_attrs['disk_space'][mountpoint] # specific values in default dictionary
    # services_attrs['disk_space']['default'] # default value in overrided dictionary
    # services_attrs['disk_space'][mountpoint] # specific value in overrided dictionary
    if 'disk_space' not in services_attrs:
        services_attrs['disk_space'] = {}
    # we can't merge default dictionary yet because priorities will not be respected
    if 'default' not in services_attrs['disk_space']:
        services_attrs['disk_space']['default'] = {}

    for mountpoint, path in mountpoints_path.items():
        if not mountpoint in services_attrs['disk_space']:
            services_attrs['disk_space'][mountpoint] = {}

        if not mountpoint in services_default_attrs['disk_space']:
            services_default_attrs['disk_space'][mountpoint] = services_default_attrs['disk_space']['default']

        services_attrs['disk_space'][mountpoint] = dict(services_default_attrs['disk_space']['default'].items()
                                                                     +services_default_attrs['disk_space'][mountpoint].items())

        services_attrs['disk_space'][mountpoint] = dict(services_attrs['disk_space'][mountpoint].items()
                                                                     +services_attrs['disk_space']['default'].items())

        services_attrs['disk_space'][mountpoint] = dict(services_attrs['disk_space'][mountpoint].items()
                                                                     +services_attrs['disk_space'][mountpoint].items())

    # merge default dictionaries in order to allow {{mountpoints.defaults.warning}} in jinja template
    if not 'default' in services_attrs['disk_space']:
        services_attrs['disk_space']['default'] = services_default_attrs['disk_space']['default']
    else:
        services_attrs['disk_space']['default'] = dict(services_default_attrs['disk_space']['default'].items() 
                                                                   + services_attrs['disk_space']['default'].items())

    # override others values (type are string or int)
    if not isinstance(services_attrs, dict):
        services_attrs = {}

    for name, command in services_default_attrs.items():
        if not name in ['dns_association', 'mountpoints', 'network', 'solr', 'web_openid', 'web']:
            if not name in services_attrs:
                services_attrs[name] = {}
            services_attrs[name] = dict(services_default_attrs[name].items() + services_attrs[name].items())


    kwargs.setdefault('services_attrs', services_attrs)

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
