# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga2:

mc_icinga2 / icinga functions
============================

The first level of subdictionaries is for distinguish configuration
files. There is one subdictionary per configuration file.
The key used for subdictionary correspond
to the name of the file but the "." is replaced with a "_"

The subdictionary "modules" contains a subsubdictionary for each
module. In each module subdictionary, there is a subdictionary per
file.
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

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import copy
import mc_states.utils

__name = 'icinga2'

DRA = 'dns_reverse_association'
log = logging.getLogger(__name__)


def objects():
    '''
    function to load the dictionary from pillar
    the dictionary contains the objects definitions to add in icinga2

    the autoconfigured_hosts_definitions dictionary contains the
    definitions of hosts created with the configuration_add_auto_host
    macro

    the objects_definitions dictionary contains the defintinions of
    objects created with the configuration_add_object_macro

    the purge_definitions list contains the files to delete

    the "notification" and "parents" are under "attrs"
    but in fact it creates other objects like HostDependency
    or Notification

    example:
        autoconfigured_hosts_definitions:
          localhost:
            hostname: "localhost"
            attrs:
              address: 127.0.0.1
              display_name: "localhost"
            ssh: true
            services_attrs:
         objects_definitions:
           mycommand:
             attrs:
              parents:
                - parent1
                - parent2
              notification:
                command: "notify-by-email"
                users = ["user1"]
              command: /usr/bin/mycommand
              arguments:
                -arg: value
           name: mycommand
           file: command.conf
           type: CheckCommand
           template: false
        purge_definitions:
          - commands.conf
    '''
    locs = __salt__['mc_locations.settings']()
    # XXX: import the centreon configuration
    # generated with
    # ./parse.py icinga2 hosts.cfg  hostgroups.cfg services.cfg \
    # hostTemplates.cfg  serviceTemplates.cfg checkcommands.cfg \
    # timeperiods.cfg contacts.cfg contactgroups.cfg meta_* \
    # misccommands.cfg servicegroups.cfg  \
    # > /srv/pillar/icinga2.sls

    # try to load from a pillar file
    data = __salt__['mc_pillar.yaml_load']('/srv/pillar/icinga2.sls')
    if not data or not isinstance(data, dict):
        data = {}
    if 'objects_definitions' not in data:
        data['objects_definitions'] = {}
    if 'purge_definitions' not in data:
        data['purge_definitions'] = []
    if 'autoconfigured_hosts_definitions' not in data:
        data['autoconfigured_hosts_definitions'] = {}
    return data


def format(dictionary, quote_keys=False, quote_values=True):
    '''
    function to transform all values in a dictionary in string
    and adding quotes.
    The main goal is to print values with quotes like "value"
    but we don't want print list with quotes like "[v1, v2]".
    This should be ["v1", "v2"] this can be done in jinja
    template but the template is already complex
    '''
    res = {}
    for key, value in dictionary.items():
        if quote_keys:
            res_key = '"'+str(key)+'"'
        else:
            res_key = key

        # ugly hack
        if key in ['type', 'template', 'types', 'states']:
            quote_value = False
        else:
            quote_value = quote_values

        if isinstance(value, dict):  # recurse
            # in theses subdictionaries, the keys are also quoted
            if key in ['arguments', 'ranges']:
                res[res_key] = format(value, True, True)
            # theses dictionaries contains booleans
            elif key in ['services_enabled', 'services_loop_enabled']:
                res[res_key] = format(value, False, False)
            else:
                res[res_key] = format(value, quote_keys, quote_value)
        elif isinstance(value, list):
            # theses lists are managed in the template,
            # we only quote each string in the list
            if key in ['import', 'parents']:
                res[res_key] = map((
                    lambda v: '"' + str(v).replace('"', '\\"') + '"'), value)
            else:

                res[res_key] = '['
                # suppose that all values in list are strings
                # escape '"' char and quote each strings
                if quote_value:
                    res[res_key] += ', '.join(
                        map((lambda v: '"' + str(v).replace(
                            '"', '\\"') + '"'), value))
                else:
                    res[res_key] += ', '.join(value)
                res[res_key] += ']'
        elif key.startswith('enable_'):
            if (
                '"1"' == value
                or '1' == value
                or 1 == value
                or 'true' == value
                or True == value
            ):
                res[res_key] = "true"
            else:
                res[res_key] = "false"
        elif key in ['template']:
            res[res_key] = value
        elif key.endswith('_interval'):  # a bad method to find a time
            res[res_key] = value
        elif isinstance(value, bool) and not quote_value:
            res[res_key] = value
        elif isinstance(value, int):
            res[res_key] = str(value)
        elif isinstance(value, unicode):
            if quote_value:
                res[res_key] = '"' + value.replace('"', '\\"') + '"'
            else:
                res[res_key] = value
        else:
            if quote_value:
                res[res_key] = '"' + str(value).decode(
                    'utf-8').replace('"', '\\"')+'"'
            else:
                res[res_key] = value
    return res


def get_settings_for_object(target=None, obj=None, attr=None):
    '''
    expand the subdictionaries which are not cached
    in mc_icinga2.settings.objects
    '''
    if 'purge_definitions' == target:
        res = objects()[target]
    else:
        res = objects()[target][obj]
        if attr:
            res = res[attr]
    return res


def settings():
    '''
    icinga2 settings

    location
        installation directory

    package
        list of packages to install icinga
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
    cmdgroup
        group for the command file
    pidfile
        file to store icinga2 pid
    niceness
        priority of icinga process
    configuration_directory
        directory to store configuration
    objects
       dictionary to configure objects

       directory
           directory in which objects will be stored. The
           directory should be listed in "include_recursive"
           values
    icinga_conf
        include
            list of configuration files
            quotes have to be added for real directories
        include_recursive
            list of directory containing files configuration
    constants_conf
        values for constants conf
    zones_conf
        values for zones conf
    modules
        perfdata
            enabled
                enable the perfdata module
        livestatus
            enabled
                enable the livestatus module
        ido2db
            enabled
                enable the ido2db module

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        icinga2_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga2', registry_format='pack')
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

        # where the icinga2 objects configuration will be written
        dict_objects['directory'] = (locs['conf_dir'] +
                                     "/icinga2/conf.d/salt_generated")

        # generate default password
        icinga2_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga2', registry_format='pack')

        password_ido = icinga2_reg.setdefault('ido.db_password', __salt__[
            'mc_utils.generate_password']())
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga2', {
                'package': ['icinga2-bin',
                            'nagios-plugins',
                            'icinga2-common',
                            'icinga2-doc'],
                'has_pgsql': False,
                'create_pgsql': True,
                'has_mysql': False,
                'user': "nagios",
                'group': "nagios",
                'cmdgroup': "www-data",
                'pidfile': "/var/run/icinga2/icinga2.pid",
                'configuration_directory': locs['conf_dir']+"/icinga2",
                'niceness': 5,
                # because the subdictionary is very big, we take it
                # from another function but we can copy/paste it here
                'objects': dict_objects,
                'icinga_conf': {
                    'include': ['"constants.conf"',
                                '"zones.conf"',
                                '<itl>',
                                '<plugins>',
                                '"features-enabled/*.conf"'],
                    'include_recursive': ['"conf.d"'],
                },
                'constants_conf': {
                    'PluginDir': "\"/usr/lib/nagios/plugins\"",
                    'ZoneName': "NodeName",
                },
                'zones_conf': {
                    'object Endpoint NodeName': {
                        'host': "NodeName"},
                    'object Zone ZoneName': {
                        'endpoints': "[ NodeName ]"},
                },
                'modules': {
                    'perfdata': {'enabled': True},
                    'livestatus': {
                        'enabled': True,
                        'bind_host': "127.0.0.1",
                        'bind_port': 6558,
                        'socket_path': (
                            "/var/run/icinga2/cmd/livestatus"
                        )
                    },
                    'ido2db': {
                        'enabled': True,
                        'user': "nagios",
                        'group': "nagios",
                        'pidfile': "/var/run/icinga2/ido2db.pid",
                        'database': {
                            'type': "pgsql",
                            'host': "localhost",
                            'port': 5432,
                            'user': "icinga2_ido",
                            'password': password_ido,
                            'name': "icinga2_ido",
                        }
                    },
                },
            }
        )
        ido2db = data['modules']['ido2db']
        data['has_pgsql'] = 'pgsql' == ido2db['database']['type']
        data['has_mysql'] = 'mysql' == ido2db['database']['type']
        if data['has_pgsql']:
            ido2db['package'] = [
                'icinga2-ido-{0}'.format(
                    ido2db['database']['type'])]
        if data['has_pgsql'] and data['has_mysql']:
            raise ValueError('choose only one sgbd')
        if not (data['has_pgsql'] or data['has_mysql']):
            raise ValueError('choose at least one sgbd')
        __salt__['mc_macros.update_local_registry'](
            'icinga2', icinga2_reg,
            registry_format='pack')
        return data
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
    '''Add the object file in the file's list to be added'''
    if get:
        if get_objects_file:
            return add_configuration_object.objects[get_objects_file]
        else:
            return add_configuration_object.objects
    elif typen and filen and attrs:
        if filen not in add_configuration_object.objects:
            add_configuration_object.objects[filen] = []
        add_configuration_object.objects[
            filen].append({'type': typen,
                           'attrs': attrs,
                           'definition': definition})
    elif fromsettings:
        if filen not in add_configuration_object.objects:
            add_configuration_object.objects[filen] = []
        add_configuration_object.objects[
            filen].append({'fromsettings': fromsettings})
    print('end call add_configuration_object')


# global variable initialisation
add_configuration_object.objects = {}


def remove_configuration_object(filen=None, get=False, **kwargs):
    '''Add the file in the file's list to be removed'''
    if get:
        return remove_configuration_object.files
    elif filen:
        icingaSettings_complete = __salt__['mc_icinga2.settings']()
        # append " \"file\"" to the global variable
        filename = '/'.join([icingaSettings_complete[
            'objects']['directory'], filen])
        # it doesn't avoid injection, just allow the '"' char
        # in filename
        filename = filename.replace('"', '\"')
        remove_configuration_object.files += " \""+filename+"\""


# global variable initialisation
remove_configuration_object.files = ""


def add_auto_configuration_host_settings(hostname,
                                         hostgroup=False,
                                         attrs={},
                                         ssh_user='root',
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
    #    icingaSettings = copy.deepcopy(__salt__['mc_icinga2.settings']())
    #   save the ram (get only useful values)
    icingaSettings_complete = __salt__['mc_icinga2.settings']()
    icingaSettings = {}
    kwargs.setdefault(
        'objects',
        {'directory': icingaSettings_complete['objects']['directory']})

    kwargs.setdefault('hostname', hostname)
    kwargs.setdefault('hostgroup', hostgroup)

    if hostgroup:
        kwargs.setdefault('type', 'HostGroup')
        service_key_hostname = 'host.groups'
    else:
        kwargs.setdefault('type', 'Host')
        service_key_hostname = 'host.name'

    kwargs.setdefault('attrs', attrs)
    kwargs.setdefault('ssh_user', ssh_user)
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
        DRA,
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
        'nmd_www': "/home",  # TODO: must be modified
    }
    disks_spaces = dict()
    for mountpoint, path in mountpoints_path.items():
        if eval('disk_space_'+mountpoint):
            disks_spaces[mountpoint] = path

    # default values for dns_association service
    dns_hostname = ''
    dns_address = ''

    if (
        dns_association_hostname
        or dns_association
        or dns_reverse_association
        and 'address' in attrs
        and 'host_name' in attrs
    ):
        if 'host_name' in attrs:
            dns_hostname = attrs['host_name']
        else:
            dns_hostname = hostname

        if not dns_hostname.endswith('.'):
            dns_hostname = dns_hostname+'.'

        dns_address = attrs['address']

    # give the default values for commands parameters values
    # the keys are the services names,
    # not the commands names (use the service filename)
    services_default_attrs = {
        'backup_burp_age': {
            'service_description': "S_BACKUP_BURP_AGE",
            'import': ["ST_BACKUP_DAILY_ALERT"],
            'check_command': "CSSH_BACKUP_BURP",

            'vars.ssh_user': "root",
            'vars.ssh_addr': "backup.makina-corpus.net",
            'vars.ssh_port': "22",
            'vars.ssh_timeout': 10,
            'vars.warning': 1560,
            'vars.critical': 1800,
        },
        'backup_rdiff': {
            'service_description': "S_BACKUP_RDIFF",
            'import': ["ST_BACKUP_DAILY_ALERT"],
            'check_command': "CSSH_BACKUP",

            'vars.ssh_user': "root",
            'vars.ssh_addr': "backup.makina-corpus.net",
            'vars.ssh_port': "22",
            'vars.ssh_timeout': 10,
            'vars.command': ("/root/admin_scripts/nagios/"
                             "check_rdiff -r /data/backups/phpnet6"
                             " -w 24 -c 48 -l 2048 -p 24")
        },
        'beam_process': {
            'service_description': "Check beam proces",
            'import': ["ST_ALERT"],
            # 'notification_options': "w,c,r",
            'enable_notifications': 1,
            'check_command': "C_SNMP_PROCESS",

            'vars.process': "beam",
            'vars.warning': 0,
            'vars.critical': 0,
        },
        'celeryd_process': {
            'service_description': "Check celeryd process",
            'import': ["ST_ALERT"],
            # 'notification_options': "w,c,r",
            'enable_notifications': 1,
            'check_command': "C_SNMP_PROCESS",

            'vars.process': "python",
            'vars.warning': 1,
            'vars.critical': 0,
        },
        'cron': {
            'service_description': "S_PROC_CRON",
            'import': ["ST_SSH_PROC_CRON"],
            'check_command': "CSSH_CRON",
        },
        'ddos': {
            'service_description': "DDOS",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_DDOS",

            'vars.warning': 50,
            'vars.critical': 60,
        },
        'debian_updates': {
            'service_description': "S_DEBIAN_UPDATES",
            'import': ["ST_DAILY_NOALERT"],
            'check_command': "CSSH_DEBIAN_UPDATES",
        },
        'dns_association_hostname': {
            'service_description': "DNS_ASSOCIATION_hostname",
            'import': ["ST_DNS_ASSOCIATION_hostname"],
            'check_command': "C_DNS_EXTERNE_ASSOCIATION",
            'vars.hostname': dns_hostname,
            'vars.dns_address': dns_address,
            'vars.other_args': "",
        },
        'dns_association': {
            'default': {
                # default service_description is a prefix (see below)
                'service_description': "DNS_ASSOCIATION_",
                'import': ["ST_DNS_ASSOCIATION"],
                'check_command': "C_DNS_EXTERNE_ASSOCIATION",
                'vars.hostname': dns_hostname,
                'vars.dns_address': dns_address,
                'vars.other_args': "",
            }
        },
        DRA: {
            'default': {
                'service_description': "DNS_REVERSE_ASSOCIATION_",
                'import': ["ST_DNS_ASSOCIATION"],
                'check_command': "C_DNS_EXTERNE_REVERSE_ASSOCIATION",
                # 'vars.inaddr': "" # generated below from
                # dns_association dictionary
                #  'vars.hostname': ""
                'vars.other_args': "",
            },
        },
        'disk_space': {
            'default': {
                # it is prefix
                'service_description': "DISK_SPACE_",
                'import': ["ST_DISK_SPACE_"],
                'check_command': "C_SNMP_DISK",

                'vars.warning': 80,
                'vars.critical': 90,
            },
        },
        'drbd': {
            'service_description': "CHECK_DRBD",
            'import': ["ST_ALERT"],
            'icon_image': "services/heartbeat.png",
            'check_command': "CSSH_DRBD",

            'vars.command': ("'/root/admin_scripts/nagios/"
                             "check_drbd -d  0,1'"),
        },
        'epmd_process': {
            'service_description': "Check epmd process",
            'import': ["ST_ALERT"],
            # 'notification_options': "w,c,r",
            'enable_notifications': 1,
            'check_command': "C_SNMP_PROCESS",

            'vars.process': "epmd",
            'vars.warning': 0,
            'vars.critical': 0,
        },
        'erp_files': {
            'service_description': "CHECK_ERP_FILES",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_CUSTOM",

            'vars.command': ("/var/makina/alma-job/job"
                             "/supervision/check_erp_files.sh"),
        },
        'fail2ban': {
            'service_description': "S_FAIL2BAN",
            'import': ["ST_ROOT"],
            'enable_notifications': 1,
            'check_command': "C_SNMP_PROCESS",

            'vars.process': "fail2ban-server",
            'vars.warning': 0,
            'vars.critical': 0,
        },
        'gunicorn_process': {
            'service_description': "Check gunicorn process",
            'import': ["ST_ALERT"],
            # 'notification_options': "w,c,r",
            'enable_notifications': 1,
            'check_command': "C_SNMP_PROCESS",

            'vars.process': "gunicorn_django",
            'vars.warning': 0,
            'vars.critical': 0,
        },
        'haproxy': {
            'service_description': "haproxy_stats",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_HAPROXY",
            'vars.command': ("/root/admin_scripts/nagios/"
                             "check_haproxy_stats.pl -p "
                             "web -w 80 -c 90"),
        },
        'ircbot_process': {
            'service_description': "S_IRCBOT_PROCESS",
            'import': ["ST_HOURLY_ALERT"],
            'check_command': "C_PROCESS_IRCBOT_RUNNING",
        },
        'load_avg': {
            'service_description': "LOAD_AVG",
            'import': ["ST_LOAD_AVG"],
            'check_command': "C_SNMP_LOADAVG",

            'vars.other_args': "",
        },
        'mail_cyrus_imap_connections': {
            'service_description': "S_MAIL_CYRUS_IMAP_CONNECTIONS",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_CYRUS_CONNECTIONS",

            'vars.warning': 300,
            'vars.critical': 900,
        },
        'mail_imap': {
            'service_description': "S_MAIL_IMAP",
            'import': ["ST_ALERT"],
            'check_command': "C_MAIL_IMAP",

            'vars.warning': 1,
            'vars.critical': 3,
        },
        'mail_imap_ssl': {
            'service_description': "S_MAIL_IMAP_SSL",
            'import': ["ST_ALERT"],
            'check_command': "C_MAIL_IMAP_SSL",

            'vars.warning': 1,
            'vars.critical': 3,
        },
        'mail_pop': {
            'service_description': "S_MAIL_POP",
            'import': ["ST_ALERT"],
            'check_command': "C_MAIL_POP",

            'vars.warning': 1,
            'vars.critical': 3,
        },
        'mail_pop_ssl': {
            'service_description': "S_MAIL_POP_SSL",
            'import': ["ST_ALERT"],
            'check_command': "C_MAIL_POP_SSL",

            'vars.warning': 1,
            'vars.critical': 3,
        },
        'mail_pop_test_account': {
            'service_description': "S_MAIL_POP3_TEST_ACCOUNT",
            'import': ["ST_ALERT"],
            'check_command': "C_POP3_TEST_SIZE_AND_DELETE",

            'vars.warning1': 52488,
            'vars.critical1': 1048576,
            'vars.warning2': 100,
            'vars.critical2': 2000,
            'vars.mx': "@makina-corpus.com",
        },
        'mail_server_queues': {
            'service_description': "S_MAIL_SERVER_QUEUES",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_MAILQUEUE",

            'vars.warning': 50,
            'vars.critical': 100,
        },
        'mail_smtp': {
            'service_description': "S_MAIL_SMTP",
            'import': ["ST_ALERT"],
            'check_command': "C_MAIL_SMTP",

            'vars.warning': 1,
            'vars.critical': 3,
        },
        'megaraid_sas': {
            'service_description': "CHECK_MEGARAID_SAS",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_MEGARAID_SAS",

            'vars.command': ("'/root/admin_scripts/"
                             "nagios/check_megaraid_sas'"),
        },
        'memory': {
            'service_description': "MEMORY",
            'import': ["ST_MEMORY"],
            'check_command': "C_SNMP_MEMORY",

            'vars.warning': 80,
            'vars.critical': 90,
        },
        'memory_hyperviseur': {
            'service_description': "MEMORY_HYPERVISEUR",
            'import': ["ST_MEMORY_HYPERVISEUR"],
            'check_command': "C_SNMP_MEMORY",

            'vars.warning': 95,
            'vars.critical': 99,
        },
        'mysql_process': {
            'service_description': "S_MYSQL_PROCESS",
            'import': ["ST_ALERT"],
            'check_command': "C_SNMP_PROCESS",

            'vars.process': "mysql",
            'vars.warning': 0,
            'vars.critical': 0,
        },
        'network': {
            'default': {
                # prefix
                'service_description': "NETWORK_",
                'import': ["ST_NETWORK_"],
                'check_command': "C_SNMP_NETWORK",

                'vars.interface': "eth0",
                'vars.other_args': "",
            },
        },
        'ntp_peers': {
            'service_description': "S_NTP_PEERS",
            'import': ["ST_ROOT"],
            'check_command': "CSSH_NTP_PEER",
        },
        'ntp_time': {
            'service_description': "S_NTP_TIME",
            'import': ["ST_ROOT"],
            'check_command': "CSSH_NTP_TIME",
        },
        'only_one_nagios_running': {
            'service_description': "S_ONLY_ONE_NAGIOS_RUNNING",
            'import': ["ST_HOURLY_ALERT"],
            'check_command': "C_CHECK_ONE_NAGIOS_ONLY",
        },
        'postgres_port': {
            'service_description': "S_POSTGRESQL_PORT",
            'import': ["ST_ROOT"],
            'icon_image': "services/sql4.png",
            'check_command': "check_tcp",

            'vars.port': 5432,
            'vars.warning': 2,
            'vars.critical': 8,
        },
        'postgres_process': {
            'service_description': "S_POSTGRESQL_PROCESS",
            'import': ["ST_ALERT"],
            'icon_image': "services/sql4.png",
            'check_command': "C_SNMP_PROCESS",

            'vars.process': "postgres",
            'vars.warning': 0,
            'vars.critical': 0,
        },
        'prebill_sending': {
            'service_description': "CHECK_PREBILL_SENDING",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_CUSTOM",

            'vars.command': ("/var/makina/alma-job/job/"
                             "supervision/check_prebill_sending.sh"),
        },
        'raid': {
            'service_description': "CHECK_MD_RAID",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_RAID_SOFT",

            'vars.command': "'/root/admin_scripts/nagios/check_md_raid'",
        },
        'sas': {
            'service_description': "S_SAS",
            'import': ["ST_ROOT"],
            'check_command': "CSSH_SAS2IRCU",

            'vars.command': ("/root/admin_scripts/check_nagios"
                             "/check_sas2ircu/check_sas2ircu"),
        },
        'snmpd_memory_control': {
            'service_description': "S_SNMPD_MEMORY_CONTROL",
            'import': ["ST_ALERT"],
            'check_command': "C_SNMP_PROCESS_WITH_MEM",

            'vars.process': "snmpd",
            'vars.warning': "0,1",
            'vars.critical': "0,1",
            'vars.memory': "256,512",
        },
        'solr': {
            'default': {
                'service_description': "SOLR_",
                'import': ["ST_WEB_PUBLIC"],
                'check_command': "C_HTTP_STRING_SOLR",

                'vars.hostname': "h",
                'vars.port': 80,
                'vars.url': "/",
                'vars.warning': 1,
                'vars.critical': 5,
                'vars.timeout': 8,
                'vars.strings': [],
                'vars.other_args': "",
            },
        },
        'ssh': {
            'service_description': "S_SSH",
            'import': ["ST_ROOT"],
            'check_command': "check_tcp",

            'vars.port': 22,
            'vars.warning': 1,
            'vars.critical': 4,
        },
        'supervisord_status': {
            'service_description': "S_SUPERVISORD_STATUS",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_SUPERVISOR",

            'vars.command': ("/home/zope/adria/rcse/"
                             "production-2014-01-"
                             "23-14-27-01/bin/supervisorctl"),
        },
        'swap': {
            'service_description': "CHECK_SWAP",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_RAID_SOFT",

            'vars.command': ("'/root/admin_scripts/"
                             "nagios/check_swap -w 80%% -c 50%%'"),
        },
        'tiles_generator_access': {
            'service_description': "Check tiles generator access",
            'import': ["ST_ALERT"],
            # 'notification_options': "w,c,r",
            'enable_notifications': 1,
            'check_command': "check_http_vhost_uri",

            'vars.hostname': "vdm.makina-corpus.net",
            'vars.url': "/vdm-tiles/status/",
        },
        'ware_raid': {
            'service_description': "CHECK_3WARE_RAID",
            'import': ["ST_ALERT"],
            'check_command': "CSSH_RAID_3WARE",

            'vars.command': "/root/admin_scripts/nagios/check_3ware_raid",
        },
        'web_apache_status': {
            'service_description': "WEB_APACHE_STATUS",
            'import': ["ST_WEB_APACHE_STATUS"],
            'check_command': "C_APACHE_STATUS",

            'vars.warning': 4,
            'vars.critical': 2,
            'vars.other_args': "",
        },
        'web_openid': {
            'default': {
                'service_description': "WEB_OPENID_",
                'import': ["ST_WEB_PUBLIC"],
                'check_command': "C_HTTPS_OPENID_REDIRECT",

                'vars.hostname': hostname,
                'vars.url': "/",
                'vars.warning': 1,
                'vars.critical': 5,
                'vars.timeout': 8,
            },
        },
        'web': {
            'default': {
                'service_description': "WEB_",
                'vars.hostname': hostname,
                'import': ["ST_WEB_PUBLIC"],
                'check_command': "C_HTTP_STRING",

                'vars.url': "/",
                'vars.warning': 2,
                'vars.critical': 3,
                'vars.timeout': 8,
                'vars.strings': [],
                'vars.other_args': "",
            },
        },
    }

    # add the services_attrs 'default' in all services
    # in services_default_attrs # in order to add
    # directives for all services (like contact_groups)
    if 'default' in services_attrs:
        for name, service in services_default_attrs.items():
            if name not in services_attrs:
                services_attrs[name] = {}
            if name not in ['dns_association',
                            DRA,
                            'disk_space',
                            'network',
                            'solr',
                            'web_openid',
                            'web']:
                services_default_attrs[name] = dict(
                    services_default_attrs[name].items() +
                    services_attrs['default'].items())
            else:
                services_default_attrs[name]['default'] = dict(
                    services_default_attrs[name]['default'].items() +
                    services_attrs['default'].items())
        services_attrs.pop('default', None)

    # override the commands parameters values
    # we complete the services_attrs dictionary
    # with values from services_default_attrs

    # override dns_association subdictionary
    if 'dns_association' not in services_attrs:
        services_attrs['dns_association'] = services_default_attrs[
            'dns_association']
        services_attrs[
            'dns_association'
        ]['default'][
            'service_description'
        ] = services_default_attrs[
            'dns_association']['default'][
                'service_description'] + 'default'
    else:
        for name, dns in services_attrs['dns_association'].items():
            # generate the service_description if not given
            if 'service_description' not in dns:
                services_attrs['dns_association'][
                    name
                ][
                    'service_description'
                ] = services_default_attrs[
                    'dns_association'
                ]['default']['service_description'] + name
            for key, value in services_default_attrs[
                'dns_association'
            ]['default'].items():
                if key not in dns:
                    services_attrs['dns_association'][name][key] = value

    # override dns_reverse_assocation subdictionary
    if DRA not in services_attrs:
        services_attrs[DRA] = {}
        # the dictionary is not set, we generate it
        # from dns_association dictionary
        # (we suppose all ips are ipv4 that is bad):
        for name, dns in services_attrs['dns_association'].items():
            services_attrs[DRA][name] = copy.deepcopy(
                services_default_attrs[DRA]['default'])
            services_attrs[DRA][name][
                'service_description'] = services_default_attrs[
                    DRA]['default']['service_description']+name

            address_splitted = dns['vars.dns_address'].split('.')
            # tanslate a.b.c.d in d.c.b.a
            inaddr = '.'.join(address_splitted[::-1])
            inaddr = inaddr + '.in-addr.arpa.'
            services_attrs[DRA][name]['vars.inaddr'] = inaddr
            services_attrs[DRA][name][
                'vars.hostname'] = dns['vars.hostname']
    else:
        # the dictionary is set, we merging normally
        for name, dns in services_attrs[DRA].items():
            if 'service_description' not in dns:
                services_attrs[DRA][name][
                    'service_description'] = services_default_attrs[
                        'dns_association'][name][
                            'service_reverse_description'] + name
            for key, value in services_default_attrs[DRA]['default'].items():
                if key not in dns:
                    services_attrs[DRA][name][key] = value

    # override network subdictionary
    if 'network' not in services_attrs:
        services_attrs['network'] = services_default_attrs['network']
        services_attrs['network'][
            'default']['service_description'] = services_default_attrs[
                'network']['default']['service_description'] + 'default'
        services_attrs['network'][
            'default']['import'] = [
                services_default_attrs['network']['default']['import'][0] +
                services_default_attrs['network'][
                    'default']['vars.interface'].upper()]
    else:
        for name, network in services_attrs['network'].items():
            # generate the service_description if not given
            if 'service_description' not in network:
                if 'vars.interface' in services_attrs['network'][name]:
                    services_attrs['network'][name][
                        'service_description'] = (
                            services_default_attrs['network'][
                                'default']['service_description'] +
                            services_attrs['network'][
                                name]['vars.interface'].upper())
                else:
                    services_attrs['network'][name][
                        'service_description'] = (
                            services_default_attrs['network'][
                                'default']['service_description'] +
                            services_default_attrs['network'][
                                'default']['vars.interface'].upper())
            if 'import' not in network:
                if 'vars.interface' in services_attrs['network'][name]:
                    services_attrs['network'][
                        name]['import'] = (
                            services_default_attrs['network'][
                                'default']['import'] +
                            services_attrs['network'][
                                name]['vars.interface'].upper())
                else:
                    # add the prefix to the import
                    services_attrs['network'][
                        name]['import'] = [
                            services_default_attrs['network'][
                                'default']['import'][0] +
                            i.upper()
                            for i in services_default_attrs['network'][
                                'default']['vars.interface']]

            for key, value in services_default_attrs[
                'network'
            ]['default'].items():
                if key not in network:
                    services_attrs['network'][name][key] = value

    # override solr subdictionary
    if 'solr' not in services_attrs:
        services_attrs['solr'] = services_default_attrs['solr']
        services_attrs['solr']['default'][
            'service_description'] = services_default_attrs[
                'solr']['default']['service_description'] + 'default'
    else:
        for name, solr in services_attrs['solr'].items():
            # generate the service_description if not given
            if 'service_description' not in solr:
                services_attrs['solr'][name][
                    'service_description'] = (
                        services_default_attrs['solr']['default'][
                            'service_description'] + name)
            for key, value in services_default_attrs[
                'solr'
            ]['default'].items():
                if key not in solr:
                    services_attrs['solr'][name][key] = value
            # transform list of values in
            # string ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_attrs['solr'][name]['vars.strings'], list):
                str_list = services_attrs['solr'][name]['vars.strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [value.replace('"', '\\\\"') for value in str_list]
                services_attrs['solr'][name]['vars.strings'] = (
                    '"' + '" -s "'.join(str_list) + '"')

    # override web_openid subdictionary
    if 'web_openid' not in services_attrs:
        services_attrs['web_openid'] = services_default_attrs['web_openid']
        services_attrs['web_openid']['default'][
            'service_description'] = services_default_attrs[
                'web_openid']['default']['service_description'] + 'default'
    else:
        for name, web_openid in services_attrs['web_openid'].items():
            # generate the service_description if not given
            if 'service_description' not in web_openid:
                services_attrs['web_openid'][name][
                    'service_description'] = services_default_attrs[
                        'web_openid']['default']['service_description'] + name
            for key, value in services_default_attrs[
                'web_openid'
            ]['default'].items():
                if key not in web_openid:
                    services_attrs['web_openid'][name][key] = value

    # override web subdictionary
    if 'web' not in services_attrs:
        services_attrs['web'] = services_default_attrs['web']
        services_attrs['web']['default'][
            'service_description'] = services_default_attrs[
                'web']['default']['service_description'] + 'default'
    else:
        for name, web in services_attrs['web'].items():
            # generate the service_description if not given
            if 'service_description' not in web:
                services_attrs['web'][name][
                    'service_description'] = services_default_attrs[
                        'web']['default']['service_description'] + name
            for key, value in services_default_attrs[
                'web'
            ]['default'].items():
                if key not in web:
                    services_attrs['web'][name][key] = value
            # transform list of values
            # in string ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_attrs['web'][name]['vars.strings'], list):
                str_list = services_attrs['web'][name]['vars.strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [value.replace('"', '\\\\"') for value in str_list]
                services_attrs['web'][name][
                    'vars.strings'] = '"' + '" -s "'.join(str_list) + '"'

    # override mountpoints subdictionaries
    # for each disk_space, build the dictionary:
    # priority for values
    if 'disk_space' not in services_attrs:
        services_attrs['disk_space'] = {}
    # we can't merge default dictionary yet because priorities
    # will not be respected
    if 'default' not in services_attrs['disk_space']:
        services_attrs['disk_space']['default'] = {}

    for mountpoint, path in mountpoints_path.items():
        if mountpoint in disks_spaces:  # the check is enabled
            if mountpoint not in services_default_attrs['disk_space']:
                services_default_attrs['disk_space'][
                    mountpoint] = copy.deepcopy(
                        services_default_attrs['disk_space']['default'])
            services_attrs['disk_space'][mountpoint] = dict(
                services_default_attrs['disk_space']['default'].items() +
                services_default_attrs['disk_space'][mountpoint].items())
            services_attrs['disk_space'][mountpoint] = dict(
                services_attrs['disk_space'][mountpoint].items() +
                services_attrs['disk_space']['default'].items())
            services_attrs['disk_space'][mountpoint] = dict(
                services_attrs['disk_space'][mountpoint].items() +
                services_attrs['disk_space'][mountpoint].items())

            if (
                services_attrs['disk_space'][
                    mountpoint
                ]['service_description'] == services_default_attrs[
                    'disk_space']['default']['service_description']
            ):
                services_attrs['disk_space'][
                    mountpoint]['service_description'] = (
                        services_attrs['disk_space'][mountpoint][
                            'service_description'] +
                        disks_spaces[mountpoint].upper())
            services_attrs['disk_space'][
                mountpoint]['import'] = [
                    services_attrs['disk_space'][mountpoint]['import'][0] +
                    disks_spaces[mountpoint].replace(
                        '/', '_').replace('_', '/', 1).upper()]
            services_attrs['disk_space'][
                mountpoint]['vars.path'] = disks_spaces[mountpoint]

    # remove default dictionary
    if 'default' in services_attrs['disk_space']:
        services_attrs['disk_space'].pop('default', None)

    # override others values (type are string or int)
    if not isinstance(services_attrs, dict):
        services_attrs = {}

    for name, command in services_default_attrs.items():
        if name not in ['dns_association', DRA,
                        'disk_space', 'network', 'solr',
                        'web_openid', 'web']:
            if name not in services_attrs:
                services_attrs[name] = {}
            services_attrs[name] = dict(
                services_default_attrs[name].items() +
                services_attrs[name].items())

    # generate the complete check command (we can't do a loop
    # before we have to give the good order for arguments)
    # don't generate the complete check command because it is
    # icinga2

    # add the host_name or hostgroup_name in each service
    # and don't remove directives begining with "vars."
    # (because it is icinga2)

    for service in services:
        if service in services_attrs:
            services_attrs[service][service_key_hostname] = hostname
            # TODO: fix this
            services_attrs[service][
                'service_description'] = (
                    hostname
                    + '__'
                    + services_attrs[service]['service_description'])

    for service in services_loop:
        if service in services_attrs:
            for subservice in services_attrs[service]:
                services_attrs[service][subservice][
                    service_key_hostname] = hostname
                # TODO: fix this
                services_attrs[service][subservice][
                    'service_description'
                ] = hostname + '__' + services_attrs[
                    service][subservice]['service_description']

    kwargs.setdefault('services_attrs', services_attrs)

    icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings,
                                                     kwargs)
    print('end call add_auto_configuration_host_settings')
    return icingaSettings


def add_auto_configuration_host(hostname=None,
                                hostgroup=False,
                                attrs={},
                                ssh_user='root',
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
    if get:
        if hostname:
            return add_auto_configuration_host.objects[hostname]
        else:
            return add_auto_configuration_host.objects
    else:
        # we need some variables to write the state

        # if fromsettings is used, we need to get some arguments values
        if fromsettings:
            host = get_settings_for_object(
                'autoconfigured_hosts_definitions', fromsettings)
            if 'hostgroup' in host:
                hostgroup = host['hostgroup']

        #    icingaSettings = copy.deepcopy(__salt__['mc_icinga2.settings']())
        #   save the ram (get only useful values)
        icingaSettings_complete = __salt__['mc_icinga2.settings']()
        icingaSettings = {}
        kwargs.setdefault(
            'objects',
            {'directory': (
                icingaSettings_complete['objects']['directory'])})
        kwargs.setdefault('hostname', hostname)
        kwargs.setdefault('hostgroup', hostgroup)
        if hostgroup:
            kwargs.setdefault('type', 'HostGroup')
            service_subdirectory = 'hostgroups'
            service_key_hostname = 'hostgroup_name'
        else:
            kwargs.setdefault('type', 'Host')
            service_subdirectory = 'hosts'
            service_key_hostname = 'host_name'
        # we set the filename here
        filen = '/'.join([service_subdirectory, hostname+'.conf'])
        kwargs.setdefault('file', filen)
        kwargs.setdefault('state_name_salt', replace_chars(filen))
        icingaSettings = __salt__['mc_utils.dictupdate'](
            icingaSettings, kwargs)

        # we remember the host to add:

        if fromsettings:
            add_auto_configuration_host.objects[hostname] = {
                'fromsettings': fromsettings}
        else:
            add_auto_configuration_host.objects[hostname] = {
                'hostname': hostname,
                'hostgroup': hostgroup,
                'attrs': attrs,
                'ssh_user': ssh_user,
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
                DRA: dns_reverse_association,
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
                'disk_space_var_backups_bluemind': (
                    disk_space_var_backups_bluemind),
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


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
