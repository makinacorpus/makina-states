# -*- coding: utf-8 -*-
'''
.. _module_mc_nagvis:

mc_nagvis / nagvis functions
============================================

You can add your own key/values in backends, rotations and actions subdictionaries.

'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import copy
import mc_states.utils

import hmac
import hashlib

__name = 'nagvis'

log = logging.getLogger(__name__)


def settings():
    '''
    nagvis settings

    location
        installation directory

    package
        list of packages to install icinga-web
    configuration_directory
        directory where configuration files are located

    root_account
        dictionary to store root account information. It is the account with the userId=1 in the sqlite database

        login
            login for root login on web interface
        hashed_password
            password for root login on web interface
        salt
            salt used to hash the password
        default_password
            the password inserted when nagvis is installed. it is to check that the password was not previously modified

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
                    socket used to contact fastcgi server in order to interpret php files

            icinga_cgi
                dictionary to store values used in templates given in
                vh_content_source and vh_top_source

                enabled
                    enable a web directory to serve cgi files. If True, icinga-cgi
                    will no be installed and configured automatically.

                web_directory
                    location under which webpages of icinga-cgi will be available
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
            doc_root
                root location for php-fpm
            session_auto_start
                must be 0 to run nagvis

        global_php
            dictionary to store values used in global.php

            CONST_VERSION
                str
            PROFILE
                "true" or "false"
            DEBUG
                "true" or "false"
            DEBUGLEVEL
                number
            DEBUGFILE
                location of file
            CONST_MAINCFG
                location of nagvis.ini.php
            CONST_MAINCFG_CACHE
                location of cache directory
            CONST_MAINCFG_DIR
                location of configuration directory
            HTDOCS_DIR
                location of webserver root
                I have not modified this value because it seems it doesn't work when we use a subdirectory
            CONST_NEEDED_PHP_VERSION
                str
            SESSION_NAME
                name of cookie session
            REQUIRES_AUTHORISATION
                "true" or "false"
            GET_STATE
                "true" or "false"
            GET_PHYSICAL_PATH
                "true" or "false"
            DONT_GET_OBJECT_STATE
                "true" or "false"
            DONT_GET_SINGLE_MEMBER_STATES
                "true" or "false"
            GET_SINGLE_MEMBER_STATES
                "true" or "false"
            HANDLE_USERCFG
                "true" or "false"
            ONLY_USERCFG
                "true" or "false"
            ONLY_STATE
                "true" or "false"
            COMPLETE
                "true" or "false"
            IS_VIEW
                "true" or "false"
            ONLY_GLOBAL
                "true" or "false"
            GET_CHILDS
                "true" or "false"
            SUMMARY_STATE
                "true" or "false"
            COUNT_QUERY
                "true" or "false"
            MEMBER_QUERY
                "true" or "false"
            HOST_QUERY
                "true" or "false"
            AUTH_MAX_PASSWORD_LENGTH
                number
            AUTH_MAX_USERNAME_LENGTH
                number
            AUTH_MAX_ROLENAME_LENGTH
                number
            AUTH_PERMISSION_WILDCARD
                str
            AUTH_TRUST_USERNAME
                "true" or "false"
            AUTH_NOT_TRUST_USERNAME
                "true" or "false"
            AUTH_PASSWORD_SALT
                salt used for password. We notice the salt used is the same for all passwords which is a security weakness.

        nagvis_ini_php
            dictionary to store values used in nagvis_ini_php
            each subdictionary represents an ini section
            if a key is not present, the directive will not be added in the configuration file

            global
                dictionary to store values of global section in nagvis_ini_php

                audit_log
                    1 or 0
                authmodule
                    name of authentication module
                authorisationmodule
                    name of authorisation module
                controls_size
                    controls size
                dateformat
                    date format
                dialog_ack_sticky
                    .
                dialog_ack_notify
                    .
                dialog_ack_persist
                    .
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
                http_timeout
                    timeout
                language_available
                    language available
                language_detection
                    language detection
                language
                    default language
                logonmodule
                    for old style authentication
                logonenvvar
                    header containing username
                logonenvcreateuser
                    1 or 0
                logonenvcreaterole
                    .
                logon_multisite_htpasswd
                    location of htpasswd file used by logon multisite
                logon_multisite_secret
                    .
                logon_multisite_createuser
                    1 or 0
                logon_multisite_createrole
                    .
                refreshtime
                    automatically refresh
                sesscookiedomain
                    session cookie domain
                sesscookiepath
                    session cookie path
                sesscookieduration
                    session cookie lifetime
                startmodule
                    .
                startaction
                    .
                startshow
                    .
                shinken_features
                    1 or 0

            paths
                dictionary to store values of paths section in nagvis_ini_php

                base
                    location of nagvis installation
                htmlbase
                    location of php files. It should be the same value that nginx.nagvis.web_directory
            defaults
                dictionary to store values of defaults section in nagvis_ini_php

                backend
                    default backend
                backgroundcolor
                    background color
                contextmenu
                    1 or 0
                contexttemplate
                    template
                event_on_load
                    1 or 0
                event_repeat_interval
                    1 or 0
                event_repeat_duration
                    number
                eventbackground
                    1 or 0
                eventhighlight
                    1 or 0
                eventhighlightduration
                    number
                eventhighlightinterval
                    number
                eventlog
                    1 or 0
                eventloglevel
                    number
                eventlogevents
                    number
                eventlogheight
                    number
                eventloghidden
                    1 or 0
                eventscroll
                    1 or 0
                eventsound
                    1 or 0
                headermenu
                    1 or 0
                headertemplate
                    name of header template
                headerfade
                    1 or 0
                hovermenu
                    1 or 0
                hovertemplate
                    name of hover template
                hoverdelay
                    number
                hoverchildsshow
                    1 or 0
                hoverchildslimit
                    number
                hoverchildsorder
                    "asc" or "desc"
                hoverchildssort
                    "s"
                icons
                    name of icons
                onlyhardstates
                    1 or 0
                recognizeservices
                    1 or 0
                showinlists
                    1 or 0
                showinmultisite
                    1 or 0
                stylesheet
                    ""
                urltarget
                    "_self"
                hosturl
                    url for hosts
                hostgroupurl
                    url for hostgroups
                serviceurl
                    url for services
                servicegroupurl
                    url for servicegroups
                mapurl
                    url of maps
                view_template
                    name of the view template
                label_show
                    1 or 0
                line_weather_colors
                    .

            index
                dictionary to store values of index section in nagvis_ini_php

                backgroundcolor
                    background color
                cellsperrow
                    number
                headermenu
                    1 or 0
                headertemplate
                    header template
                showmaps
                    1 or 0
                showgeomap
                    1 or 0
                showrotations
                    1 or 0
                showmapthumbs
                    1 or 0

            automap
                dictionary to store values of automap section in nagvis_ini_php

                defaultparams
                    default parameters
                defaultroot
                    default root
                graphvizpath
                    location of graphviz binary

            wui
                dictionary to store values of wui section in nagvis_ini_php

                maplocktime
                    map lock time
                grid_show
                    1 or 0
                grid_color
                    grid color
                grid_steps
                    scale of the grid

            worker
                dictionary to store values of worker section in nagvis_ini_php

                interval
                    number
                requestmaxparams
                    number
                requestmaxlength
                    number
                updateobjectstates
                    number

            backends
                dictionary to store values of backends section in nagvis_ini_php
                each subdictionary corresponds to a "backend_foo" section

                foo
                    dictionary to store values of foo backend. foo must be replaced with the name of the backend
                    the keys and values expected depends on the backend type

                    backendtype
                        type of backend

            rotations
                dictionary to store values of rotations section in nagvis_ini_php
                each subdictionary corresponds to a "rotation_foo" section

                foo
                    dictionary to store values of foo rotation. foo must be replaced with the name of the rotation

                    maps
                        list of maps which are in the rotation
                    interval
                        interval

            actions
                dictionary to store values of actions section in nagvis_ini_php
                each subdictionary corresponds to a "action_foo" section

                foo
                    dictionary to store values of foo action. foo must be replaced with the name of the action

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

            states
                dictionary to store values of states section in nagvis_ini_php

                down
                    .
                down_ack
                    .
                down_downtime
                    .
                unreachable
                    .
                unreachable_ack
                    .
                unreachable_downtime
                    .
                critical
                    .
                critical_ack
                    .
                critical_downtime
                    .
                warning
                    .
                warning_ack
                    .
                warning_downtime
                    .
                unknown
                    .
                unknown_ack
                    .
                unknown_downtime
                    .
                error
                    .
                error_ack
                    .
                error_downtime
                    .
                up
                    .
                ok
                    .
                unchecked
                    .
                pending
                    .

                unreachable_bgcolor
                    .
                unreachable_color
                    .
                unreachable_ack_bgcolor
                    .
                unreachable_downtime_bgcolor
                    .
                down_bgcolor
                    .
                down_color
                    .
                down_ack_bgcolor
                    .
                down_downtime_bgcolor
                    .
                critical_bgcolor
                    .
                critical_color
                    .
                critical_ack_bgcolor
                    .
                critical_downtime_bgcolor
                    .
                warning_bgcolor
                    .
                warning_color
                    .
                warning_ack_bgcolor
                    .
                warning_downtime_bgcolor
                    .
                unknown_bgcolor
                    .
                unknown_color
                    .
                unknown_ack_bgcolor
                    .
                unknown_downtime_bgcolor
                    .
                error_bgcolor
                    .
                error_color
                    .
                up_bgcolor
                    .
                up_color
                    .
                ok_bgcolor
                    .
                ok_color
                    .
                unchecked_bgcolor
                    .
                unchecked_color
                    .
                pending_bgcolor
                    .
                pending_color
                    .
                unreachable_sound
                    .
                down_sound
                    .
                critical_sound
                    .
                warning_sound
                    .
                unknown_sound
                    .
                error_sound
                    .
                up_sound
                    .
                ok_sound
                    .
                unchecked_sound
                    .
                pending_sound
                    .

                
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locs = __salt__['mc_locations.settings']()

        nagvis_reg = __salt__[
            'mc_macros.get_local_registry'](
                'nagvis', registry_format='pack')

        password_web_root_account = nagvis_reg.setdefault('web.root_account_password', __salt__['mc_utils.generate_password']())

        root_account = {
            'password': password_web_root_account,
            'salt': "29d58ead6a65f5c00342ae03cdc6d26565e20954", # if you change this, you must change it in php
        }

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.nagvis', {
                'package': ['nagvis'],
                'configuration_directory': locs['conf_dir']+"/nagvis",
                'root_account': { # we considere that the root_account has the ID 1
                    'user': "admin",
                    'hashed_password': hashlib.sha1(root_account['salt']+root_account['password']).hexdigest(),
                    'salt': root_account['salt'],
                    'default_password': "868103841a2244768b2dbead5dbea2b533940e20", # default value that we find if before nagvis
                    # configuration. It is the password set during installation
                },
                'nginx': {
                    'domain': "nagvis.localhost",
                    'doc_root': "/usr/share/nagvis/www/",
                    'vh_content_source': "salt://makina-states/files/etc/nginx/sites-available/nagvis.content.conf",
                    'vh_top_source': "salt://makina-states/files/etc/nginx/sites-available/nagvis.top.conf",
                    'nagvis': {
                        'web_directory': "/nagvis",
                        'fastcgi_pass': "unix:/var/spool/www/nagvis_localhost.fpm.sock",
                    },
                    'icinga_cgi': {
                        'enabled': True, # icinga cgi will not be configured. It is done in services.monitoring.icinga
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
                    'open_basedir': "/var/lib/icinga/rw/:/usr/share/php/php-gettext/:/etc/nagvis/:/var/lib/nagvis/:/var/cache/nagvis/",
                    'doc_root': '/usr/share/nagvis/',
                    #'session_save_path': '/var/lib/php5',
                    'session_auto_start': 0,
                    'extensions_packages': ['php-gettext', 'php-net-socket', 'php-pear', 'php5-sqlite'],
                },
                'global_php': {
                    'CONST_VERSION': "1.7.10",
                    'PROFILE': "false",
                    'DEBUG': "false",
                    'DEBUGLEVEL': 6,
                    'DEBUGFILE': "../../../var/nagvis-debug.log",
                    'CONST_MAINCFG': "/etc/nagvis/nagvis.ini.php",
                    'CONST_MAINCFG_CACHE': "/var/cache/nagvis/nagvis-conf",
                    'CONST_MAINCFG_DIR': "/etc/nagvis/conf.d",
                    'HTDOCS_DIR': "share",
                    'CONST_NEEDED_PHP_VERSION': "5.0",
                    'SESSION_NAME': "nagvis_session",
                    'REQUIRES_AUTHORISATION': "true",
                    'GET_STATE': "true",
                    'GET_PHYSICAL_PATH': "false",
                    'DONT_GET_OBJECT_STATE': "false",
                    'DONT_GET_SINGLE_MEMBER_STATES': "false",
                    'GET_SINGLE_MEMBER_STATES': "true",
                    'HANDLE_USERCFG': "true",
                    'ONLY_USERCFG': "true",
                    'ONLY_STATE': "true",
                    'COMPLETE': "false",
                    'IS_VIEW': "true",
                    'ONLY_GLOBAL': "true",
                    'GET_CHILDS': "true",
                    'SET_KEYS': "true",
                    'SUMMARY_STATE': "true",
                    'COUNT_QUERY': "true",
                    'MEMBER_QUERY': "true",
                    'HOST_QUERY': "true",
                    'AUTH_MAX_PASSWORD_LENGTH': 30,
                    'AUTH_MAX_USERNAME_LENGTH': 30,
                    'AUTH_MAX_ROLENAME_LENGTH': 30,
                    'AUTH_PERMISSION_WILDCARD': "*",
                    'AUTH_TRUST_USERNAME': "true",
                    'AUTH_NOT_TRUST_USERNAME': "false",
                    'AUTH_PASSWORD_SALT': root_account['salt'],
                },
                'nagvis_ini_php': {
                    'global': {
                        'audit_log': 1,
                        'authmodule': "CoreAuthModSQLite",
                        'authorisationmodule': "CoreAuthorisationModSQLite",
                        'controls_size': 10,
                        'dateformat': "Y-m-d H:i:s",
                        'dialog_ack_sticky': 1,
                        'dialog_ack_notify': 1,
                        'dialog_ack_persist': 0,
                        'file_group': "www-data",
                        'file_mode': 660,
                        'geomap_server': "http://geomap.nagvis.org/",
                        # 'http_proxy': "",
                        # 'http_proxy_auth': "",
                        'http_timeout': 10,
                        'language_available': "de_DE,en_US,es_ES,fr_FR,pt_BR",
                        'language_detection': "user,session,browser,config",
                        'language': "en_US",
                        'logonmodule': "LogonMixed",
                        'logonenvvar': "REMOTE_USER",
                        'logonenvcreateuser': 1,
                        'logonenvcreaterole': "Guests",
                        'logon_multisite_htpasswd': "",
                        'logon_multisite_secret': "",
                        'logon_multisite_createuser': 1,
                        'logon_multisite_createrole': "Guest",
                        'refreshtime': 60,
                        'sesscookiedomain': "auto-detect",
                        'sesscookiepath': "auto-detect",
                        'sesscookieduration': 86400,
                        'startmodule': "Overview",
                        'startaction': "view",
                        'startshow': "",
                        'shinken_features': 0,
                    },
                    'paths': {
                        'base': "/usr/share/nagvis/",
                        'htmlbase': "/nagvis",
                        'htmlcgi': "/cgi-bin/icinga",
                    },
                    'defaults': {
                        'backend': "live_1",
                        'backgroundcolor': "transparent",
                        'contextmenu': 1,
                        'contexttemplate': "default",
                        'event_on_load': 0,
                        'event_repeat_interval': 0,
                        'event_repeat_duration': -1,
                        'eventbackground': 0,
                        'eventhighlight': 1,
                        'eventhighlightduration': 10000,
                        'eventhighlightinterval': 500,
                        'eventlog': 0,
                        'eventloglevel': "info",
                        'eventlogevents': 24,
                        'eventlogheight': 100,
                        'eventloghidden': 1,
                        'eventscroll': 1,
                        'eventsound': 1,
                        'headermenu': 1,
                        'headertemplate': "default",
                        'headerfade': 0,
                        'hovermenu': 1,
                        'hovertemplate': "default",
                        'hoverdelay': 0,
                        'hoverchildsshow': 1,
                        'hoverchildslimit': 10,
                        'hoverchildsorder': "asc",
                        'hoverchildssort': "a",
                        'icons': "std_medium",
                        'onlyhardstates': 0,
                        'recognizeservices': 1,
                        'showinlists': 1,
                        'showinmultisite': 1,
#                        'stylesheet': "",
                        'urltarget': "_self",
                        'hosturl': "[htmlcgi]/status.cgi?host=[host_name]",
                        'hostgroupurl': "[htmlcgi]/status.cgi?hostgroup=[hostgroup_name]",
                        'serviceurl': "[htmlcgi]/extinfo.cgi?type=2&host=[host_name]&service=[service_description]",
                        'servicegroupurl': "[htmlcgi]/status.cgi?servicegroup=[servicegroup_name]&style=detail",
                        'mapurl': "[htmlbase]/index.php?mod=Map&act=view&show=[map_name]",
                        'view_template': "default",
                        'label_show': 0,
                        'line_weather_colors': "10:#8c00ff,25:#2020ff,40:#00c0ff,55:#00f000,70:#f0f000,85:#ffc000,100:#ff0000",
                    },
                    'index': {
                        'backgroundcolor': "#ffffff",
                        'cellsperrow': 4,
                        'headermenu': 1,
                        'headertemplate': "default",
                        'showmaps': 1,
                        'showgeomap': 0,
                        'showrotations': 1,
                        'showmapthumbs': 0,
                    },
                    'automap': {
                        'defaultparams': "&childLayers=2",
                        'defaultroot': "/",
                        'graphvizpath': "/usr/bin/",
                    },
                    'wui': {
                        'maplocktime': 5,
                        'grid_show': 0,
#                        'grid_color': "#D5DCEF",
                        'grid_color': "#F7F7F7",
                        'grid_steps': 32,
                    },
                    'worker': {
                        'interval': 5,
                        'requestmaxparams': 0,
                        'requestmaxlength': 1900,
                        'updateobjectstates': 15,
                    },
                    'backends': {
                        'live_1': {
                            'backendtype': "mklivestatus",
                            'socket': "unix:/var/lib/icinga/rw/live",
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
                    'states': {
                        'down': 10,
                        'down_ack': 6,
                        'down_downtime': 6,
                        'unreachable': 9,
                        'unreachable_ack': 6,
                        'unreachable_downtime': 6,
                        'critical': 8,
                        'critical_ack': 6,
                        'critical_downtime': 6,
                        'warning': 7,
                        'warning_ack': 5,
                        'warning_downtime': 5,
                        'unknown': 4,
                        'unknown_ack': 3,
                        'unknown_downtime': 3,
                        'error': 4,
                        'error_ack': 3,
                        'error_downtime': 3,
                        'up': 2,
                        'ok': 1,
                        'unchecked': 0,
                        'pending': 0,
                        'unreachable_bgcolor': "#F1811B",
                        'unreachable_color': "#F1811B",
                        # 'unreachable_ack_bgcolor': "",
                        # 'unreachable_downtime_bgcolor': "",
                        'down_bgcolor': "#FF0000",
                        'down_color': "#FF0000",
                        # 'down_ack_bgcolor': "",
                        # 'down_downtime_bgcolor': "",
                        'critical_bgcolor': "#FF0000",
                        'critical_color': "#FF0000",
                        'critical_ack_bgcolor': "",
                        'critical_downtime_bgcolor': "",
                        'warning_bgcolor': "#FFFF00",
                        'warning_color': "#FFFF00",
                        # 'warning_ack_bgcolor': "",
                        # 'warning_downtime_bgcolor': "",
                        'unknown_bgcolor': "#FFCC66",
                        'unknown_color': "#FFCC66",
                        # 'unknown_ack_bgcolor': "",
                        # 'unknown_downtime_bgcolor': "",
                        'error_bgcolor': "#0000FF",
                        'error_color': "#0000FF",
                        'up_bgcolor': "#00FF00",
                        'up_color': "#00FF00",
                        'ok_bgcolor': "#00FF00",
                        'ok_color': "#00FF00",
                        'unchecked_bgcolor': "#C0C0C0",
                        'unchecked_color': "#C0C0C0",
                        'pending_bgcolor': "#C0C0C0",
                        'pending_color': "#C0C0C0",
                        'unreachable_sound': "std_unreachable.mp3",
                        'down_sound': "std_down.mp3",
                        'critical_sound': "std_critical.mp3",
                        'warning_sound': "std_warning.mp3",
                        # 'unknown_sound': "",
                        # 'error_sound': "",
                        # 'up_sound': "",
                        # 'ok_sound': "",
                        # 'unchecked_sound': "",
                        # 'pending_sound': "",
                    },
                },
        })

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
    nagvisSettings['data'] = copy.deepcopy(nagvisSettings)
    nagvisSettings['data']['extra'] = copy.deepcopy(nagvisSettings)
    nagvisSettings['extra'] = copy.deepcopy(nagvisSettings)
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
    nagvisSettings['data'] = copy.deepcopy(nagvisSettings)
    nagvisSettings['data']['extra'] = copy.deepcopy(nagvisSettings)
    nagvisSettings['extra'] = copy.deepcopy(nagvisSettings)
    return nagvisSettings



def dump():
    return mc_states.utils.dump(__salt__,__name)

#
