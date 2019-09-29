# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga2:

mc_icinga2 / icinga functions
=============================



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

# Import python libs

from salt.utils.odict import OrderedDict
import re
import os
import socket
import logging
import traceback
import copy
import mc_states.api

six = mc_states.api.six
__name = 'icinga2'
_default = object()
_activated = object()
_disabled = object()

log = logging.getLogger(__name__)


def svc_name(key):
    key = key.replace('/', 'SLASH')
    key = key.replace(':', '_')
    return key


def object_uniquify(attrs):
    if 'import' in attrs:
        attrs['import'] = __salt__['mc_utils.uniquify'](
            attrs['import'])
    if 'parents' in attrs:
        attrs['parents'] = __salt__['mc_utils.uniquify'](
            attrs['parents'])
    return attrs


def reencode_webstrings(str_list):
    # transform list of values in
    # string ['a', 'b'] becomes '"a" -s "b"'
    if isinstance(str_list, list):
        # to avoid quotes conflicts (doesn't avoid code injection)
        str_list = [value.replace('"', '\\\\"') for value in str_list]
        str_list = ('"' + '" -s "'.join(str_list) + '"')
    return str_list


def load_objects(core=True, ttl=120):
    '''
    function to load extra icinga settings from pillar

    they contains the objects definitions to add in icinga2

    Idea is to use them differently not to use all the RAM
    in cache for the states construction.

    the autoconfigured_hosts_definitions dictionary contains the
    definitions of hosts created with the configuration_add_auto_host
    macro

    the objects_definitions dictionary contains the defintinions of
    objects created with the configuration_add_object_macro

    the purges list contains the files to delete

    the "notification" and "parents" are under "attrs"
    but in fact it creates other objects like HostDependency
    or Notification

    example::

      icinga2_definitions:
         autoconfigured_hosts:
          localhost:
            hostname: "localhost"
            attrs:
              address: 127.0.0.1
              display_name: "localhost"
            ssh: true
            services_attrs:
              web:
                www.foo.com: bar
         objects:
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
                - arg: value
           name: mycommand
           file: command.conf
           type: CheckCommand
           template: false
         purges:
           - commands.conf
    '''

    def _do(core):
        core_objects = {}
        if core:
            msr = __salt__['mc_locations.msr']()
            core_objects = __salt__['mc_utils.cyaml_load'](
                msr +
                '/files/icinga2_core_objects.conf')
        data = __salt__['mc_utils.defaults'](
            'icinga2_definitions', {
                'objects': core_objects,
                'purges': [],
                # where the icinga2 objects configuration
                # will be written
                'autoconfigured_hosts': {}
            })
        return data
    cache_key = 'mc_icinga2.load_objects___cache__'
    return __salt__['mc_utils.memoize_cache'](_do, [core], {}, cache_key, ttl)


def objects(core=True, ttl=120):
    def _do(core):
        rdata = OrderedDict()
        data = __salt__['mc_icinga2.load_objects'](core=core)
        dsettings = __salt__['mc_icinga2.settings']()
        rdata['raw_objects'] = data['objects']
        rdata['objects'] = OrderedDict()
        rdata['objects_by_file'] = OrderedDict()
        for obj, data in data['objects'].items():
            try:
                # automatic name from ID
                if not data.get('name', ''):
                    data['name'] = obj
                name = data['name']
                # by default, we are not a template
                tp = data.setdefault('template', False)
                typ_ = data.get('type', None)
                # try to guess template status from name
                if not tp:
                    for test in [
                        lambda x: x.startswith('HT_'),
                        lambda x: x.startswith('ST_'),
                        lambda x: x.startswith('NT_'),
                        lambda x: x.startswith('NCT_')
                    ]:
                        if test(name):
                            tp = data['template'] = True
                            break
                # automatic hostname from ID
                if not data.get('hostname', ''):
                    data['hostname'] = obj
                # try to get type from name
                if not typ_:
                    for final_typ, tests in {
                        'TimePeriod': [lambda x: x.startswith('TP_'),
                                       lambda x: x.startswith('T_')],
                        'NotificationCommand': (
                            [lambda x: x.startswith('NC_'),
                             lambda x: x.startswith('NCT_')]),
                        'Notification': [lambda x: x.startswith('N_'),
                                         lambda x: x.startswith('NT_')],
                        'Host': [lambda x: x.startswith('HT_'),
                                 lambda x: x.startswith('H_')],
                        'Service': [lambda x: x.startswith('ST_'),
                                    lambda x: x.startswith('S_')],
                        'User': [lambda x: x.startswith('U_')],
                        'UserGroup': [lambda x: x.startswith('G_')],
                        'HostGroup': [lambda x: x.startswith('HG_')],
                        'ServiceGroup': [lambda x: x.startswith('GS_'),
                                         lambda x: x.startswith('SG_')],
                        'CheckCommand': [lambda x: x.startswith('check_'),
                                         lambda x: x.startswith('C_'),
                                         lambda x: x.startswith('EV_'),
                                         lambda x: x.startswith('CSSH'),
                                         lambda x: x.startswith('CSSH_')],
                    }.items():
                        for test in tests:
                            if test(name):
                                typ_ = final_typ
                                break
                        if typ_:
                            break
                file_ = {'NotificationCommand': 'notifications.conf',
                         'Notification': 'notifications.conf',
                         'TimePeriod': 'timeperiods.conf',
                         'CheckCommand': 'checkcommands.conf',
                         'User': 'contacts.conf',
                         'UserGroup': 'contactgroups.conf',
                         'HostGroup': 'hostgroups.conf',
                         'Service': 'services.conf',
                         'ServiceGroup': 'servicegroups.conf',
                         'Host': 'hosts.conf'}
                # guess configuration file from type
                ft = data.setdefault('file', file_.get(typ_, None))
                data['file'] = ft
                data['type'] = typ_
                # declare constants as var for them to be resolved
                # by macro calls
                if obj == 'C_BASE':
                    for i in dsettings['constants_conf']:
                        data['attrs'][
                            'vars.{0}'.format(i)] = '{0} + ""'.format(i)
                attrs = data.setdefault('attrs', {})
                members = attrs.get('members', _default)
                notification = data.setdefault('notification', [])
                # convert single notification form
                # to standard list one (a list of one element)
                data['notification'] = notification
                if typ_ in ['Host', 'Service'] and notification:
                    add_notification(attrs, notification,
                                     is_host=typ_ in ['Host'],
                                     is_service=typ_ in ['Service'])
                if members is not _default:
                    if 'members_link' not in attrs:
                        if typ_ in ['Service']:
                            attrs['members_link'] = 'host.name'
                    if 'members_link_operator' not in attrs:
                        if isinstance(members, list):
                            mlo = 'in'
                        else:
                            mlo = '=='
                        attrs['members_link_operator'] = mlo
                cmd = attrs.get('command', None)
                arguments = attrs.get('arguments', None)
                if (
                    cmd and
                    not isinstance(cmd, list) and
                    arguments
                ):
                    attrs['command'] = [cmd]
                rdata['objects'][obj] = data
                fdata = rdata['objects_by_file'].setdefault(
                    data['file'], OrderedDict())
                fdata[obj] = object_uniquify(data)
            except (Exception,):
                log.error(
                    'Icinga object configuration failed for {0}'.format(obj))
                raise
        return rdata
    cache_key = 'mc_icinga2.objects___cache__'
    return __salt__['mc_utils.memoize_cache'](_do, [core], {}, cache_key, ttl)


def quotev(v, valtype=''):
    donotquote = False
    # cases that we should not quote (eg: variables construction)
    if valtype == 'command' and v.count('$') >= 2:
        donotquote = True
    if ' + ' in v:
        donotquote = True
    if not donotquote and not v.startswith('"'):
        v = '"' + str(v.replace('"', '\\"')) + '"'
    v = v .replace('+ ""', '').replace("+ ''", '')
    return v


# pylint: disable=W0622
def format(dictionary, quote_keys=False, quote_values=True, init=True):
    '''
    function to transform all values in a dictionary in string
    and adding quotes.
    The main goal is to print values with quotes like "value"
    but we don't want print list with quotes like "[v1, v2]".
    This should be ["v1", "v2"] this can be done in jinja
    template but the template is already complex
    '''
    res = {}
    for key, value in copy.deepcopy(dictionary).items():
        if quote_keys:
            res_key = quotev(key)
        else:
            res_key = key

        valtype = None
        # ugly hack
        if key in ['template', 'type', 'types', 'states', 'import',
                   'raw_config', 'members_link_operator', 'members_link']:
            quote_value = False
        elif key in ['command']:
            quote_value = True
        else:
            quote_value = quote_values

        if isinstance(value, dict):  # recurse
            # in theses subdictionaries, the keys are also quoted
            if key in ['arguments',
                       'ranges']:
                res[res_key] = format(value, True, True, False)
            # theses dictionaries are quoted
            elif key in ['notification']:
                res[res_key] = format(value, False, True, False)
            # theses dictionaries contains booleans
            elif key in ['services_enabled']:
                res[res_key] = format(value, False, False, False)
            else:
                res[res_key] = format(value, quote_keys, quote_value, False)
        elif isinstance(value, list):
            # theses lists are managed in the template,
            # we only quote each string in the list
            if key in ['notification']:
                res[res_key] = []
                for v in value:
                    res[res_key].append(format(v, False, True, False))
            elif key in ['import', 'parents']:
                res[res_key] = map(quotev, value)
            else:
                res[res_key] = '['
                # suppose that all values in list are strings
                # escape '"' char and quote each strings
                if quote_value:
                    res[res_key] += ', '.join(map(quotev, value))
                else:
                    res[res_key] += ', '.join(value)
                res[res_key] += ']'
        elif key.startswith('enable_'):
            if (
                '"1"' == value or
                '1' == value or
                1 == value or
                'true' == value or
                value is True
            ):
                res[res_key] = "true"
            else:
                res[res_key] = "false"
        elif key in ['template']:
            res[res_key] = value
        elif key.endswith('_interval'):  # a bad method to find a time
            res[res_key] = value
        elif isinstance(value, bool):
            res[res_key] = (value is True) and 'true' or 'false'
        elif isinstance(value, int):
            res[res_key] = str(value)
        elif isinstance(value, unicode):
            if quote_value:
                res[res_key] = quotev(value, valtype=valtype)
            else:
                res[res_key] = value
        else:
            if quote_value:
                res[res_key] = quotev(str(value).decode('utf-8'),
                                      valtype=valtype)
            else:
                res[res_key] = value
    return res


def get_settings_for_object(target=None, obj=None, attr=None):
    '''
    expand the subdictionaries which are not cached
    in mc_icinga2.settings.objects
    '''
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
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
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
                'gen_directory': (
                    "/etc/icinga2/conf.d/salt_generated"),
                'group': "nagios",
                'cmdgroup': "www-data",
                'pidfile': "/var/run/icinga2/icinga2.pid",
                'configuration_directory': (
                    locs['conf_dir'] + "/icinga2"),
                'niceness': 5,
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
                    'USER1': "\"/usr/lib/nagios/plugins\"",
                    'CUSTM_ADM_SCRIPTS': (
                        '\"/usr/local/admin_scripts/nagios\"'),
                    'SNMP_CRYPT': '\"secret\"',
                    'SNMP_PASS': '\"secret\"',
                    'SNMP_USER': '\"user\"',
                    'SNMP_AUTH': '\"sha\"',
                    'SNMP_PRIV': '\"des\"',
                    'TEST_AUTHPAIR': '\"tsa:pw\"',
                    'TESTUSER': "\"tsa\"",
                    'TESTPWD': "\"pw\"",
                    'MAIL': "\"@foo.com\"",
                    'MX': "\"@mail.foo.com\"",
                    'SSHKEY': '\"/var/lib/nagios/id_rsa_supervision\"',
                    'ZoneName': "\"NodeName\"",
                },
                'matrix': {
                    'room': '',
                    'server': '',
                    'room': '#makinacorpus:matrix.makina-corpus.net',
                    'token': '',
                    'enabled': False,
                },
                'irc': {
                    'channel': '#test',
                    'ssl': 'False',
                    'key': '',
                    'server_name': 'freenode',
                    'server': 'irc.freenode.net:6667',
                    'enabled': False,
                    'nick': 'makina_icinga',
                    'server_password': '',
                },
                'zones_conf': {
                    'object Endpoint NodeName': {
                        'host': "NodeName"},
                    'object Zone ZoneName': {
                        'endpoints': "[ NodeName ]"},
                },
                'ssh': {
                    'id_rsa_supervision': '',
                    'id_rsa_supervision.pub': '',
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
            data['modules']['ido2db']['psql_uri'] = (
                'postgres://{user}:{password}@'
                '{host}:{port}/{name}'
                '').format(
                    **data['modules']['ido2db']['database'])
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


def remove_configuration_objects():
    '''Add the file in the file's list to be removed'''
    icingaSettings_complete = __salt__['mc_icinga2.settings']()
    files = __salt__['mc_icinga2.load_objects']()['purges']
    todel = []
    prefix = icingaSettings_complete['gen_directory']
    for f in files:
        pretendants = [os.path.join(prefix, f),
                       f]
        for p in pretendants:
            if os.path.exists(p):
                todel.append(p)
    return todel


def autoconfigured_hosts(ttl=60):
    def _do():
        rdata = OrderedDict()
        objs = __salt__['mc_icinga2.load_objects']()['autoconfigured_hosts']
        for host, data in objs.items():
            rdata[host] = __salt__['mc_icinga2.autoconfigured_host'](
                host, data=data)
        return rdata
    cache_key = 'mc_icinga2.autoconfigured_hosts__cache__'
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def autoconfigured_host(host, data=None, ttl=60):
    def _do(host, data):
        if data is None:
            data = __salt__['mc_icinga2.load_objects']()[
                'autoconfigured_hosts'][host]
        data = copy.deepcopy(data)
        # automatic name from ID
        if not data.get('name', ''):
            data['name'] = host
        # automatic hostname from ID
        if not data.get('hostname', ''):
            data['hostname'] = host
        try:
            rdata = __salt__['mc_icinga2.autoconfigure_host'](
                data['hostname'], **data)
            for k in ['name', 'hostname']:
                rdata[k] = data[k]
        except Exception, exc:
            log.warning(
                'Failed autohost for {0}: {1} \n{2}'.format(
                    host, exc, traceback.format_exc()))
            raise exc
        return rdata
    cache_key = 'mc_icinga2.autoconfigured_host__cache__{0}'.format(host)
    return __salt__['mc_utils.memoize_cache'](_do, [host, data], {}, cache_key, ttl)


def add_notification(attrs,
                     notification_list=None,
                     default_notifiers=None,
                     is_service=None,
                     is_host=None):
    '''Add a basic per-mail notification
    If you want that a notification becomes the default one,
    just set vars.default_email_notification: true in
    your notification object definition

    '''
    icingaSettings = __salt__['mc_icinga2.settings']()
    if not attrs:
        attrs = {}
    if is_service:
        is_host = False
    if is_host:
        is_service = False
    if not is_service and not is_host:
        if 'address' in attrs:
            is_host = True
        elif 'address6' in attrs:
            is_host = True
        else:
            is_service = True

    if not notification_list:
        notification_list = []
    onotifications = attrs.setdefault('notification', [])
    if not isinstance(onotifications, list):
        # single notification definition (as a dict)
        if isinstance(onotifications, dict):
            onotifications = [onotifications]
        if not onotifications:
            onotifications = []
        attrs['notification'] = onotifications
    # special sysadmin notifiations
    if not default_notifiers:
        default_notifiers = ['G_Sysadmins']
    for i in default_notifiers:
        if i not in notification_list:
            notification_list.append(i)
    if notification_list:
        # search for our special notification
        default_notification = None
        default_irc_notification = None
        default_matrix_notification = None
        for i in onotifications:
            if i.get('vars.default_email_notification', False):
                default_notification = i
            if i.get('vars.default_irc_notification', False):
                default_irc_notification = i
            if i.get('vars.default_matrix_notification', False):
                default_matrix_notification = i
            if None not in [default_notification, default_irc_notification,
                            default_matrix_notification]:  # noqa
                break
        if default_notification is None:
            default_notification = {}
        if default_irc_notification is None:
            default_irc_notification = {}
        if default_matrix_notification is None:
            default_matrix_notification = {}
        # if notifications were defined for the object
        # but we did not found any notication, take the first
        # as the default one
        if not default_notification:
            if onotifications:
                default_notification = onotifications[0]
            else:
                default_notification = {}
                default_notification.setdefault('import', [])
                onotifications.append(default_notification)
            default_notification['vars.default_email_notification'] = True
        imports = default_notification.setdefault('import', [])
        default_notification.setdefault(
            'vars.n_name', 'mail_notification')
        if is_host:
            default_import = 'NT_HOST'
            default_irc_import = 'NT_HOST_IRC'
            default_matrix_import = 'NT_HOST_MATRIX'
        #     intv = 'host.vars.n_interval + ""'
        if is_service:
            default_import = 'NT_SERVICE'
            default_irc_import = 'NT_SERVICE_IRC'
            default_matrix_import = 'NT_SERVICE_MATRIX'
        #     intv = 'service.vars.n_interval + ""'
        # conditionnal notification interval based on underlying
        # service or host does not work that way yet, searching ...
        # for not, sett interval to zero (only one alert per state change and
        # norepeat)
        intv = attrs.get('vars.n_interval', 0)
        default_notification.setdefault('interval', intv)
        for simport in ['NT_BASE', default_import]:
            if simport not in imports:
                imports.append(simport)
        for notifier in notification_list:
            ntyp = 'users'
            if notifier.startswith('G_'):
                ntyp = 'user_groups'
            users = default_notification.setdefault(ntyp, [])
            if notifier not in users:
                users.append(notifier)
        if icingaSettings['matrix']['enabled']:
            if not default_matrix_notification:
                # take the second, here !
                if len(onotifications) > 1:
                    default_matrix_notification = onotifications[1]
                else:
                    default_matrix_notification = {}
                    default_matrix_notification.setdefault('import', [])
                    onotifications.append(default_matrix_notification)
                default_matrix_notification[
                    'vars.default_matrix_notification'] = True
            default_matrix_notification.setdefault(
                'vars.n_name', 'matrix_notification')
            users = default_matrix_notification.setdefault('users', [])
            if 'U_matrixbot' not in users:
                users.append('U_matrixbot')
            matrix_imports = default_matrix_notification.setdefault('import', [])
            default_matrix_notification.setdefault('interval', intv)
            for simport in ['NT_BASE', default_matrix_import]:
                if simport not in matrix_imports:
                    matrix_imports.append(simport)
        if icingaSettings['irc']['enabled']:
            if not default_irc_notification:
                # take the second, here !
                if len(onotifications) > 1:
                    default_irc_notification = onotifications[1]
                else:
                    default_irc_notification = {}
                    default_irc_notification.setdefault('import', [])
                    onotifications.append(default_irc_notification)
                default_irc_notification[
                    'vars.default_irc_notification'] = True
            default_irc_notification.setdefault(
                'vars.n_name', 'irc_notification')
            users = default_irc_notification.setdefault('users', [])
            if 'U_bot' not in users:
                users.append('U_bot')
            irc_imports = default_irc_notification.setdefault('import', [])
            default_irc_notification.setdefault('interval', intv)
            for simport in ['NT_BASE', default_irc_import]:
                if simport not in irc_imports:
                    irc_imports.append(simport)
    return attrs


# pylint: disable=R0913
def autoconfigure_host(host,
                       attrs=None,
                       groups=None,
                       notification=None,
                       default_notifiers=None,
                       imports=None,
                       no_default_checks=False,
                       no_default_imports=False,
                       services_attrs=None,
                       ssh_username='root',
                       ssh_addr='',
                       ssh_port=22,
                       snmp_port=161,
                       ssh_timeout=30,
                       apt=None,
                       backup_burp_age=None,
                       burp_counters=None,
                       cron=None,
                       ddos=None,
                       disk_space_mode=None,
                       disk_space=None,
                       dns_association=None,
                       dns_association_hostname=None,
                       drbd=None,
                       haproxy_stats=None,
                       load_avg=None,
                       inotify=None,
                       mail_cyrus_imap_connections=None,
                       mail_imap=None,
                       mail_imap_ssl=None,
                       mail_pop=None,
                       mail_pop_ssl=None,
                       mail_pop_test_account=None,
                       mail_server_queues=None,
                       mail_smtp=None,
                       mongodb=None,
                       memory_mode=None,
                       memory=None,
                       ping=None,
                       nic_card=None,
                       ntp_peers=None,
                       ntp_time=None,
                       postgresql_port=None,
                       processes=None,
                       fullpath_processes=None,
                       raid=None,
                       snmpd_memory_control=None,
                       supervisor=None,
                       ssh=None,
                       swap=None,
                       apache_status=None,
                       remote_apache_status=None,
                       nginx_status=None,
                       remote_nginx_status=None,
                       tomcat=None,
                       redis=None,
                       web=None,
                       sar=None,
                       rbl=None,
                       web_openid=None,
                       **kwargs):
    services = ['backup_burp_age',
                'burp_counters',
                'cron',
                'ddos',
                'apt',
                'disk_space',
                'memory',
                'dns_association',
                'dns_association_hostname',
                'drbd',
                'haproxy_stats',
                'load_avg',
                'mail_cyrus_imap_connections',
                'mail_imap',
                'mail_imap_ssl',
                'mail_pop',
                'mail_pop_ssl',
                'mail_pop_test_account',
                'mail_server_queues',
                'mail_smtp',
                'nic_card',
                'mongodb',
                'inotify',
                'ntp_peers',
                'ntp_time',
                'ping',
                'postgresql_port',
                'fullpath_processes',
                'processes',
                'raid',
                'snmpd_memory_control',
                'ssh',
                'rbl',
                'redis',
                'supervisor',
                'tomcat',
                'web',
                'web_openid',
                'swap',
                'remote_nginx_status',
                'nginx_status',
                'sar',
                'remote_apache_status',
                'apache_status']
    services_multiple = ['disk_space', 'nic_card', 'dns_association',
                         'supervisor', 'drbd', 'tomcat', 'sar',
                         'rbl', 'fullpath_processes', 'processes',
                         'web_openid', 'web']
    if attrs is None:
        attrs = {}
    if services_attrs is None:
        services_attrs = {}
    # allow to select no_default_checks in yaml
    # but also allow some services to be manually activated to be checked
    non_defaults = ['apt', 'backup_burp_age', 'load_avg', 'memory',
                    'dns_association_hostname', 'ping', 'ntp_time',
                    'ssh', 'swap']
    defaults = [a for a in services + services_multiple
                if a not in non_defaults]
    for _default, checks in [(True, non_defaults),
                             (False, defaults)]:
        for check in checks:
            init_val = eval(check)  # pylint: disable=W0123
            manual = True
            if init_val is None:
                manual = False
                # pylint: disable=W0122
                exec('{0}={1}'.format(check, _default))
            # if manually selected On, be sure to select it for a run
            # even if we activated no_default_checks
            if init_val is False and manual is False:
                services_attrs.pop(check, None)
            elif bool(init_val):
                services_attrs.setdefault(check, {})
    disk_space_mode_maps = {
        'large': 'ST_LARGE_DISK_SPACE',
        'ularge': 'ST_ULARGE_DISK_SPACE',
        None: 'ST_DISK_SPACE'}
    memory_mode_maps = {
        'large': 'ST_MEMORY_LARGE',
        None: 'ST_MEMORY'}
    st_mem = memory_mode_maps.get(memory_mode, None)
    st_disk = disk_space_mode_maps.get(disk_space_mode, None)

    if not processes:
        processes = []
    if not fullpath_processes:
        fullpath_processes = []
    for i, val in kwargs.items():
        if i.startswith('process_') and val:
            processes.append('process_'.join(i.split('process_')[1:]))
        for i in ['fail2ban']:
            if kwargs.get(
                'process_' + i,
                kwargs.get('processes_' + i, True)
            ):
                processes.append(i)
    fullpath_processes = __salt__['mc_utils.uniquify'](fullpath_processes)
    processes = __salt__['mc_utils.uniquify'](processes)
    for i, val in kwargs.items():
        if i.startswith('process_') and not val:
            try:
                processes.pop(processes.index(i))
            except (ValueError, IndexError):
                continue
    rdata = {"host.name": host}
    icingaSettings = __salt__['mc_icinga2.settings']()
    if 'postgres' not in processes:
        if (
            'postgresl' in host or 'pgsql' in host
        ):
            processes.append('postgres')
    if 'mysql' not in processes:
        if 'mysql' in host:
            processes.append('mysql')
    if not notification:
        notification = []
    if not groups:
        groups = []
    if drbd is None:
        drbd = []
    if drbd is True:
        drbd = [0]
    if web_openid is None:
        web_openid = []
    if supervisor is None:
        supervisor = []
    if tomcat is None:
        tomcat = []
    if web is None:
        web = []
    filen = '/'.join(['hosts', host+'.conf'])
    if disk_space is None:
        disk_space = ['/']
    if nic_card is None:
        nic_card = ['eth0']
    if not disk_space:
        disk_space = []
    if not rbl:
        rbl = []
    if not sar:
        sar = []
    if not nic_card:
        nic_card = []
    if not ssh_addr:
        ssh_addr = host
    rdata.update({'type': 'Host',
                  'directory': icingaSettings['gen_directory'],
                  'attrs': attrs,
                  'hostname': host,
                  'file': filen,
                  'state_name_salt': replace_chars(filen)})
    services_enabled = rdata.setdefault('services_enabled', OrderedDict())
    services_enabled_types = rdata.setdefault('services_enabled_types', [])
    imports = attrs.setdefault('import', imports)
    if not imports:
        imports = []
    if not no_default_imports:
        default_imports = ['HT_BASE']
        for i in [
            a for a in default_imports
            if a not in imports
        ]:
            imports.append(i)
    if isinstance(imports, six.string_types):
        imports = imports.split(',')  # pylint: disable=E1101
    attrs['import'] = imports
    attrs.setdefault('vars.ssh_username', ssh_username)
    attrs.setdefault('vars.ssh_addr', ssh_addr)
    attrs.setdefault('vars.ssh_port', ssh_port)
    attrs.setdefault('vars.ssh_timeout', ssh_timeout)
    hgroups = attrs.setdefault('groups', [])
    for i in groups:
        if i not in hgroups:
            hgroups.append(i)
    add_notification(attrs, notification, default_notifiers, is_host=True)
    object_uniquify(rdata['attrs'])
    # services for which a loop is used in the macro
    if (
        dns_association_hostname or
        dns_association and
        'address' in attrs and
        'host_name' in attrs
    ):
        if 'host_name' in attrs:
            dns_hostname = attrs['host_name']
        else:
            dns_hostname = host
        if not dns_hostname.endswith('.'):
            dns_hostname += '.'
        dns_address = attrs['address']
    # give the default values for commands parameters values
    # the keys are the services names,
    # not the commands names (use the service filename)
    services_default_attrs = {
        'dns_association_hostname': {
            'vars.hostname': dns_hostname,
            'vars.dns_address': dns_address},
        'dns_association': {
            'vars.hostname': dns_hostname,
            'vars.dns_address': dns_address},
        'load_avg': {
            # 'vars.n_interval': 6000,
        },
        'mongodb': {
            'check_command': "CSSH_CHECK_MONGODB_AUTH"},
        'disk_space': {
            'vars.n_interval': 6000,
            'import': [st_disk]},
        'backup_burp_age': {
            'vars.n_interval': 72000,
        },
        'web': {
            'vars.n_interval': 7200,
        },
        'raid': {
            'vars.n_interval': 6000,
        },
        'memory': {
            'vars.n_interval': 6000,
            'import': [st_mem]}}
    # if we defined extra properties on a service,
    # enable it automatically
    if 'postgres' in processes:
        services_enabled_types.extend(['postgresql_connection_time'])
    if 'mongod' in processes:
        services_enabled_types.extend([
            'mongodb_connect',
            'mongodb_collections',
            'mongodb_databases',
            'mongodb_connections',
            'mongodb_index_miss_ratio',
            'mongodb_last_flush_time',
            'mongodb_flushing',
            'mongodb_lock',
            'mongodb_memory_mapped',
            'mongodb_memory'])
    if 'mysql' in processes:
        services_enabled_types.extend([])
        # disable automatic mysql probes, they have not much use for now
        # and cause more harm than good
        # services_enabled_types.extend(['mysql_connection_time',
        #                                'mysql_tablecache_hitrate',
        #                                'mysql_table_fragmentation',
        #                                'mysql_long_running_procs',
        #                                'mysql_open_files',
        #                                'mysql_index_usage',
        #                                'mysql_qcache_lowmem_prunes',
        #                                # more noise than good
        #                                # 'mysql_table_lock_contention',
        #                                'mysql_log_waits',
        #                                'mysql_threads_cached',
        #                                'mysql_threads_running',
        #                                'mysql_threads_connected',
        #                                'mysql_threads_created',
        #                                'mysql_connects_aborted',
        #                                'mysql_threads_connected',
        #                                'mysql_slow_queries',
        #                                'mysql_bufferpool_hitrate',
        #                                'mysql_bufferpool_wait_free',
        #                                'mysql_tmp_disk_tables'])
    for s in services:
        if (
            s not in services_enabled_types and
            (s in services_attrs or
             (not no_default_checks and
              bool(eval(s))))  # pylint: disable=W0123
        ):
            if 'ovh-g3-1' in host and s == 'swap':
                import pdb;pdb.set_trace()  ## Breakpoint ##

            services_enabled_types.append(s)
    checks = []
    for svc in services_enabled_types:
        if svc in ['mongodb', 'mongodb_auth']:
            continue
        if svc in services_multiple:
            default_vals = {'web': {host: {}}, 'tomcat': {host: {}}}
            if svc in ['drbd', 'disk_space', 'processes', 'sar', 'rbl',
                       'fullpath_processes', 'nic_card', 'supervisor']:
                values = eval(svc)  # pylint: disable=W0123
            else:
                values = services_attrs.get(svc,
                                            default_vals.get(svc, {}))
            keys = [a for a in values]
            for v in keys:
                vdata = services_attrs.get(svc, {}).get(v, {})
                skey = svc_name('{1}_{2}'.format(host, svc, v).upper())
                svc_attrs = get_svc_attrs(services_default_attrs, svc)
                ss = add_check(host,
                               services_enabled,
                               svc,
                               skey,
                               svc_attrs,
                               vdata)[skey]
                # switch between
                # HTTP_STRING / HTTP_STRING_AUTH
                # HTTPS_STRING / HTTPS_STRING_AUTH
                if svc in ['fullpath_processes', 'processes']:
                    for pattern in [
                        'fail2ban',
                    ]:
                        if re.search(pattern, v):
                            ss['vars.check_interval'] = '19200m'
                    ss['vars.process'] = v
                mongo_auth = False
                # let us authenticate to mongodb by defining
                # vars.mongo_user
                # vars.mongo_password on the host definition
                if 'mongo' in svc:
                    for i in ['mongo_user', 'mongo_password']:
                        if attrs.get(i, ''):
                            ss['vars.' + i] = attrs[i]
                            mongo_auth = True
                if mongo_auth:
                    ss['check_command'] = 'CSSH_CHECK_MONGODB_AUTH'
                if svc == 'rbl':
                    ss['vars.checked_address'] = v
                if svc == 'sar':
                    ss['vars.sar_profile'] = v
                if svc == 'web':
                    if ss.get('vars.http_remote', False):
                        command = 'CSSH_HTTP'
                        http_host = '127.0.0.1'
                        ss.setdefault('vars.http_host', http_host)
                    else:
                        command = 'C_HTTP'
                    http_port = '80'
                    if ss.get('vars.http_ssl', False):
                        http_port = '443'
                        command += 'S'
                    command += '_STRING'
                    if ss.get('vars.http_auth', False):
                        command += '_AUTH'
                    if ss.get('vars.http_expect'):
                        command += '_E'
                    ss.setdefault('check_command', command)
                    http_port = ss.setdefault('vars.port', http_port)
                    # switch service to not alert if it is
                    # selected in custom attributes
                    simports = ss.setdefault('import', [])
                    for simported in ['ST_WEB']:
                        if simported not in simports:
                            simports.append(simported)
                    # transform value in string: ['a', 'b'] => '"a" -s "b"'
                    if 'vars.strings' in ss:
                        ss['vars.strings'] = reencode_webstrings(
                            ss['vars.strings'])
                    # with this a http check can be as simple as:
                    # web:
                    #   www.domain.com: {}
                    #   www.domain.net: {strings: net}
                    if (
                        ('vars.http_servername' not in ss) and
                        ('.' in v)
                    ):
                        # check that v is DNS resolvable
                        socket.setdefaulttimeout(2)
                        try:
                            socket.gethostbyname(v)
                            ss['vars.http_servername'] = v
                        except (Exception,):
                            pass
                if svc in ['drbd']:
                    ss['vars.device'] = v
                if svc in ['disk_space', 'nic_card']:
                    ss[{'disk_space': 'vars.path',
                        'nic_card': 'vars.interface'}[svc]] = v
                if svc == 'supervisor':
                    ss['vars.command'] = v
                object_uniquify(ss)
                if (
                    svc == 'web' and
                    "{0}".format(ss.get('vars.http_ssl', '')) == "1" and
                    ss.get('vars.http_ssl_check', True)
                ):
                    check_cert = copy.deepcopy(ss)
                    for i in ('vars.strings',):
                        check_cert.pop(i, None)
                    check_cert['import'] = ['ST_CERT']
                    d = check_cert['service_description'] = check_cert[
                        'service_description'].replace('WEB', 'HTTPS_CERT')
                    check_cert['check_command'] = check_cert['check_command'].replace(
                        '_STRING', '_CERT')
                    checks.append(check_cert)
                    rdata['services_enabled'][d] = check_cert
                checks.append(ss)
        else:
            skey = svc_name('{1}'.format(host, svc).upper())
            svc_attrs = get_svc_attrs(services_default_attrs, svc)
            ss = add_check(host,
                           services_enabled,
                           svc,
                           skey,
                           svc_attrs,
                           services_attrs.get(svc, {}))[skey]
            checks.append(ss)
    for ss in checks:
        add_notification(ss, notification, default_notifiers, is_service=True)
        object_uniquify(ss)
    return rdata


def get_svc_attrs(default_attrs, ksvc):
    svc_attrs = default_attrs.setdefault(ksvc, OrderedDict())
    svc_attrs.setdefault('import', ['ST_{0}'.format(ksvc.upper())])
    return svc_attrs


def order_keys(data):
    def sort_keys(k):
        s = '1_'
        if k == 'import':
            s = '0_'
        return s + k
    keys = [a for a in data]
    keys.sort(key=sort_keys)
    return [(a, data[a]) for a in keys]


def add_check(host, services_enabled, svc, skey, default_value, vdata):
    ss = __salt__['mc_utils.dictupdate'](copy.deepcopy(default_value), vdata)
    ss['host.name'] = host
    ss['service_description'] = skey
    ss['vars.makinastates_service_type'] = svc
    services_enabled[skey] = ss
    return services_enabled
