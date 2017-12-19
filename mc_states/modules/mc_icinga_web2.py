# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga_web2:

mc_icinga_web2 / icinga_web2 functions
============================================

'''

# Import python libs
import logging
import mc_states.api
import six

import hmac
import hashlib

__name = 'icinga_web2'

log = logging.getLogger(__name__)
isalt = "0c099ae4627b144f3a7eaa763ba43b10fd5d1caa8738a98f11bb973bebc52ccd"
ngurl = "<![CDATA[http://nagvis.localhost/nagvis/frontend/nagvis-js/]]>"


def settings():
    '''
    icinga_web2 settings

    location
        installation directory

    package
        list of packages to install icinga-web2
    configuration_directory
        directory where configuration files are located
    has_pgsql
        install and configure a postgresql service in order
        to store icinga-web2 data
        (no ido2db data)
    modules
        nagvis
            enable
                enable the nagvis module which add link to nagvis in icinga-web2
            cronks_xml
                dictionary to store the cronks. The content is added in
                cronks.xml.  The structure is the same that 'cronks_xml'
                subdictionary.
        pnp4nagios
            enable
                enable the pnp4nagios module which add links to
                graphs in icinga-web2
            package
                package to install for pnp4nagios integration
            cronks_extensions-templates
                dictionary in which, each key is the name of an extension
                template and the content of the dictionary contains the
                values to fill the template
                each 'key': "value" produce
                a "<parameter name={{key}}>{{value}}</parameter>".
                The key "parameter" or "parameter_*" produce
                a "<parameter></parameter>" tag.
                Each subdictionary add sub parameters tags.

    root_account
        Dictionary to store root account information.
        It is the account created on first installation of icinga_web2

        login
            login for root login on web interface
        password_hash
            password for root login on web interface
        salt
            salt used to hash the password

    nginx
        dictionary to store values of nginx configuration

        domain
            name of virtualhost created to serve webpages
        doc_root
            root location of virtualhost
        vh_content_source
            template file for nginx content file
        vh_top_source
            template file for nginx top file

        icinga_web2
            dictionary to store values used in templates given in
            vh_content_source and vh_top_source

            web_directory
                location under which webpages of icinga-web2 will be
                available
            images_dir
                directory where images used by icinga-web2 are stored
            styles_dir
                directory where css used by icinga-web2 are stored
            bpaddon_dir
                directory where bpaddon scripts are located
            ext3_dir
                directory where ext3 scripts are located
            fastcgi_pass
                socket used to contact fastcgi server in order to
                interpret php files

    phpfpm
        dictionary to store values of phpfpm configuration

        open_basedir
            paths to add to open_basedir
        extensions_package
            additional packages to install (such as php5-pgsql
            or php5-mysql for
            php database connection)
        doc_root
            root location for php-fpm
        session_auto_start
            must be 0 to run icinga-web2

    databases
        dictionary to store databases connections parameters

        ido2db
            dictionary to store ido2db database connection parameters

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

        web
            dictionary to store icinga-web2 database connection parameters

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


    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s, _g = __salt__, __grains__

        locs = _s['mc_locations.settings']()

        # get default ido database connectionfrom mc_icinga
        icinga_settings = _s['mc_icinga2.settings']()
        ido2db_database = icinga_settings['modules']['ido2db']['database']

        web_database = {
            'type': "pgsql",
            'host': "localhost",
            'port': 5432,
            # 'socket': "",
            'user': "icinga_web2",
            'password': 'icinga_web2',
            'name': "icinga_web2",
        }
        logrotate = _s['mc_logrotate.settings']()

        for data in [ido2db_database, web_database]:
            data.setdefault('prefix', '')
        has_sgbd = (
            (
                ('host' in web_database) and (
                    web_database['host'] in ['localhost',
                                             '127.0.0.1',
                                             _g['host']]
                )
            ) or
            ('socket' in web_database))
        data = _s['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga_web2', {
                'doc_root': "/usr/share/icingaweb2/public",
                'htpasswd': '/etc/icinga2web.users',
                'package': ['icingaweb2', 'php5-ldap',
                            'php5', 'php5-cli', 'php-pear',
                            'php5-xmlrpc', 'php5-xsl', 'apache2-utils',
                            'php-soap', 'php5-gd',
                            'php5-ldap'],
                'configuration_directory': locs['conf_dir'] + "/icinga-web2",
                'create_pgsql': True,
                'has_pgsql': ('pgsql' == web_database['type'] and has_sgbd),
                'modules': {
                    'pnp4nagios': {
                        'enabled': True,
                    },
                },
                'databases': {'ido2db': ido2db_database,
                              'web': web_database},
                'nginx': {
                    'ssl_cacert': '',
                    'ssl_cert': '',
                    'ssl_key': '',
                    'domain': "icinga-web2.localhost",
                    'doc_root': '{doc_root}',
                    'vhost_basename': 'icingaweb2',
                    'vh_content_source': (
                        "salt://makina-states/files/etc/nginx/"
                        "includes/icinga-web2.content.conf"),
                    'vh_top_source': (
                        "salt://makina-states/files/etc/"
                        "nginx/includes/icinga-web2.top.conf"),
                },
                'fastcgi_pass': (
                    "unix:/var/spool/www/"
                    "icinga-web2_localhost.fpm.sock"),
                'modules_enabled': {
                    'doc': {},
                    'setup': {},
                    'monitoring': {},
                    'translation': {}
                },
                'resources': {
                    'ldap': {
                        'type': 'ldap',
                        'hostname': 'localhost',
                        'port': '389',
                        'root_dn': 'ou=people,dc=icinga,dc=org',
                        'bind_dn': 'cn=admin,ou=people,dc=icinga,dc=org',
                        'bind_pw': 'secret',
                        'user_class': 'inetOrgPerson',
                        'user_name_attribute': 'uid',
                        'enabled': False,
                    },
                },
                'auths': [],
                'roles': {
                    'admins': {
                        'users': '',
                        'groups': '',
                        'permissions': '*',
                    },
                    'readonly': {
                        'users': 'readonly',
                        'permissions': ','.join([
                            "application/share/navigation",
                            "module/monitoring"
                        ])
                    }
                },
                'authentication_settings': {
                    'pgsql': {
                        'enabled': True,
                        'backend': 'db',
                        'resource': 'icingaweb2',
                    },
                    'web': {
                        'enabled': True,
                        'backend': 'external',
                    },
                    'ldap_a': {
                        'enabled': False,
                        'backend': 'ldap',
                        'resource': 'ldap',
                    },
                    'mysql': {
                        'enabled': False,
                        'backend': 'db',
                        'resource': 'icingaweb-mysql',
                    },
                },
                'groups': {
                    'ldap_g': {
                        'enabled': False,
                        'resource': 'ldap',
                        'user_backend': 'ldap_a',
                        'group_name_attribute': 'cn',
                        'base_dn': 'ou=group,dc=icinga,dc=org',
                        'backend': 'ldap',
                        'group_member_attribute': 'memberUid',
                        'group_class': 'groupOfNames',
                    }
                },
                'phpfpm': {
                    'pool_name': 'icingaweb2',
                    'include_path': (
                        '/usr/share/php'
                        ':/usr/share/icingaweb2/application'
                        ':/usr/share/icingaweb2/library'
                    ),
                    'open_basedir': None,
                    'open_basedir2': (
                        "/usr/share/icingaweb2/library"
                        ":/usr/share/icingaweb2/application"
                        ":{doc_root}"
                        ":/etc"
                        ":/usr/share/php"
                        ":/var/run/icinga2/cmd/"
                        ":/var/cache/icingaweb2/"
                        ":/var/log/icingaweb2/"),
                    'etcdir': '/etc/php/5.6',
                    'extensions_packages': ['php5-pgsql'],
                    'doc_root': '{doc_root}',
                    'session_auto_start': 0,
                },
                'users': {},
                'rotate': logrotate['days'],
                'configs': {
                    '/usr/share/icingaweb2/log/icingaweb2.log': {
                        'source': None,
                        'user': 'www-data',
                        'group': 'www-data',
                        'mode': '644'},
                    '/etc/logrotate.d/icinga2web.conf': {
                        'user': 'root',
                        'group': 'root',
                        'mode': '644'},
                    ('/etc/icingaweb2/modules/'
                     'monitoring/commandtransports.ini'): {
                         'user': 'www-data',
                         'mode': '644'},
                    ('/etc/icingaweb2/modules/'
                     'monitoring/backends.ini'): {
                         'user': 'www-data',
                         'mode': '644'},
                    '/etc/icingaweb2/authentication.ini': {
                        'user': 'www-data',
                        'mode': '644'},
                    '/etc/icingaweb2/resources.ini': {
                        'user': 'www-data',
                        'mode': '644'},
                    '/etc/icingaweb2/config.ini': {
                        'user': 'www-data',
                        'mode': '644'},
                    '/etc/icingaweb2/groups.ini': {
                        'user': 'www-data',
                        'mode': '644'},
                    '/etc/icingaweb2/authentication.ini': {
                        'user': 'www-data',
                        'mode': '644'},
                    '/etc/icingaweb2/roles.ini': {
                        'user': 'www-data',
                        'mode': '644'},
                },
                # 'log': 'syslog',
                'logging_log': 'file',
                'logging_file': '/usr/share/icingaweb2/log/icingaweb2.log',
                'logging_level': 'ERROR',
            }
        )

        for r, rdata in six.iteritems(data['resources']):
            if not rdata.get('enabled', False):
                continue
            srauth = '{0}_a'.format(r)
            try:
                rauth = data['authentication_settings'][srauth]
            except KeyError:
                pass
            else:
                rauth['enabled'] = True
            srgroup = '{0}_g'.format(r)
            try:
                rgroup = data['groups'][srgroup]
            except KeyError:
                pass
            else:
                rgroup['enabled'] = True
        for dbn, dbm in six.iteritems(
            {'web': 'icingaweb2',
             'ido2db': 'icinga2'}
        ):
            db = data['databases'][dbn]
            settings = data['resources'].setdefault(dbm, {})
            settings['type'] = "db"
            settings['db'] = db['type']
            settings['host'] = db['host']
            settings['port'] = db['port']
            settings['dbname'] = db['name']
            settings['username'] = db['user']
            settings['password'] = db['password']

        if data['nginx'].get('ssl_redirect', False):
            if not data['nginx'].get('ssl_cert', None):
                cert, key, chain = _s['mc_ssl.get_configured_cert'](
                    data['nginx']['domain'], gen=True)
                data['nginx']['ssl_key'] = key
                data['nginx']['ssl_cert'] = cert + chain

        if not data['auths']:
            data['auths'] = [a for a in data['authentication_settings']]
        data['auths'] = [a for a in data['auths']
                         if a in data['authentication_settings']]
        data['fastcgi_pass'] = (
            "unix:/var/spool/www/icingaweb2.fpm.sock".format(
                data['nginx']['domain'].replace('.', '_')
            )
        )
        for r, rdata in six.iteritems(data['roles']):
            for i in rdata.get('users', '').split(','):
                data['users'].setdefault(i, {})
        icinga_web2_reg = _s[
            'mc_macros.get_local_registry'](
            'icinga_web2', registry_format='pack')
        for i, idata in six.iteritems(data['users']):
            password = idata.setdefault(
                'password',
                icinga_web2_reg.setdefault(
                    'web.{0}_password'.format(i),
                    _s['mc_utils.generate_password']()))
            salt = idata.setdefault(
                'salt',
                icinga_web2_reg.setdefault(
                    'web.{0}_salt'.format(i),
                    _s['mc_utils.generate_password'](64)))
            hpw = _s['cmd.run'](
                "echo '{0}'|openssl passwd -stdin -1 -salt '{1}'".format(
                    password, salt),
                python_shell=True)
            idata.update({
                'login': i,
                'password_hash': hpw,
            })
        _s['mc_macros.update_local_registry'](
            'icinga_web2', icinga_web2_reg,
            registry_format='pack')
        return data
    return _settings()
