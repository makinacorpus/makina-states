# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga_web:

mc_icinga_web / icinga_web functions
============================================

when it is written that "each key will be treated as a parameter",
if you add keys in dictionary, they will be added
in the configuration file with

::

<ae:paremeter name="{{key}}">{{value}}</ae:parameter>


when it is written that "foo must be replace with foo value", you can
add as many sub-dictionaries as you want. All sub-dictionaries must
have the same structure. It is to avoid a list but in templates
it is treated as if there was a list of dictionaries.

I have prefered

::

    'foo': {
        'n1': {
            'param1': "v1",
        },
        'n2': {
            'param1': "v2",
        },
    },

instead of

::

    'foo': [
        {'name': "n1",
         'param1': "v1",
        },
        {'name': "n2",
         'param1': "v2",
        },
    ]


When a real list is kept, It is precised below. Generally it is
when the content is not structures but simple values.

The template of xml configuration files use a lot of loops
in order to add content easily but it is not the case with
the ini files where directives are limited and always the same.

The "nginx" and "phpfpm" sub-dictionaries are given to
macros in \*\*kwargs parameter. If you add a key in,
you can access in the nginx configuration template
or in phpfpm configuration template. In ngin
x subdictionary, the "icinga_cgi" and "icinga_web"
keys store values used to fill the template.

Otherwise, the first level of subdictionaries is
for distinguish configuration files. There is one
subdictionary per configuration file. The key used
for subdictionary correspond to the name of the file
but the "." is replaced with a "_"

I have not found dtd/xsd files in order to verify
grammar of xml files.

Only the hashed password and the salt for the root
account for icinga-web interface are stored in settings.
The hashed password is not computed automatically from an
other value with the clear password (settings
dictionary doesn't contains the clear password)

I should add a state to compute the hash from clear
password but I don't have successfully done this.

The keys "has_pgsql" and "has_mysql" determine
if a local postgresql or mysql instance must be installed.
The default value is computed from default database parameters
If the connection is made through a unix pipe
or with the localhost hostname, the booleans are set to True.

The default parameters for icinga_ido database
connection are get from icinga settings.

In the templates, I didn't perform a lot of check.
For example if a value must be set only if a other
directive has a precise value, I didn't add a if statement.
It is possible to create invalid configuration files.

If in a list, each value must be unique, I tried
to have the elements of the list as dictionary keys.

For optional values which don't have a default value,
I didn't set them in the default dictionary but in the
templates, I have done::

    {% if data.get('foo', None) %}
    foo={{data.foo}}
    {% endif %}

Theses optional values corresponds to commented keys in
the default dictionary.


'''

# Import python libs
import logging
import mc_states.api

import hmac
import hashlib

__name = 'icinga_web'

log = logging.getLogger(__name__)
isalt = "0c099ae4627b144f3a7eaa763ba43b10fd5d1caa8738a98f11bb973bebc52ccd"
ngurl = "<![CDATA[http://nagvis.localhost/nagvis/frontend/nagvis-js/]]>"


def settings():
    '''
    icinga_web settings

    location
        installation directory

    package
        list of packages to install icinga-web
    configuration_directory
        directory where configuration files are located
    has_pgsql
        install and configure a postgresql service in order
        to store icinga-web data
        (no ido2db data)
    has_mysql
        install and configure a mysql service in order to store icinga-web data
        (no ido2db data)
    modules
        nagvis
            enable
                enable the nagvis module which add link to nagvis in icinga-web
            cronks_xml
                dictionary to store the cronks. The content is added in
                cronks.xml.  The structure is the same that 'cronks_xml'
                subdictionary.
        pnp4nagios
            enable
                enable the pnp4nagios module which add links to
                graphs in icinga-web
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
        It is the account created on first installation of icinga_web

        login
            login for root login on web interface
        hashed_password
            password for root login on web interface
        salt
            salt used to hash the password

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
            dictionary to store icinga-web database connection parameters

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

            icinga_web
                dictionary to store values used in templates given in
                vh_content_source and vh_top_source

                web_directory
                    location under which webpages of icinga-web will be
                    available
                images_dir
                    directory where images used by icinga-web are stored
                styles_dir
                    directory where css used by icinga-web are stored
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
                must be 0 to run icinga-web
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _g, _s = __grains__, __salt__
        locs = _s['mc_locations.settings']()

        # get default ido database connectionfrom mc_icinga
        icinga_settings = _s['mc_icinga2.settings']()
        ido2db_database = icinga_settings['modules']['ido2db']['database']
        icinga_web_reg = _s[
            'mc_macros.get_local_registry'](
                'icinga_web', registry_format='pack')
        password_web_db = icinga_web_reg.setdefault(
            'web.db_password',
            _s['mc_utils.generate_password']())
        password_web_root_account = icinga_web_reg.setdefault(
            'web.root_account_password',
            _s['mc_utils.generate_password']())
        if not password_web_root_account:
            password_web_root_account = icinga_web_reg[
                'web.root_account_password'] = _s[
                    'mc_utils.generate_password'](8)

        web_database = {
            'type': "pgsql",
            'host': "localhost",
            'port': 5432,
            # 'socket': "",
            'user': "icinga_web",
            'password': password_web_db,
            'name': "icinga_web",
        }

        for data in [ido2db_database, web_database]:
            data.setdefault('prefix', '')
        root_account = {
            'password': password_web_root_account,
            'salt': isalt,
        }

        has_sgbd = (
            (
                ('host' in web_database) and (
                    web_database['host'] in ['localhost',
                                             '127.0.0.1',
                                             _g['host']]
                )
            ) or ('socket' in web_database))

        NAVGIS_DEFAULTS = {
            'enabled': True,
            'cronks_xml': {
                'cronks': {
                    'iFrameViewNagvis': {
                        'module': "Cronks",
                        'action': "System.IframeView",
                        'hide': "false",
                        'description': "Nagvis Maps views",
                        'name': "Nagvis Display",
                        'image': "cronks.Info2",
                        'categories': "misc",
                        'position': 310,
                        'parameter': {
                            'url': ngurl,
                            # 'user': "",
                            # 'password': "",
                        },
                    },
                },
            },
        }
        data = _s['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga_web', {
                'package': ['icinga-web', 'php5-ldap',
                            'php5', 'php5-cli', 'php-pear',
                            'php5-xmlrpc', 'php5-xsl',
                            'php-soap', 'php5-gd',
                            'php5-ldap'],
                'configuration_directory': locs['conf_dir']+"/icinga-web",
                'create_pgsql': True,
                'has_pgsql': ('pgsql' == web_database['type'] and has_sgbd),
                'has_mysql': ('mysql' == web_database['type'] and has_sgbd),
                'modules': {
                    'nagvis': NAVGIS_DEFAULTS,
                    'pnp4nagios': {
                        "pnpfornagios_url": "http://phpfornagios.local",
                        'enabled': True,
                        'package': ['icinga-web-pnp'],
                        'cronks_extensions_templates': {
                            'pnp-host-extension.xml': (
                                "salt://makina-states/files/usr/share/"
                                "icinga-web/app/modules/Cronks/data/xml/"
                                "extensions/pnp-host-extension.xml"
                            ),
                            'pnp-service-extension.xml': (
                                "salt://makina-states/files/usr/share/"
                                "icinga-web/app/modules/Cronks/data/xml/"
                                "extensions/pnp-service-extension.xml"
                            ),
                        }
                    },
                },
                'root_account': {
                    'login': "root",
                    'clear': root_account['password'],
                    'hashed_password': hmac.new(
                        root_account['salt'],
                        root_account['password'],
                        digestmod=hashlib.sha256).hexdigest(),
                    'salt': root_account['salt'],
                },
                'ldap_auth': {
                    'url': '',  # ldap://
                    'binddn': '',
                    'bindpw': '',
                    'filter_user': "(&(uid=__USERNAME__))",
                    'base_dn': '',
                    'tls': False,
                },
                'databases': {'ido2db': ido2db_database,
                              'web': web_database},
                'nginx': {
                    'vhost_basename': 'icingaweb',
                    'ssl_cacert': '',
                    'ssl_cert': '',
                    'ssl_key': '',
                    'domain': "icinga-web.localhost",
                    'doc_root': "/usr/share/icinga-web/www/",
                    'vh_content_source': (
                        "salt://makina-states/files/etc/nginx/"
                        "sites-available/icinga-web.content.conf"),
                    'vh_top_source': (
                        "salt://makina-states/files/etc/"
                        "nginx/sites-available/icinga-web.top.conf"),
                    'icinga_web': {
                        'htpasswd_file': '/etc/icinga2/htpasswd.users',
                        'web_directory': "/icinga-web",
                        'images_dir': ("/usr/share/icinga-web/app"
                                       "/modules/$1/pub/images/$2"),
                        'styles_dir': ("/usr/share/icinga-web/app"
                                       "/modules/$1/pub/styles/$2"),
                        'bpaddon_dir': ("/usr/share/icinga-web/app"
                                        "/modules/BPAddon/pub"),
                        'ext3_dir': "/usr/share/icinga-web/lib/ext3/",
                        'fastcgi_pass': (
                            "unix:/var/spool/www/"
                            "icinga-web_localhost.fpm.sock"),
                    },
                },
                'phpfpm': {
                    'pool_name': 'icingaweb',
                    'open_basedir': (
                        "/usr/share/icinga-web/"
                        ":/etc"
                        ":/var/run/icinga2/cmd/"
                        ":/var/cache/icinga-web/"
                        ":/var/log/icinga-web/"),
                    'extensions_packages': ['php5-pgsql'],
                    'doc_root': '/usr/share/icinga-web/',
                    'session_auto_start': 0,
                },
                'templates': {},
                'has_jasper': False,
            }
        )
        if data['nginx'].get('ssl_redirect', False):
            if not data['nginx'].get('ssl_cert', None):
                cert, key, chain = _s['mc_ssl.get_configured_cert'](
                    data['nginx']['domain'], gen=True)
                data['nginx']['ssl_key'] = key
                data['nginx']['ssl_cert'] = cert + chain

        data['nginx']['icinga_web']['fastcgi_pass'] = (
            "unix:/var/spool/www/icingaweb.fpm.sock".format(
                data['nginx']['domain'].replace('.', '_')
            )
        )
        _s['mc_macros.update_local_registry'](
            'icinga_web', icinga_web_reg,
            registry_format='pack')
        return data
    return _settings()
