# -*- coding: utf-8 -*-
'''
.. _module_mc_nagvis:

mc_nagvis / nagvis functions
============================================

'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
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
                
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locs = __salt__['mc_locations.settings']()

        nagvis_reg = __salt__[
            'mc_macros.get_local_registry'](
                'nagvis', registry_format='pack')

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.nagvis', {
                'package': ['nagvis'],
                'configuration_directory': locs['conf_dir']+"/nagvis",
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
                    'open_basedir': "/usr/share/php/php-gettext/:/etc/nagvis/:/var/lib/nagvis/:/var/cache/nagvis/",
                    'doc_root': '/usr/share/nagvis/',
                    #'session_save_path': '/var/lib/php5',
                    'session_auto_start': 0,
                },
                'nagvis_ini_php': {
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
                    'http_proxy': "",
                    'http_proxy_auth': "",
                    'http_timeout': 10,
                    'language_available': "de_DE,en_US,es_ES,fr_FR,pt_BR",
                    'language_detection': "user,session,browser,config",
                    'language': "en_US",
                    'logon_multisite_htpasswd': "/path/to/htpasswd",
                    'logon_multisite_serials': "/path/to/auth.serials",
                    'logon_multisite_secret': "/path/to/auth.secret",
                    'logon_multisite_createuser': 1,
                    'logon_multisite_createrole': "Guests",
                    'logonmodule': "LogonMixed",
                    'logonenvvar': "REMOTE_USER",
                    'logonenvcreateuser': "1",
                    'logonenvcreaterole': "Guests",
                    'refreshtime': 60,
                    'sesscookiedomain': "auto-detect",
                    'sesscookiepath': "/nagvis",
                    'sesscookieduration': 86400,
                    'startmodule': "Overview",
                    'startaction': "view",
                    'startshow': "",
                    'shinken_features': 0,
                    'base': "/usr/share/nagvis/",
                    'htmlbase': "/nagvis",
                    'htmlcgi': "/cgi-bin/icinga",
                    'backend': "live_1",
                    'backgroundcolor': "#ffffff",
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
                    'eventlogheight': 75,
                    'eventloghidden': 1,
                    'eventscroll': 1,
                    'eventsound': 1,
                    'headermenu': 1,
                    'headertemplate': "default",
                    'headerfade': 1,
                    'hovermenu': 1,
                    'hovertemplate': "default",
                    'hoverdelay': 0,
                    'hoverchildsshow': 1,
                    'hoverchildslimit': 10,
                    'hoverchildsorder': "asc",
                    'hoverchildssort': "s",
                    'icons': "std_medium",
                    'onlyhardstates': 0,
                    'recognizeservices': 1,
                    'showinlists': 1,
                    'showinmultisite': 1,
                    'stylesheet': "",
                    'urltarget': "_self",
                    'hosturl=[htmlcgi]/status.cgi?host': "[host_name]",
                    'hostgroupurl=[htmlcgi]/status.cgi?hostgroup': "[hostgroup_name]",
                    'serviceurl=[htmlcgi]/extinfo.cgi?type=2&host=[host_name]&service': "[service_description]",
                    'servicegroupurl=[htmlcgi]/status.cgi?servicegroup=[servicegroup_name]&style': "detail",
                    'mapurl=[htmlbase]/index.php?mod=Map&act=view&show': "[map_name]",
                    'view_template': "default",
                    'label_show': 0,
                    'line_weather_colors': "10:#8c00ff,25:#2020ff,40:#00c0ff,55:#00f000,70:#f0f000,85:#ffc000,100:#ff0000",
                    'backgroundcolor': "#ffffff",
                    'cellsperrow': 4,
                    'headermenu': 1,
                    'headertemplate': "default",
                    'showmaps': 1,
                    'showgeomap': 0,
                    'showrotations': 1,
                    'showmapthumbs': 0,
                    'defaultparams=&childLayers': "2",
                    'defaultroot': "<<<monitoring>>>",
                    'graphvizpath': "/usr/bin/",
                    'maplocktime': 5,
                    'grid_show': 0,
                    'grid_color': "#D5DCEF",
                    'grid_steps': 32,
                    'interval': 10,
                    'requestmaxparams': 0,
                    'requestmaxlength': 1900,
                    'updateobjectstates': 30,
                    'backends': {}
                    'maps': "demo-germany,demo-ham-racks,demo-load,demo-muc-srv1,demo-geomap,demo-automap",
                    'interval': 15,
                    'action_type': "rdp",
                    'obj_type': "host,service",
                    'condition': "TAGS~win",
                    'client_os': "win",
                    'domain': "",
                    'username': "",
                    'action_type': "win_ssh",
                    'obj_type': "host,service",
                    'client_os': "win",
                    'condition': "TAGS~unix",
                    'action_type': "ssh_url",
                    'obj_type': "host,service",
                    'client_os': "mac,lnx",
                    'condition': "TAGS~unix",
                    'action_type': "http",
                    'obj_type': "host,service",
                    'condition': "TAGS~web-80",
                    'action_type': "https",
                    'obj_type': "host,service",
                    'condition': "TAGS~web-443",
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
                    'unreachable_ack_bgcolor': "",
                    'unreachable_downtime_bgcolor': "",
                    'down_bgcolor': "#FF0000",
                    'down_color': "#FF0000",
                    'down_ack_bgcolor': "",
                    'down_downtime_bgcolor': "",
                    'critical_bgcolor': "#FF0000",
                    'critical_color': "#FF0000",
                    'critical_ack_bgcolor': "",
                    'critical_downtime_bgcolor': "",
                    'warning_bgcolor': "#FFFF00",
                    'warning_color': "#FFFF00",
                    'warning_ack_bgcolor': "",
                    'warning_downtime_bgcolor': "",
                    'unknown_bgcolor': "#FFCC66",
                    'unknown_color': "#FFCC66",
                    'unknown_ack_bgcolor': "",
                    'unknown_downtime_bgcolor': "",
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
                    'unknown_sound': "",
                    'error_sound': "",
                    'up_sound': "",
                    'ok_sound': "",
                    'unchecked_sound': "",
                    'pending_sound': "",
                },
        })

        __salt__['mc_macros.update_local_registry'](
            'nagvis', nagvis_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
