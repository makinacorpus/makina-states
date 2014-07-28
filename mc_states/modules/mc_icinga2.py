# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga2:

mc_icinga2 / icinga functions
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

import re

__name = 'icinga2'

log = logging.getLogger(__name__)

def objects_icinga1():
    locs = __salt__['mc_locations.settings']()
    data = __salt__['mc_icinga.objects']()
    data['directory'] = locs['conf_dir']+"/icinga2/conf.d/salt_generated"
    return data


def objects_icinga2(): 
    '''function to translate objects() dictionary for icinga2 
       the objects() dictionary can be translated manually in order to improve performance
       this function is here, only to reuse the icinga dictionary

       http://docs.icinga.org/icinga2/latest/doc/module/icinga2/toc#!/icinga2/latest/doc/module/icinga2/chapter/monitoring-basics#check-commands
       https://github.com/Icinga/icinga2-migration
    '''

    # TODO: translate durations in minutes

    # ARGx are not beautiful arguments, we will try to give name. This dictionary was used in mc_icinga to do the reverse operation (association a named value to ARGx variable)
    cssh_params = ['ssh_user', 'ssh_addr', 'ssh_port', 'ssh_timeout']

    check_command_args = {
        'CSSH_BACKUP_BURP': ['ssh_user', 'ssh_addr', 'ssh_port', 'warning', 'critical'],
        'CSSH_BACKUP': ['ssh_user', 'ssh_addr', 'ssh_port', 'warning', 'critical'],
        'C_SNMP_PROCESS': ['process', 'warning', 'critical'],
        'CSSH_CRON': cssh_params,
        'CSSH_DDOS': cssh_params+['warning', 'critical'],
        'CSSH_DEBIAN_UPDATES': cssh_params,
        'C_DNS_EXTERNE_ASSOCIATION': ['hostname', 'other_args'],
        'C_DNS_EXTERNE_REVERSE_ASSOCIATION': ['inaddr', 'hostname', 'other_args'],
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
        'C_POP3_TEST_SIZE_AND_DELETE': ['warning1', 'critical1', 'warning2', 'critical2', 'mx'],
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
        'C_SNMP_PROCESS_WITH_MEM': ['process', 'warning', 'critical', 'memory'],
        'C_HTTP_STRING_SOLR': ['hostname', 'port', 'warning', 'critical', 'timeout', 'strings', 'other_args'],
        'CSSH_SUPERVISOR': cssh_params+['command'],
        'check_http_vhost_uri': ['hostname', 'url'],
        'CSSH_RAID_3WARE': cssh_params+['command'],
        'C_APACHE_STATUS': ['warning', 'critical', 'other_args'],
        'C_HTTPS_OPENID_REDIRECT': ['hostname', 'url', 'warning', 'critical', 'timeout'],
        'C_HTTP_STRING': ['hostname', 'url', 'warning', 'critical', 'timeout', 'strings', 'other_args'],
        'C_HTTP_STRING_AUTH': ['hostname', 'url', 'warning', 'critical', 'timeout', 'strings', 'other_args'],
        'C_HTTP_STRING_ONLY': ['hostname', 'url', 'warning', 'critical', 'timeout', 'strings', 'other_args'],
        'C_HTTPS_STRING_ONLY': ['hostname', 'url', 'warning', 'critical', 'timeout', 'strings', 'other_args'],
        'C_CHECK_LABORANGE_LOGIN': ['hostname', 'url', 'warning', 'critical', 'timeout', 'strings', 'other_args'],
        'C_CHECK_LABORANGE_STATS': ['hostname', 'url', 'warning', 'critical', 'timeout', 'strings', 'other_args'],
        'check_https': ['hostname', 'url', 'warning', 'critical', 'timeout', 'strings', 'other_args'],
    }

    # build the check command with args
    src = objects_icinga1()
    res = {}

    # directory
    res['directory'] = src['directory']

    # objects definitions
    res['objects_definitions'] = {}

    def _unquoting(value):
        '''remove begining and ending quotes'''
        value = str(value)
        if value.startswith('\\\'') or value.startswith('\\"'):
            value=value[2:]
        elif value.startswith('\'') or value.startswith('"'):
            value=value[1:]
        if value.endswith('\\\'') or value.endswith('\\"'):
            value=value[:-2]
        elif value.endswith('\'') or value.endswith('"'):
            value=value[:-1]
        # because of in the template, the value are enclosed with '"' character, we escape the quotes
        value = value.replace('"', '\\"')
        return value

    def _check_command_arguments(check_command):
        '''split a check_command in order to get the arguments'''
        # we have to split the "!"
        command_splitted=check_command.split('!')
        res = {}
        res['check_command']=command_splitted[0]
        if command_splitted[0] in check_command_args:
            nb_args = len(check_command_args[command_splitted[0]])
            for i, val in enumerate(command_splitted[1:]):
                if i < nb_args: # because some commands ends with "!!!!" but the ARG are not used in command_line
                    res['vars.'+check_command_args[command_splitted[0]][i]] = val
        else:
            for i, val in enumerate(command_splitted[1:]):
                res['vars.ARG'+str(i+1)] = val
        return res

    def _command_line_arguments(command_line):
        '''generate arguments dictionary from a command_line'''
        res={}
        command_splitted=[]

        # bad method to split command_line
        tmp=[]
        spaced_arg=False
        for arg in re.split(' |=', command_line): # split on space and =
            if arg.startswith('\'') or arg.startswith('\\\'') or arg.startswith('\"') or arg.startswith('\\\"'):
                spaced_arg=True
            if arg.endswith('\'') or arg.endswith('\\\'') or  arg.endswith('\"') or arg.endswith('\\\"'):
                spaced_arg=False
            tmp.append(arg)
            if not spaced_arg:
                tmpstr = " ".join(tmp)
                if tmpstr:
                    command_splitted.append(tmpstr) # merge the argument on quotes (bad)
                tmp=[]


#        res['command'] = _format(command_splitted[0])
        res['command'] = command_splitted[0]
        n_args = len(command_splitted)-1
        i_args = 1

        # replace $ARGx$ with the names found in check_command_args
        if res['command'] in check_command_args:
            argx = 1
            for param in check_command_args[command_name]:
                i_args = 1
                while i_args <= n_args:
                    command_splitted[i_args] = command_splitted[i_args].replace('$ARG'+str(argx)+'$', '$'+str(param)+'$')
                    i_args += 1
                argx += 1

        # remove quotes
        i_args = 1
        while i_args <= n_args:
            command_splitted[i_args] = _unquoting(command_splitted[i_args])
            i_args += 1

        # find the couple of arguments
        res['arguments'] = {}
        i_args = 1
        while i_args <= n_args:
            if not command_splitted[i_args]: # to remove blanks
                i_args += 1
            else:
                if i_args < n_args:
                    if (not command_splitted[i_args+1].startswith('-')) and (not command_splitted[i_args].startswith('$')): # bad method to detect the couple of arguments "-a 1", the "1" doesn't begin with '-'
                        res['arguments'][command_splitted[i_args]] = command_splitted[i_args+1]
                        i_args += 2
                    else:
                        res['arguments'][command_splitted[i_args]] = {} 
                        i_args += 1
                else:
                    res['arguments'][command_splitted[i_args]] = {} 
                    i_args += 1
        return res

    def _translate_attrs(obj_type, res_type, obj_attrs):
        '''function to translate attrs subdictionary
           it is used to translate objects_definitions and autoconfigured_hosts_definitions
        '''
        res={}
        for key,value in obj_attrs.items():

            # specific translation
            if 'command_line' == key: # translate the command_line attributes
                command = _command_line_arguments(value)
                res['command'] = command['command']
                res['arguments'] = command['arguments']
            elif 'check_command' == key: # translate the check_command attributes
                command = _check_command_arguments(value)
                for key, value in command.items():
                    res[key] = value

            elif key in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']: # for timeperiods
                if 'ranges' not in res:
                    res['ranges'] = {}
#                res['ranges'][_format(key)] = _format(value)
                res['ranges'][key] = value

            # global translation
            else:
                # check if the attribute is removed
                if obj_type in attrs_used_as_name and key == attrs_used_as_name[obj_type]:
                    # the attribute used as name is removed from attrs list
                    continue
                elif key in attrs_removed: # attribute removed
                    continue

                # translate the attribute key
                if key in attrs_renamed:
                    res_key = attrs_renamed[key]
                elif 'name' == key and obj_type in attrs_used_as_name and attrs_used_as_name[obj_type] not in obj_attrs: # translate "name" attrs
                    res_key = attrs_used_as_name[obj_type]
                elif key.startswith('cmdarg_'): # translate the old argument prefix
                    res_key = key.replace('cmdarg_', 'vars.')
                elif key in ['_SERVICE_ID', '_HOST_ID']: # theses arguments seems to be not supported
                    continue 
                else:
                    res_key = key

                # create the lists if needed and format the value 
                if key in attrs_force_list:
                    res_value = value.split(',') 
                else:
                    res_value = value

                # add the attribute
                res[res_key] = res_value


        if 'timeperiod' == obj_type:
            if 'import' not in res:
                res['import'] = []
            res["import"] = res["import"] + ["legacy-timeperiod"] + res['import']
        elif 'command' == obj_type and 'CheckCommand' == res_type: 
            if 'import' not in res:
                res['import'] = []
            res['import'] = ["plugin-check-command"] + res['import']
        elif 'command' == obj_type and 'NotificationCommand' == res_type:
            if 'import' not in res:
                res['import'] = []
            res['import'] = ["plugin-notification-command"] + res['import']
        return res


    types_renamed = {
        'timeperiod': "TimePeriod",
        'contactgroup': "UserGroup",
        'contact': "User",
        'servicegroup': "ServiceGroup",
        'service': "Service",
        'hostgroup': "HostGroup",
        'host': "Host",
        'command': "CheckCommand",
    }
    attrs_used_as_name = {
        'timeperiod': "timeperiod_name",
        'contactgroup': "contactgroup_name",
        'contact': "contact_name",
        'servicegroup': "servicegroup_name",
        'service': "service_description",
        'hostgroup': "hostgroup_name",
        'host': "host_name",
        'command': "command_name",
    }
    attrs_renamed = {
        'use': "import",
        'alias': "display_name",
        # timeperiods
        'active_checks_enabled': "enable_active_checks",
        'passive_checks_enabled': "enable_passive_checks",
        'event_handler_enabled': "enable_event_handler",
        'low_flap_threshold': "flapping_threshold",
        'high_flap_threshold': 'flapping_threshold',
        'flap_detection_enabled': "enable_flapping",
#TODO:
#        'process_perf_data': "enabled_perfata",
        'notifications_enabled': "enable_notifications",
        # contactgroups
        # contacts
        'contactgroups': "groups",
        # servicegroups
        # services
        'is_volatile': "volatile",
        # hostgroups
        # hosts
    }
    attrs_force_list = [
        'use',
        # contacts
        'contactgroups',
        # services
        'contact_groups',
        # hosts
        'parents',
    ]
    attrs_removed = [ # from icinga2-migration php script
        'name',
        'register',
        # timeperiods
        # contactgroups
        # contacts
        'service_notification_period',
        'host_notification_period',
        'host_notification_options',
        'service_notification_options',
        'service_notification_commands',
        'host_notification_commands',
        'host_notifications_enabled',
        'service_notifications_enabled',
        'address1',
        'address2',
        'address3',
        'address4',
        'address5',
        'address6',
        # servicegroups
        # services
        'initial_state',
        'obsess_over_service',
        'check_freshness',
        'freshness_threshold',
        'flap_detection_options',
        'failure_prediction_enabled',
        'retain_status_information',
        'stalking_options',
        'parallelize_check',
        'notification_interval',
        'first_notification_delay',
        'notification_period',
        'notification_options',
        # hostgroups
        # hosts
        'host_name',
        'initial_state',
        'obsess_over_host',
#        'check_freshness',
#        'freshness_threshold',
#        'flap_detection_options',
#        'failure_prediction_enabled',
#        'retain_status_information',
        'retain_nonstatus_information',
#        'stalking_options',
        'statusmap_image',
        '2d_coords',
#        'parallelize_check',
#        'notification_interval',
#        'first_notification_delay',
#        'notification_period',
#        'notification_options',

# TODO: because the configuration is invalid 
         'normal_check_interval',
         'retry_check_interval',
         'process_perf_data',
         'parents',
         'hostgroups',

# TODO:
# because, we don't have done the contact migration (http://docs.icinga.org/icinga2/latest/doc/module/icinga2/toc#!/icinga2/latest/doc/module/icinga2/chapter/migration#manual-config-migration-hints-contacts-users)
         'contacts',
         'contact_groups',

    ]
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
    services_loop = [
        'dns_association',
        'dns_reverse_association',
        'disk_space',
        'network',
        'solr',
        'web_openid',
        'web',
    ]

    services_enabled = dict()
    for name, obj in src['objects_definitions'].items():
        # global changes
        res['objects_definitions'][name]={}
        res['objects_definitions'][name]['attrs'] = {}
        res['objects_definitions'][name]['file'] = obj['file'].replace('.cfg', '.conf') # the extension of filenames is changed

        # translate the type of the object
        if obj['type'] in types_renamed:
            if name in ['command_meta_notify']: # hack 
                res['objects_definitions'][name]['type'] = "NotificationCommand"
            else:
                res['objects_definitions'][name]['type'] = types_renamed[obj['type']]
        else:
            res['objects_definitions'][name]['type'] = obj['type'] 

        # determine if the object is a template or not
        if 'attrs' in obj and 'register' in obj['attrs'] and 0 == obj['attrs']['register']:
            res['objects_definitions'][name]['template']=True
        else:
            res['objects_definitions'][name]['template']=False

        # find the object name
        if 'attrs' in obj and 'name' in obj['attrs']: # priority for the name attribute (change this generates an invalid configuration)
            res['objects_definitions'][name]['name'] = obj['attrs']['name']
        elif obj['type'] in attrs_used_as_name and 'attrs' in obj and attrs_used_as_name[obj['type']] in obj['attrs']:
            res['objects_definitions'][name]['name'] = obj['attrs'][attrs_used_as_name[obj['type']]]
        else:
            res['objects_definitions'][name]['name'] = name

        # translate the attributes
        res['objects_definitions'][name]['attrs'] = _translate_attrs(obj['type'], res['objects_definitions'][name]['type'], obj['attrs'])

    # purge_definitions
    res['purge_definitions'] = src['purge_definitions']

    # autoconfigured_hosts
    #res['autoconfigured_hosts_definitions'] = src['autoconfigured_hosts_definitions']
    res['autoconfigured_hosts_definitions'] = {}
    for name, params in src['autoconfigured_hosts_definitions'].items():
        res['autoconfigured_hosts_definitions'][name] = {}

        # translate the host attrs
        if 'attrs' in params:
            if 'hostgroup' in params and params['hostgroup']:
                res['autoconfigured_hosts_definitions'][name]['attrs'] = _translate_attrs('hostgroup', types_renamed['hostgroup'], params['attrs'])
            else:
                res['autoconfigured_hosts_definitions'][name]['attrs'] = _translate_attrs('host', types_renamed['host'], params['attrs'])
        else:
            res['autoconfigured_hosts_definitions'][name]['attrs'] = {}
       
        # keep the booleans
        for key, value in params.items():
            if key not in ['service_attrs', 'attrs']:
                res['autoconfigured_hosts_definitions'][name][key] = value

        # translate the service_attrs
        if 'services_attrs' in params:
            res['autoconfigured_hosts_definitions'][name]['services_attrs'] = {}
            for service in services:
                if service in params['services_attrs']:
                    res['autoconfigured_hosts_definitions'][name]['services_attrs'][service] = _translate_attrs('service', types_renamed['service'], params['services_attrs'][service])

            for service in services_loop:
                if service in params['services_attrs']:
                    res['autoconfigured_hosts_definitions'][name]['services_attrs'][service] = {}
                    for subservice in params['services_attrs'][service]:
                        res['autoconfigured_hosts_definitions'][name]['services_attrs'][service][subservice] = _translate_attrs('service', types_renamed['service'], params['services_attrs'][service][subservice])
    return res

def objects():
    return objects_icinga2()

def format(dictionary, quote_keys=False, quote_values=True):
    '''
    function to transform all values in a dictionary in string and adding quotes
    the main goal is to print values with quotes like "value" but we don't want print list with quotes like "[v1, v2]". This should be ["v1", "v2"]
    this can be done in jinja template but the template is already complex
    '''
    res={}
    for key, value in dictionary.items():
        if quote_keys:
            key = '"'+str(key)+'"'

        if key in ['type', 'template']: # ugly hack
            quote_values = False

        if isinstance(value, dict): # recurse
            if key in ['arguments', 'ranges']: # in theses subdictionaries, the keys are also quoted
                res[key] = format(value, True, True)
            elif key in ['services_enabled', 'services_loop_enabled']: # theses dictionaries contains booleans
                res[key] = format(value, False, False)
            else:
                res[key] = format(value)
        elif isinstance(value, list):
            if 'import' == key:
                res[key] = map((lambda v: '"'+str(v).replace('"','\\"')+'"'), value)
            else:
                res[key] = '['
                # suppose that all values in list are strings
                # escape '"' char and quote each strings
                if quote_values:
                    res[key] += ', '.join(map((lambda v: '"'+str(v).replace('"','\\"')+'"'), value))
                else:
                    res[key] += ', '.join(value)
                res[key] += ']'
        elif isinstance(value, unicode):
            if quote_values:
                res[key] = '"'+value.replace('"', '\\"')+'"'
            else:
                res[key] = value
        else:
            if quote_values:
                res[key] = '"'+str(value).encode('utf-8').replace('"', '\\"')+'"'
            else:
                res[key] = value

    return res

def get_settings_for_object(target=None, obj=None, attr=None):
    '''
    expand the subdictionaries which are not cached in mc_icinga2.settings.objects
    '''
    if 'purge_definitions' == target:
        res =  __salt__['mc_utils.defaults']('makina-states.services.monitoring.icinga2.objects.'+target, { target: objects()[target] })[target]
    else:
        res = __salt__['mc_utils.defaults']('makina-states.services.monitoring.icinga2.objects.'+target+'.'+obj, objects()[target][obj])
        if attr: # and attr in res:
            res = res[attr]
    return res


def settings():
    '''
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
        # get_settings_for_object is the function to retrieve a non cached subdictionary
        dict_objects = objects()
        dict_objects['objects_definitions'] = dict_objects['objects_definitions'].keys()
        dict_objects['purge_definitions'] = []
        dict_objects['autoconfigured_hosts_definitions'] = dict_objects['autoconfigured_hosts_definitions'].keys()

        # generate default password
        icinga2_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga2', registry_format='pack')

        password_ido = icinga2_reg.setdefault('ido.db_password'
                                        , __salt__['mc_utils.generate_password']())
        password_cgi = icinga2_reg.setdefault('cgi.root_account_password'
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
            'makina-states.services.monitoring.icinga2', {
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
                # because the subdictionary is very big, we take it from another function but we can copy/paste it here
                'objects': dict_objects,
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
                                'uwsgi_pass': "127.0.0.1:3031",
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
                            'socket': "127.0.0.1:3031",
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
            'icinga2', icinga2_reg,
            registry_format='pack')
        return data
    return _settings()

def replace_chars(s):
    res=s
    for char in list('/.:_'):
        res=res.replace(char, '-')
    return res

def add_configuration_object(file=None, type=None, attrs=None, definition=None, fromsettings=None, get=False, get_objects_file=None, **kwargs):
    print('call add_configuration_object')
    '''Add the object file in the file's list to be added'''
    if get:
        if get_objects_file:
            return add_configuration_object.objects[get_objects_file]
        else:
            return add_configuration_object.objects
    elif type and file and attrs:
        if file not in add_configuration_object.objects:
            add_configuration_object.objects[file]=[]
        add_configuration_object.objects[file].append({'type': type, 'attrs': attrs, 'definition': definition})
    elif fromsettings:
        if file not in add_configuration_object.objects:
            add_configuration_object.objects[file]=[]
        add_configuration_object.objects[file].append({'fromsettings': fromsettings})
    print('end call add_configuration_object')


# global variable initialisation
add_configuration_object.objects={}

def remove_configuration_object(file=None, get=False, **kwargs):
    '''Add the file in the file's list to be removed'''
    if get :
        return remove_configuration_object.files
    elif file:
        icingaSettings_complete = __salt__['mc_icinga2.settings']()
        # append " \"file\"" to the global variable
        filename='/'.join([icingaSettings_complete['objects']['directory'], file])
        # it doesn't avoid injection, just allow the '"' char in filename
        filename=filename.replace('"', '\"')
        remove_configuration_object.files += " \""+filename+"\""

# global variable initialisation
remove_configuration_object.files=""

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
    kwargs.setdefault('objects', {'directory': icingaSettings_complete['objects']['directory']})

    kwargs.setdefault('hostname', hostname)
    kwargs.setdefault('hostgroup', hostgroup)

    if hostgroup:
        kwargs.setdefault('type', 'HostGroup')
        service_key_hostname = 'hostgroup_name'
    else:
        kwargs.setdefault('type', 'Host')
        service_key_hostname = 'host_name'

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
            services_loop_enabled[service]=True
        else:
            services_loop_enabled[service]=False

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
        'nmd_www': "/", # must be completed
    }
    disks_spaces = dict()
    for mountpoint, path in mountpoints_path.items():
        if eval('disk_space_'+mountpoint):
            disks_spaces[mountpoint]=path

    # default values for dns_association service
    dns_hostname=''
    dns_address=''

    if dns_association_hostname or dns_association or dns_reverse_association and 'address' in attrs and 'host_name' in attrs:
        if 'host_name' in attrs:
            dns_hostname = attrs['host_name']
        else:
            dns_hostname = hostname

        if not dns_hostname.endswith('.'):
            dns_hostname = dns_hostname+'.'

        dns_address = attrs['address']

    # give the default values for commands parameters values
    # the keys are the services names, not the commands names (use the service filename)
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
           'vars.command': "/root/admin_scripts/nagios/check_rdiff -r /data/backups/phpnet6 -w 24 -c 48 -l 2048 -p 24"
       },
       'beam_process': {
           'service_description': "Check beam proces",
           'import': ["ST_ALERT"],
#           'notification_options': "w,c,r",
           'enable_notifications': 1,
           'check_command': "C_SNMP_PROCESS",

           'vars.process': "beam",
           'vars.warning': 0,
           'vars.critical': 0,
       },
       'celeryd_process': {
           'service_description': "Check celeryd process",
           'import': ["ST_ALERT"],
#           'notification_options': "w,c,r",
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
       'dns_reverse_association': {
           'default': {
               'service_description': "DNS_REVERSE_ASSOCIATION_",
               'import': ["ST_DNS_ASSOCIATION"],
               'check_command': "C_DNS_EXTERNE_REVERSE_ASSOCIATION",
#               'vars.inaddr': "" # generated below from dns_association dictionary
#               'vars.hostname': ""
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

           'vars.command': "'/root/admin_scripts/nagios/check_drbd -d  0,1'",
       },
       'epmd_process': {
           'service_description': "Check epmd process",
           'import': ["ST_ALERT"],
#           'notification_options': "w,c,r",
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

           'vars.command': "/var/makina/alma-job/job/supervision/check_erp_files.sh",
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
#           'notification_options': "w,c,r",
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

           'vars.command': "/root/admin_scripts/nagios/check_haproxy_stats.pl -p web -w 80 -c 90",
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

           'vars.command': "'/root/admin_scripts/nagios/check_megaraid_sas'",
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

           'vars.command': "/var/makina/alma-job/job/supervision/check_prebill_sending.sh",
       },
       'raid': {
           'service_description': "CHECK_RAID",
           'import': ["ST_ALERT"],
           'check_command': "CSSH_RAID_SOFT",

           'vars.command': "'/root/admin_scripts/nagios/check_md_raid'",
       },
       'sas': {
           'service_description': "S_SAS",
           'import': ["ST_ROOT"],
           'check_command': "CSSH_SAS2IRCU",

           'vars.command': "/root/admin_scripts/check_nagios/check_sas2ircu/check_sas2ircu",
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

           'vars.command': "/home/zope/adria/rcse/production-2014-01-23-14-27-01/bin/supervisorctl",
       },
       'swap': {
           'service_description': "CHECK_SWAP",
           'import': ["ST_ALERT"],
           'check_command': "CSSH_RAID_SOFT",

           'vars.command': "'/root/admin_scripts/nagios/check_swap -w 80%% -c 50%%'",
       },
       'tiles_generator_access': {
           'service_description': "Check tiles generator access",
           'import': ["ST_ALERT"],
#           'notification_options': "w,c,r",
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

    # add the services_attrs 'default' in all services in services_default_attrs
    # in order to add directives for all services (like contact_groups)
    if 'default' in services_attrs:
        for name, service in services_default_attrs.items():
            if not name in services_attrs:
                services_attrs[name]={}
            if not name in ['dns_association', 'dns_reverse_association', 'disk_space', 'network', 'solr', 'web_openid', 'web']:
                services_default_attrs[name] = dict(services_default_attrs[name].items() + services_attrs['default'].items())
            else:
                services_default_attrs[name]['default'] = dict(services_default_attrs[name]['default'].items() + services_attrs['default'].items())
        services_attrs.pop('default', None)

    # override the commands parameters values
    # we complete the services_attrs dictionary with values from services_default_attrs

    # override dns_association subdictionary
    if not 'dns_association' in services_attrs:
        services_attrs['dns_association'] =  services_default_attrs['dns_association']
        services_attrs['dns_association']['default']['service_description']=services_default_attrs['dns_association']['default']['service_description']+'default'
    else:
        for name, dns in services_attrs['dns_association'].items():
            # generate the service_description if not given
            if 'service_description' not in dns:
                services_attrs['dns_association'][name]['service_description']=services_default_attrs['dns_association']['default']['service_description']+name
            for key, value in services_default_attrs['dns_association']['default'].items():
                if not key in dns:
                    services_attrs['dns_association'][name][key]=value

    # override dns_reverse_assocation subdictionary
    if not 'dns_reverse_association' in services_attrs:
        services_attrs['dns_reverse_association'] = {}
        # the dictionary is not set, we generate it from dns_association dictionary (we suppose all ips are ipv4 that is bad):
        for name, dns in services_attrs['dns_association'].items():
            services_attrs['dns_reverse_association'][name] = copy.deepcopy(services_default_attrs['dns_reverse_association']['default'])
            services_attrs['dns_reverse_association'][name]['service_description']=services_default_attrs['dns_reverse_association']['default']['service_description']+name
 
            address_splitted = dns['vars.dns_address'].split('.')
            inaddr = '.'.join(address_splitted[::-1]) # tanslate a.b.c.d in d.c.b.a
            inaddr = inaddr + '.in-addr.arpa.'
            services_attrs['dns_reverse_association'][name]['vars.inaddr']=inaddr
            services_attrs['dns_reverse_association'][name]['vars.hostname']=dns['vars.hostname']
    else:
        # the dictionary is set, we merging normally
        for name, dns in services_attrs['dns_reverse_association'].items():
            if 'service_description' not in dns:
                services_attrs['dns_reverse_association'][name]['service_description']=services_default_attrs['dns_association'][name]['service_reverse_description']+name
            for key, value in services_default_attrs['dns_reverse_association']['default'].items():
                if not key in dns:
                    services_attrs['dns_reverse_association'][name][key]=value

    # override network subdictionary
    if not 'network' in services_attrs:
        services_attrs['network'] =  services_default_attrs['network']
        services_attrs['network']['default']['service_description']=services_default_attrs['network']['default']['service_description']+'default'
        services_attrs['network']['default']['import']=services_default_attrs['network']['default']['import']+[services_default_attrs['network']['default']['vars.interface']]
    else:
        for name, network in services_attrs['network'].items():
            # generate the service_description if not given
            if 'service_description' not in network:
                if 'vars.interface' in services_attrs['network'][name]:
                    services_attrs['network'][name]['service_description']=services_default_attrs['network']['default']['service_description']+services_attrs['network'][name]['vars.interface'].upper()
                else:
                    services_attrs['network'][name]['service_description']=services_default_attrs['network']['default']['service_description']+services_default_attrs['network']['default']['vars.interface'].upper()
            if 'import' not in network:
                if 'vars.interface' in services_attrs['network'][name]:
                    services_attrs['network'][name]['import']=services_default_attrs['network']['default']['import']+services_attrs['network'][name]['vars.interface'].upper()
                else:
                    services_attrs['network'][name]['import']=[services_default_attrs['network']['default']['import'][0]+i.upper() for i in services_default_attrs['network']['default']['vars.interface']] # add the prefix to the import

            for key, value in services_default_attrs['network']['default'].items():
                if not key in network:
                    services_attrs['network'][name][key]=value

    # override solr subdictionary
    if not 'solr' in services_attrs:
        services_attrs['solr'] =  services_default_attrs['solr']
        services_attrs['solr']['default']['service_description']=services_default_attrs['solr']['default']['service_description']+'default'
    else:
        for name, solr in services_attrs['solr'].items():
            # generate the service_description if not given
            if 'service_description' not in solr:
                services_attrs['solr'][name]['service_description']=services_default_attrs['solr']['default']['service_description']+name
            for key, value in services_default_attrs['solr']['default'].items():
                if not key in solr:
                    services_attrs['solr'][name][key]=value
            # transform list of values in string ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_attrs['solr'][name]['vars.strings'], list):
                str_list = services_attrs['solr'][name]['vars.strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [ value.replace('"', '\\\\"') for value in str_list ]
                services_attrs['solr'][name]['vars.strings']='"'+'" -s "'.join(str_list)+'"'


    # override web_openid subdictionary
    if not 'web_openid' in services_attrs:
        services_attrs['web_openid'] =  services_default_attrs['web_openid']
        services_attrs['web_openid']['default']['service_description']=services_default_attrs['web_openid']['default']['service_description']+'default'
    else:
        for name, web_openid in services_attrs['web_openid'].items():
            # generate the service_description if not given
            if 'service_description' not in web_openid:
                services_attrs['web_openid'][name]['service_description']=services_default_attrs['web_openid']['default']['service_description']+name
            for key, value in services_default_attrs['web_openid']['default'].items():
                if not key in web_openid:
                    services_attrs['web_openid'][name][key]=value

    # override web subdictionary
    if not 'web' in services_attrs:
        services_attrs['web'] =  services_default_attrs['web']
        services_attrs['web']['default']['service_description']=services_default_attrs['web']['default']['service_description']+'default'
    else:
        for name, web in services_attrs['web'].items():
            # generate the service_description if not given
            if 'service_description' not in web:
                services_attrs['web'][name]['service_description']=services_default_attrs['web']['default']['service_description']+name
            for key, value in services_default_attrs['web']['default'].items():
                if not key in web:
                    services_attrs['web'][name][key]=value
            # transform list of values in string ['a', 'b'] becomes '"a" -s "b"'
            if isinstance(services_attrs['web'][name]['vars.strings'], list):
                str_list = services_attrs['web'][name]['vars.strings']
                # to avoid quotes conflicts (doesn't avoid code injection)
                str_list = [ value.replace('"', '\\\\"') for value in str_list ]
                services_attrs['web'][name]['vars.strings']='"'+'" -s "'.join(str_list)+'"'

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
        if mountpoint in disks_spaces: # the check is enabled
            if mountpoint not in services_default_attrs['disk_space']:
                services_default_attrs['disk_space'][mountpoint] = copy.deepcopy(services_default_attrs['disk_space']['default'])

            services_attrs['disk_space'][mountpoint] = dict(services_default_attrs['disk_space']['default'].items()
                                                                         +services_default_attrs['disk_space'][mountpoint].items())

            services_attrs['disk_space'][mountpoint] = dict(services_attrs['disk_space'][mountpoint].items()
                                                                         +services_attrs['disk_space']['default'].items())

            services_attrs['disk_space'][mountpoint] = dict(services_attrs['disk_space'][mountpoint].items()
                                                                         +services_attrs['disk_space'][mountpoint].items())

            if services_attrs['disk_space'][mountpoint]['service_description'] == services_default_attrs['disk_space']['default']['service_description']:
                services_attrs['disk_space'][mountpoint]['service_description']=services_attrs['disk_space'][mountpoint]['service_description']+disks_spaces[mountpoint].upper()
#            if services_attrs['disk_space'][mountpoint]['import'][0] in services_default_attrs['disk_space']['default']['import']:
            services_attrs['disk_space'][mountpoint]['import']=[services_attrs['disk_space'][mountpoint]['import'][0]+disks_spaces[mountpoint].replace('/', '_').replace('_', '/', 1).upper()]
            services_attrs['disk_space'][mountpoint]['vars.path']= disks_spaces[mountpoint]


    # remove default dictionary
    if 'default' in services_attrs['disk_space']:
        services_attrs['disk_space'].pop('default', None)

    # override others values (type are string or int)
    if not isinstance(services_attrs, dict):
        services_attrs = {}

    for name, command in services_default_attrs.items():
        if not name in ['dns_association', 'dns_reverse_association', 'disk_space', 'network', 'solr', 'web_openid', 'web']:
            if not name in services_attrs:
                services_attrs[name] = {}
            services_attrs[name] = dict(services_default_attrs[name].items() + services_attrs[name].items())


    # generate the complete check command (we can't do a loop before we have to give the good order for arguments)
    ## don't generate the complete check command because it is icinga2 ##
    
    # add the host_name or hostgroup_name in each service and don't remove directives begining with "vars." (because it is icinga2)

    for service in services:
        if service in services_attrs:
            services_attrs[service][service_key_hostname] = hostname

    for service in services_loop:
        if service in services_attrs:
            for subservice  in services_attrs[service]:
                services_attrs[service][subservice][service_key_hostname] = hostname
 
    kwargs.setdefault('services_attrs', services_attrs)

    icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings, kwargs)
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
            host =  get_settings_for_object('autoconfigured_hosts_definitions', fromsettings)
            if 'hostgroup' in host:
                hostgroup = host['hostgroup']

        #    icingaSettings = copy.deepcopy(__salt__['mc_icinga2.settings']())
        #   save the ram (get only useful values)
        icingaSettings_complete = __salt__['mc_icinga2.settings']()
        icingaSettings = {}
        kwargs.setdefault('objects', {'directory': icingaSettings_complete['objects']['directory']})
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
        file='/'.join([service_subdirectory, hostname+'.conf'])
        kwargs.setdefault('file', file)
        kwargs.setdefault('state_name_salt', replace_chars(file))
        icingaSettings = __salt__['mc_utils.dictupdate'](icingaSettings, kwargs)

        # we remember the host to add:

        if fromsettings:
            add_auto_configuration_host.objects[hostname] = { 'fromsettings': fromsettings }
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
add_auto_configuration_host.objects={}

#TODO: find how to call this function
def clean_global_variables():
    '''Function to remove global variables'''
    del add_configuration_object.objects
    del remove_configuration_object.files
    del add_auto_configuration_host.objects






def dump():
    return mc_states.utils.dump(__salt__,__name)

#
