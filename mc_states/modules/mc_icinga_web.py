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

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

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

        icinga_cgi
            dictionary to store values used in templates given in
            vh_content_source and vh_top_source

            enabled
                enable a web directory to serve cgi files. If True,
                icinga-cgi will no be installed and configured
                automatically.

            web_directory
                location under which webpages of icinga-cgi
                will be available
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

   exclude_customvars_xml
       dictionary to store values of exclude_customvars.xml
       configuration file

       settings
           list of settings added in exclude_customvars.xml file

   access_xml
       dictionary to store values of access.xml configuration file

       instances
           list of icinga instances
       default
           dictionary which describe defaults rights
           (applied for all hosts by defaults)


           access
               readwrite
                  folders
                      dictionary of folders in readwrite access
                      the structure is:

                      name
                          path_to_folder

                  files
                      dictionary of files in readwrite access
                      the structure is:

                      name
                          path_to_file

               read
                  folders
                      dictionary of folders in read only access
                      the structure is:

                      name
                          path_to_folder

                  files
                      dictionary of files in read only access
                      the structure is:

                      name
                          path_to_file
               write
                  folder
                      dictionary of folders in write only access
                      the structure is:

                      name
                          path_to_folder
                  files
                      dictionary of files in write only access
                      the structure is:

                      name
                          path_to_file
               execute
                  folder
                      dictionary of folders with execute access
                      the structure is:

                      name
                          path_to_folder
                  files
                      dictionary of files with execute access
                      the structure is:

                      name
                          path_to_files
       hosts
           dictionary to store access for a specific host

           hostname
               "hostname" must be changed by the "hostname"

               type
                   "local" or "ssh"
               ssh_config
                   dictionary to store ssh connection parameters i
                   (used only if "type" is "ssh")

                   host
                       ssh hostname
                   port
                       ssh port
                   auth
                       type
                           "key" or "password"
                       user
                           ssh login
                       password
                           ssh password
                       private_key
                           file with ssh private key

                   access
                       dictionary with the same structure that
                       the default access dictionary

                       useDefault
                           whether the defaults access are applied or note
                       readwrite
                           folders
                               dictionary of folders in readwrite access
                               the structure is:

                               name
                                   path_to_folder

                           files
                               dictionary of files in readwrite access
                               the structure is:

                               name
                                   path_to_file

                       read
                           folders
                               dictionary of folders in read only access
                               the structure is:

                               name
                                   path_to_folder

                           files
                               dictionary of files in read only access
                               the structure is:

                               name
                                   path_to_file
                       write
                           folder
                               dictionary of folders in write only access
                               the structure is:

                               name
                                   path_to_folder
                           files
                               dictionary of files in write only access
                               the structure is:

                               name
                                   path_to_file
                       execute
                           folder
                               dictionary of folders with execute access
                               the structure is:

                               name
                                   path_to_folder
                           files
                               dictionary of files with execute access
                               the structure is:

                               name
                                   readwrite

   auth_xml
       dictionary to store values of auth.xml configuration file

       settings
           auth_provider
               "auth_provider" must be changed by the
               "auth provider" or "default"

           auth_create
               "true" or "false"
           aut_update
               "true" or "false"
           auth_resume
               "true" or "false"
           auth_groups
               group name concerned by this configuration
           auth_enable
               "true" or "false"
           auth_authoritative
               "true" or "false"

   cronks_xml
       dictionary to store values of cronks.xml configuration file

       cronks
           cronksname
               "cronksname" must be replaced with the cronk name
               dictionary in which each key will be treated as a parameter

       categories
           categoryname
               "categoryname" must be replaced with the category name
               dictionary in which each key will be treated as a parameter

   databases_xml
       dictionary to store values of databases.xml configuration file

       icinga
           dictionary to store parameters about ido2db database

       icinga_web
           dictionary to store parameters about icinga-web database

   factories_xml
       dictionary to store values of factories.xml configuration file

       storages
           storagename
           "storagename" must be replaced with the storage name
           dictionary in which each key will be treated as a parameter

   icinga_xml
       dictionary to store values of icinga.xml configuration file

       settings
           dictionary in which each key will be treated as a parameter

   logging_xml
       dictionary to store values of logging.xml configuration file

       loggers
           default
               name of the default logger
           loggername
               "loggername" must replaced with the logger name
               dictionary in which each key will be treated as a parameter


   module_appkit_xml
       dictionary to store values of module_appkit.xml configuration file

       settings
           ajax.timeout
               ajax timeout
           debug.verbose
               list

   module_cronks_xml
       dictionary to store values of module_cronks.xml configuration file

       enable
           "true" or "false"

       settings
            dictionary in which each key will be treated as a parameter

   module_reporting_xml
       dictionary to store values of module_reporting.xml configuration file

       enable
           "true" or "false"

           settings
              jasperconfig.default
                  jasper_url
                      jasper url
                  jasper_user
                      jasper user
                  jasper_pass
                      jasper pass
                  tree_root
                      tree root


   module_web_xml
       dictionary to store values of module_web.xml configuration file

       enable
           "true" or "false"

   settings_xml
       dictionary to store values of settings.xml configuration file

       settings
         dictionary in which each key will be treated as a parameter

   sla_xml
       dictionary to store values of sla.xml configuration file

       settings
           dictionary in which each key will be treated as a parameter

   translation_xml
       dictionary to store values of translation.xml configuration file

       available_locales
           default_locale
               default locale
           default_timezone
               default timezone
           available_locales
               lang
                   "lang" must be replaced with the lang
                   dictionary in which each key will be treated
                   as a parameter
       translators
           default_domain
               default domain
           translators
               translatorname
               "translatorname" must be replaced with the translator name

               dictionary in which each key will be treated as a parameter


   userpreferences_xml
       dictionary to store values of userpreferences.xml configuration file

       org_icinga_grid_pagerMaxItems
           number
       org_icinga_grid_refreshTime
           number
       org_icinga_grid_outputLength
           number
       org_icinga_tabslider_changeTime
           number
       org_icinga_cronk_default
           text
       org_icinga_bugTrackerEnabled
           "true" or "false"
       org_icinga_errorNotificationsEnabled
           "true" or "false"
       org_icinga_autoRefresh
           "true" or "false"
       org_icinga_status_refreshTime
           number
       org_icinga_cronk_liststyle
           "list"

   views_xml
       dictionary to store values of views.xml configuration file

       dql
           target
           "target" must be replaced with the target

           content
               plain text for the dql tag


'''
@mc_states.utils.lazy_subregistry_get(__salt__, __name)
def _settings():
    grains = __grains__
    pillar = __pillar__
    locs = __salt__['mc_locations.settings']()


    # get default ido database connectionfrom mc_icinga
    icinga_settings =  __salt__['mc_icinga.settings']()
    ido2db_database= icinga_settings['modules']['ido2db']['database']


    icinga_web_reg = __salt__[
        'mc_macros.get_local_registry'](
            'icinga_web', registry_format='pack')

    password_web_db = icinga_web_reg.setdefault(
        'web.db_password',
        __salt__['mc_utils.generate_password']())
    password_web_root_account = icinga_web_reg.setdefault(
        'web.root_account_password',
        __salt__['mc_utils.generate_password']())

    web_database = {
        'type': "pgsql",
        'host': "localhost",
        'port': 5432,
        # 'socket': "",
        'user': "icinga_web",
        'password': password_web_db,
        'name': "icinga_web",
    }

    root_account = {
        'password': password_web_root_account,
        'salt': isalt,
    }

    has_sgbd = (
        (
            ('host' in web_database)
            and (
                web_database['host'] in ['localhost',
                                         '127.0.0.1',
                                         grains['host']]
            )
        )
        or ('socket' in web_database))


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
    data = __salt__['mc_utils.defaults'](
        'makina-states.services.monitoring.icinga_web', {
            'package': ['icinga-web'],
            'configuration_directory': locs['conf_dir']+"/icinga-web",
            'has_pgsql': ('pgsql' == web_database['type']
                          and has_sgbd),
            'has_mysql': ('mysql' == web_database['type']
                          and has_sgbd),
            'modules': {
                'nagvis': NAVGIS_DEFAULTS,
                    'pnp4nagios': {
                        'enabled': True,
                        'package': ['icinga-web-pnp'],
                        'cronks_extensions_templates': {
                            'pnp-host-extension': {
                                'match_pattern': "icinga-(host-template|.+-host-problems)",
                                'option': {
                                    'rowEvents': {
                                        'parameter': {
                                            'title': "PNP4Nagios",
                                            'menuid': "pnp4nagios",
                                            'items': {
                                                'parameter': {
                                                    'target': "sub",
                                                    'handler': {
                                                        'click': "Cronk.grid.handler.URL.imagePanel",
                                                    },
                                                    'handlerArguments': {
                                                        'src': "<![CDATA[http://pnp4nagios.localhost/pnp4nagios/index.php/image?host={host_name}&srv=_HOST_&view=0]]>",
                                                        'iconCls': "icinga-icon-image-arrow",
                                                        'width': 400,
                                                        'title': "Hostgraph for {host_name}",
                                                    },

                                                    'conditions': {
                                                        'parameter': {
                                                            'condition': "show",
                                                            'fn': "<![CDATA[ \n \
                                                                function() { \n \
                                                                    if (this.getRecord().get(\"process_performance_data\") == \"1\") { \n \
                                                                        return true; \n \
                                                                    } else { \n \
                                                                        return false; \n \
                                                                    } \n \
                                                                } \n \
                                                            ]]>",
                                                        },
                                                    },
                                                    'model': "",
                                                    'xtype': "grideventbutton",
                                                    'menuid': "pnp4nagios_host_image_hover",
                                                    'iconCls': "icinga-icon-image-arrow",
                                                    'tooltip': "Host performance chart",
                                                    'text': "Graph",
                                                },
                                                'parameter_1': {
                                                    'target': "sub",
                                                    'handler': {
                                                        'click': "Cronk.grid.handler.URL.open",
                                                    },
                                                    'handlerArguments': {
                                                        'cronkTitle': "Chart for {host_name}",
                                                        'url': "<![CDATA[{{data.url}}/graph?host={host_name}&srv=_HOST_]]>",
                                                        'activateOnClick': "true",
                                                    },
                                                    'conditions': {
                                                        'parameter': {
                                                            'condition': "show",
                                                            'fn': "<![CDATA[ \n \
                                                                function() { \n \
                                                                    if (this.getRecord().get(\"process_performance_data\") == \"1\") { \n \
                                                                        return true; \n \
                                                                    } else { \n \
                                                                        return false; \n \
                                                                    } \n \
                                                                } \n \
                                                            ]]>",
                                                        },
                                                    },
                                                    'model': "",
                                                    'xtype': "grideventbutton",
                                                    'menuid': "pnp4nagios_host_detail",
                                                    'iconCls': "icinga-icon-hostlightning",
                                                    'tooltip': "Chart Detail for this host",
                                                    'text': "Detail",
                                                },
                                            },
                                        },
                                    },
                                },
                                'fields': {
                                    'process_performance_data': {
                                        'datasource': {
                                            'field': "HOST_PROCESS_PERFORMANCE_DATA",
                                        },
                                        'display': {
                                            'visible': "false",
                                            'label': "",
                                        },
                                        'filter': {
                                            'enabled': "false",
                                        },
                                        'order': {
                                            'enabled': "false",
                                            'default': "false",
                                        },
                                    },
                                },
                            },
                            'pnp-service-extension': {
                                'match_pattern': "icinga-(service-template|.+-service-problems)",
                                'option': {
                                    'rowEvents': {
                                        'parameter': {
                                            'title': "PNP4Nagios",
                                            'menuid': "pnp4nagios",
                                            'items': {
                                                'parameter': {
                                                    'target': "sub",
                                                    'handler': {
                                                        'click': "Cronk.grid.handler.URL.imagePanel",
                                                    },
                                                    'handlerArguments': {
                                                        'src': "<![CDATA[http://pnp4nagios.localhost/pnp4nagios/index.php/image?host={host_name}&srv={service_name}&view=0]]>",
                                                        'iconCls': "icinga-icon-image-arrow",
                                                        'width': 400,
                                                        'title': "Servicegraph for {service_name}",
                                                    },

                                                    'conditions': {
                                                        'parameter': {
                                                            'condition': "show",
                                                            'fn': "<![CDATA[ \n \
                                                                function() { \n \
                                                                    if (this.getRecord().get(\"process_performance_data\") == \"1\") { \n \
                                                                        return true; \n \
                                                                    } else { \n \
                                                                        return false; \n \
                                                                    } \n \
                                                                } \n \
                                                            ]]>",
                                                        },
                                                    },
                                                    'model': "",
                                                    'xtype': "grideventbutton",
                                                    'menuid': "pnp4nagios_service_image_hover",
                                                    'iconCls': "icinga-icon-image-arrow",
                                                    'tooltip': "Service performance chart",
                                                    'text': "Graph",
                                                },
                                                'parameter_1': {
                                                    'target': "sub",
                                                    'handler': {
                                                        'click': "Cronk.grid.handler.URL.open",
                                                    },
                                                    'handlerArguments': {
                                                        'cronkTitle': "Chart for {host_name}/{service_name}",
                                                        'url': "<![CDATA[http://pnp4nagios.localhost/pnp4nagios/index.php/graph?host={host_name}&srv={service_name}]]>",
                                                        'activateOnClick': "true",
                                                    },
                                                    'conditions': {
                                                        'parameter': {
                                                            'condition': "show",
                                                            'fn': "<![CDATA[ \n \
                                                                function() { \n \
                                                                    if (this.getRecord().get(\"process_performance_data\") == \"1\") { \n \
                                                                        return true; \n \
                                                                    } else { \n \
                                                                        return false; \n \
                                                                    } \n \
                                                                } \n \
                                                            ]]>",
                                                        },
                                                    },
                                                    'model': "",
                                                    'xtype': "grideventbutton",
                                                    'menuid': "pnp4nagios_service_detail",
                                                    'iconCls': "icinga-icon-hostlightning",
                                                    'tooltip': "Chart Detail for this service",
                                                    'text': "Detail",
                                                },
                                            },
                                        },
                                    },
                                },
                                'fields': {
                                    'process_performance_data': {
                                        'datasource': {
                                            'field': "SERVICE_PROCESS_PERFORMANCE_DATA",
                                        },
                                        'display': {
                                            'visible': "false",
                                            'label': "",
                                        },
                                        'filter': {
                                            'enabled': "false",
                                        },
                                        'order': {
                                            'enabled': "false",
                                            'default': "false",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                'root_account': {
                    'login': "root",
                    'hashed_password': hmac.new(root_account['salt']
                                               ,root_account['password']
                                               ,digestmod=hashlib.sha256).hexdigest(),
                    'salt': root_account['salt'],
                },
                'databases': {
                    'ido2db': ido2db_database,
                    'web': web_database,
                },
                'nginx': {
                    'domain': "icinga-web.localhost",
                    'doc_root': "/usr/share/icinga-web/www/",
                    'vh_content_source': "salt://makina-states/files/etc/nginx/sites-available/icinga-web.content.conf",
                    'vh_top_source': "salt://makina-states/files/etc/nginx/sites-available/icinga-web.top.conf",
                    'icinga_web': {
                        'web_directory': "/icinga-web",
                        'images_dir': "/usr/share/icinga-web/app/modules/$1/pub/images/$2",
                        'styles_dir': "/usr/share/icinga-web/app/modules/$1/pub/styles/$2",
                        'bpaddon_dir': "/usr/share/icinga-web/app/modules/BPAddon/pub",
                        'ext3_dir': "/usr/share/icinga-web/lib/ext3/",
                        'fastcgi_pass': "unix:/var/spool/www/icinga-web_localhost.fpm.sock",
                    },
                    'icinga_cgi': {
                        'enabled': False, # icinga cgi will not be configured. It is done in services.monitoring.icinga
                        'web_directory': "/icinga",
                        'realm': "Authentication",
                        'htpasswd_file': "/etc/icinga/htpasswd.users",
                        'htdocs_dir': "/usr/share/icinga/htdocs/",
                        'images_dir': "/usr/share/icinga/htdocs/images/$1",
                        'styles_dir': "/usr/share/icinga/htdocs/stylesheets/$1",
                        'cgi_dir': "/usr/lib/cgi-bin/",
                        'uwsgi_pass': "127.0.0.1:3030",
                    },
                },
                'phpfpm': {
                    'open_basedir': "/usr/share/icinga-web/:/var/cache/icinga-web/:/var/log/icinga-web/",
                    'extensions_packages': ['php5-pgsql'],
                    'doc_root': '/usr/share/icinga-web/',
                    # 'session_save_path': '/var/lib/php5',
                    'session_auto_start': 0,
                },
                'exclude_customvars_xml': {
                    'settings': [],
                },
                'access_xml': {
                    'instances': ["localhost"],
                    'defaults': {
                        'access': {
                            'readwrite': {
                                'folders': {
                                    'icinga_objects': "/etc/icinga/objects",
                                },
                                'files': {
                                    'icinga_cfg': "/etc/icinga/icinga.cfg",
                                },
                            },
                            # 'read': {
                            #     'folders': {},
                            #     'files': {},
                            # },
                            'write': {
                                # 'folders': {},
                                'files': {
                                    'icinga_pipe': (
                                        "/var/lib/icinga/rw/icinga.cmd"),
                                },
                            },
                            'execute': {
                                # 'folders': {},
                                'files': {
                                    'icinga_service': (
                                        "/usr/bin/service icinga"
                                    ),
                                    'icinga_bin': "/usr/sbin/icinga",
                                    'echo': "/bin/echo",
                                    'printf': "printf",
                                    'cp': "/bin/cp",
                                    'ls': "/bin/ls",
                                    'grep': "/bin/grep",
                                },
                            },
                        },
                    },
                    'hosts': {
                        'localhost': {
                            'type': 'local',
                            # 'ssh_config': {
                            #     'host': "debian.www",
                            #     'port': 22,
                            #     'auth': {
                            #         'type': "key",
                            #         'user': "icinga",
                            #         'private_key': (
                            #            "/usr/local/icinga-web/id_debian"),
                            #         'password': "123",
                            #     },
                            # },
                            'access': {
                                'useDefaults': "true",
                                # 'readwrite': {
                                #     'folders': {},
                                #     'files': {},
                                # },
                                # 'read': {
                                #     'folders': {},
                                #     'files': {},
                                # },
                                # 'write': {
                                #     'folders': {},
                                #     'files': {},
                                # },
                                # 'execute': {
                                #     'folders': {},
                                #     'files': {},
                                # },
                            },
                        },
                    },
                },
                'auth_xml': {
                    'settings': {
                        'defaults' : {
                            'auth_create': "false",
                            'auth_update': "false",
                            'auth_resume': "true",
                            'auth_groups': "icinga_user",
                            'auth_enable': "true",
                            'auth_authoritative': "true",
                         },
                        'auth_key': {
                            'auth_create': "false",
                            'auth_update': "false",
                            'auth_resume': "true",
                            'auth_groups': "icinga_user",
                            'auth_enable': "true",
                            'auth_authoritative': "true",
                        },
                    },
                },
                'cronks_xml': {
                    'cronks': {
                        'iframeViewIcingaDocsEn': {
                            'module': "Cronks",
                            'action': "System.IframeView",
                            'hide': "false",
                            'description': "Icinga docs english version",
                            'name': "Docs EN",
                            'image': "cronks.Info2",
                            'categories': "misc",
                            'position': 300,
                            'parameters': {
                                'url': "<![CDATA[/icinga-web/docs/en/index.html]]>",
                            },
                        },
                        'iframeViewIcingaDocsDe': {
                            'module': "Cronks",
                            'action': "System.IframeView",
                            'hide': "false",
                            'description': "Icinga docs german version",
                            'name': "Docs DE",
                            'image': "cronks.Info2",
                            'categories': "misc",
                            'position': 310,
                            'parameters': {
                                'url': "<![CDATA[/icinga-web/docs/de/index.html]]>",
                            },
                        },
                        'icingaReportingDefault': {
                            'module': "Reporting",
                            'action': "Cronk.Main",
                            'hide': "true",
                            'enabled': "false",
                            'description': "Seamless Jasper Integration",
                            'name': "Reporting",
                            'categories': "icinga-reporting",
                            'image': "cronks.Weather_Cloud_Sun",
                            'groupsonly': "appkit_admin",
                            'parameters': {
                                'jasperconfig': "modules.reporting.jasperconfig.default",
                                'enable_onthefly': 1,
                                'enable_repository': 1,
                                'enable_scheduling': 1,
                            },
                        },
                    },
                    'categories': {
#                       'misc': {,
#                            'title': "Misc",
#                            'visible': "true",
#                            'position': 99,
#                       },
                    },
                },
                'databases_xml': {
                    'icinga': {
                        'enable_dbconfig_common': True,
                        'charset': "utf8",
                        'use_retained': "true",
                        'Doctrine_Core_ATTR_MODEL_LOADING': "CONSERVATIVE",
                        'load_models': "%core.module_dir%/Api/lib/database/models/generated",
                        'models_directory': "%core.module_dir%/Api/lib/database/models",
                        'date_format': "<![CDATA[YYYY-MM-DD HH24:MI:SS]]>",
                        'caching': {
                            'enabled': "false",
                            'driver': "apc",
                            'use_query_cache': "true",
                        },
                    },
                    'icinga_web': {
                        'enable_dbconfig_common': True,
                        'charset': "utf8",
                        'Doctrine_Core_ATTR_MODEL_LOADING': "CONSERVATIVE",
                        'load_models': "%core.module_dir%/AppKit/lib/database/models/generated",
                        'models_directory': "%core.module_dir%/AppKit/lib/database/models",
                        'date_format': "<![CDATA[YYYY-MM-DD HH24:MI:SS]]>",
                        'caching': {
                            'enabled': "false",
                            'driver': "apc",
                            'use_query_cache': "true",
                            'use_result_cache': "true",
                            'result_cache_lifespan': "60",
                        },
                    },
                },
                'factories_xml': {
                    'storages': {
                        'AppKitDoctrineSessionStorage': {
                            'session_cookie_lifetime': 0,
                            'session_name': "icinga-web",
                            'gzip_level': 6,
                        },
                    },
                },
                'icinga_xml': {
                    'settings': {
                        'bogus.include': "true",
                    },
                },
                'logging_xml': {
                    # 'loggers': {
                    #     'default': "icinga-web",
                    #      'loggers': {
                    #          'icinga-debug': {
                    #               'class': "AgaviLogger",
                    #               'level': "",
                    #          },
                    #      },
                    # },
                },
                'module_appkit_xml': {
                    'settings': {
                        'ajax.timeout': 240000,
                        'debug.verbose': ["API_Views_ApiDQLViewModel"],
                    },
                },
                'module_cronks_xml': {
                    'enabled': "true",
                    'settings': {
                        # 'search.numberMinimumLetters': 2,
                        # 'search.maximumResults': 200,
                    },
                },
                'module_reporting_xml': {
                    'enabled': "false",
                    'settings': {
                        'jasperconfig.default': {
                            'jasper_url': "http://127.0.0.1:8080/jasperserver",
                            'jasper_user': "jasperadmin",
                            'jasper_pass': "jasperadmin",
                            'tree_root': "/icinga/reports",
                        },
                    },
                },
                'module_web_xml': {
                    'enabled': "true",
                },
                'settings_xml': {
                    # 'settings': {
                    #     'available': "false",
                    #     'app_name': "My Custom Version",
                    # },
                },
                'sla_xml': {
                    'settings': {
                        'default_timespan': "-1 month",
                        'enabled': "false",
                    }
                },
                'translation_xml': {
                    # 'available_locales': {
                    #     'default_locale': "de",
                    #     'default_timezone': "GMT",
                    #     'available_locales': {
                    #         'de_DE': {
                    #             'description': "Deutsch",
                    #         },
                    #         'en': {
                    #             'description': "English",
                    #         },
                    #     },
                    # },
                    # 'translators': {
                    #     'default_domain': "icinga.default",
                    #     'translators': {
                    #         'date-tstamp': {
                    #             'date_formatter': {
                    #                 'type': "date",
                    #                 'format': "yyyy-MM-dd"
                    #             },
                    #         },
                    #     },
                    # },
                },
                'userpreferences_xml': {
                    'org_icinga_grid_pagerMaxItems': 25,
                    'org_icinga_grid_refreshTime': 300,
                    'org_icinga_grid_outputLength': 70,
                    'org_icinga_tabslider_changeTime': 10,
                    'org_icinga_cronk_default': "portalHello",
                    'org_icinga_bugTrackerEnabled': "false",
                    'org_icinga_errorNotificationsEnabled': "false",
                    'org_icinga_autoRefresh': "true",
                    'org_icinga_status_refreshTime': 60,
                    'org_icinga_cronk_liststyle': "list",
                },
                'views_xml': {
                    # 'dql': {
                    #     'TARGET_MYVIEW': {
                    #         'content': "<!-- - ... -->",
                    #     },
                    # },
                },
        })

        __salt__['mc_macros.update_local_registry'](
            'icinga_web', icinga_web_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
