# -*- coding: utf-8 -*-
'''
.. _module_mc_nagvis:

mc_nagvis / nagvis functions
============================================

You can add your own key/values in backends,
rotations and actions subdictionaries.

'''

# Import python libs
import logging
import copy
import mc_states.api

import hashlib

__name = 'nagvis'

log = logging.getLogger(__name__)


def settings():
    '''
    nagvis settings

    location
        installation directory

    package
        list of packages to install navgis
    configuration_directory
        directory where configuration files are located

    root_account
        dictionary to store root account information.
        It is the account with the userId=1 in the sqlite database

        login
            login for root login on web interface
        hashed_password
            password for root login on web interface
        salt
            salt used to hash the password
        default_password
            the password inserted when nagvis is installed.
            it is to check that the password was not previously modified

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

            nagvis
                dictionary to store values used in templates given in
                vh_content_source and vh_top_source

                web_directory
                    location under which webpages of nagvis will be available
                fastcgi_pass
                    socket used to contact fastcgi server in order
                    to interpret php files

        phpfpm
            dictionary to store values of phpfpm configuration

            open_basedir
                paths to add to open_basedir
            doc_root
                root location for php-fpm
            session_auto_start
                must be 0 to run nagvis

        global_php
            dictionary to store values used in global.php

            AUTH_PASSWORD_SALT
                salt used for password. We notice the salt used is
                the same for all passwords which is a security weakness.

        nagvis_ini_php
            dictionary to store values used in nagvis_ini_php
            each subdictionary represents an ini section
            if a key is not present, the directive will
            not be added in the configuration file

            global
                dictionary to store values of global section in nagvis_ini_php

                authmodule
                    name of authentication module
                authorisationmodule
                    name of authorisation module
                file_group
                    group used to launch nagvis script
                file_mode
                    default file mode for temporary files
                geomap_server
                    url of geomap server
                http_proxy
                    http proxy
                http_proxy_auth
                    auth for http proxy

            paths
                dictionary to store values of paths section in nagvis_ini_php

                base
                    location of nagvis installation
                htmlbase
                    location of php files. It should be the same value that
                    nginx.nagvis.web_directory

            defaults
                dictionary to store values of defaults section in
                nagvis_ini_php

                backend
                    default backend

            automap
                dictionary to store values of automap section in nagvis_ini_php

                defaultparams
                    default parameters
                defaultroot
                    default root
                graphvizpath
                    location of graphviz binary

            backends
                dictionary to store values of backends section in
                nagvis_ini_php each subdictionary corresponds to
                a "backend_foo" section

                foo
                    dictionary to store values of foo backend. foo must
                    be replaced with the name of the backend
                    the keys and values expected depends on the backend type

                    backendtype
                        type of backend

            rotations
                dictionary to store values of rotations section
                in nagvis_ini_php each subdictionary corresponds
                to a "rotation_foo" section

                foo
                    dictionary to store values of foo rotation.
                    foo must be replaced with the name of the rotation

                    maps
                        list of maps which are in the rotation
                    interval
                        interval

            actions
                dictionary to store values of actions section in nagvis_ini_php
                each subdictionary corresponds to a "action_foo" section

                foo
                    dictionary to store values of foo action.
                    foo must be replaced with the name of the action

                    action_type
                        type of action
                    obj_type
                        "host" or "service" or "host,service"
                    condition
                        condition to apply the action
                    domain
                        domain
                    username
                        username

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locs = __salt__['mc_locations.settings']()

        nagvis_reg = __salt__[
            'mc_macros.get_local_registry'](
                'nagvis', registry_format='pack')

        password_web_root_account = nagvis_reg.setdefault(
            'web.root_account_password',
            __salt__['mc_utils.generate_password']())

        root_account = {
            'password': password_web_root_account,
            # if you change this, you must change it in php
            'salt': "29d58ead6a65f5c00342ae03cdc6d26565e20954",
        }

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.nagvis', {
                'package': ['nagvis'],
                'configuration_directory': locs['conf_dir']+"/nagvis",
                'root_account': {
                    # we considere that the root_account has the ID 1
                    'user': "admin",
                    'hashed_password': hashlib.sha1(
                        root_account['salt'] +
                        root_account['password']).hexdigest(),
                    'salt': root_account['salt'],
                    # default value that we find in nagvis configuration
                    'default_password': (
                        "868103841a2244768b2dbead5dbea2b533940e20"),
                },
                'nginx': {
                    'ssl_cacert': '',
                    'ssl_cert': '',
                    'ssl_key': '',
                    'domain': "nagvis.localhost",
                    'doc_root': "/usr/share/nagvis/www/",
                    'vh_content_source': (
                        "salt://makina-states/files/etc/nginx/"
                        "includes/nagvis.content.conf"
                    ),
                    'vh_top_source': (
                        "salt://makina-states/files/"
                        "etc/nginx/includes/nagvis.top.conf"),
                    'nagvis': {
                        'htpasswd_file': '/etc/icinga2/htpasswd.users',
                        'web_directory': "/nagvis",
                        'fastcgi_pass': (
                            "unix:/var/spool/www/"
                            "nagvis_localhost.fpm.sock"),
                    },
                },
                'phpfpm': {
                    'open_basedir': (
                        "/usr/share/php/php-gettext/"
                        ":/etc/nagvis/"
                        ":/var/lib/nagvis/"
                        ":/var/cache/nagvis/"),
                    'doc_root': '/usr/share/nagvis/',
                    'session_auto_start': 0,
                    'extensions_packages': ['php-gettext',
                                            'php-net-socket',
                                            'php-pear',
                                            'php5-sqlite'],
                },
                'global_php': {
                    'PROFILE': "false",
                    'DEBUG': "false",
                    'DEBUGLEVEL': 6,
                    'AUTH_PASSWORD_SALT': root_account['salt'],
                },
                'nagvis_ini_php': {
                    'global': {
                        'audit_log': 1,
                        'authmodule': "CoreAuthModSQLite",
                        'authorisationmodule': "CoreAuthorisationModSQLite",
                        'file_group': "www-data",
                        'file_mode': 660,
                        'geomap_server': "http://geomap.nagvis.org/",
                        # 'http_proxy': "",
                        # 'http_proxy_auth': "",
                    },
                    'paths': {
                        'base': "/usr/share/nagvis/",
                        'htmlbase': "/nagvis",
                        'htmlcgi': "/cgi-bin/icinga",
                    },
                    'defaults': {
                        'backend': "live_1",
                    },
                    'automap': {
                        'defaultroot': "/",
                        'graphvizpath': "/usr/bin/",
                    },
                    'worker': {
                        'interval': 5,
                    },
                    'backends': {
                        'live_1': {
                            'backendtype': "mklivestatus",
                            'socket': "tcp:localhost:6558",
                            # for icinga2
                            # 'socket': "unix:/var/run/icinga2/cmd/livestatus",
                            'htmlcgi': "/cgi-bin/icinga/",
                        },
                    },
                    'rotations': {
                        # 'demo': {
                        #      'maps': ("demo-germany,demo-ham-racks,"
                        #               "demo-load,demo-muc-srv1,"
                        #               "demo-geomap,demo-automap"),
                        #      'interval': 15,
                        #  },
                    },
                    'actions': {
                        # 'rdp': {
                        #     'action_type': "rdp",
                        #     'obj_type': "host,service",
                        #     'condition': "TAGS~win",
                        #     'client_os': "win",
                        #     'domain': "",
                        #     'username': "",
                        # },
                    },
                },
                'templates': {},
                })
        data['nginx']['nagvis']['fastcgi_pass'] = (
            "unix:/var/spool/www/{0}.fpm.sock".format(
                data['nginx']['domain'].replace('.', '_')
            )
        )

        __salt__['mc_macros.update_local_registry'](
            'nagvis', nagvis_reg,
            registry_format='pack')
        return data
    return _settings()


def add_map_settings(name, _global, objects, keys_mapping, **kwargs):
    '''Settings for the add_map macro'''
    nagvisSettings = copy.deepcopy(__salt__['mc_nagvis.settings']())
    extra = kwargs.pop('extra', {})
    kwargs.update(extra)
    kwargs.setdefault('name', name)
    kwargs.setdefault('_global', _global)
    kwargs.setdefault('objects', objects)
    kwargs.setdefault('keys_mapping', keys_mapping)
    nagvisSettings = __salt__['mc_utils.dictupdate'](nagvisSettings, kwargs)
    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
    # nagvisSettings['data'] = copy.deepcopy(nagvisSettings)
    # nagvisSettings['data']['extra'] = copy.deepcopy(nagvisSettings)
    # nagvisSettings['extra'] = copy.deepcopy(nagvisSettings)
    return nagvisSettings


def add_geomap_settings(name, hosts, **kwargs):
    '''Settings for the add_geomap macro'''
    nagvisSettings = copy.deepcopy(__salt__['mc_nagvis.settings']())
    extra = kwargs.pop('extra', {})
    kwargs.update(extra)
    kwargs.setdefault('name', name)
    kwargs.setdefault('hosts', hosts)
    nagvisSettings = __salt__['mc_utils.dictupdate'](nagvisSettings, kwargs)
    # retro compat // USE DEEPCOPY FOR LATER RECURSIVITY !
    # nagvisSettings['data'] = copy.deepcopy(nagvisSettings)
    # nagvisSettings['data']['extra'] = copy.deepcopy(nagvisSettings)
    # nagvisSettings['extra'] = copy.deepcopy(nagvisSettings)
    return nagvisSettings



#
