# -*- coding: utf-8 -*-
'''
.. _module_mc_pnp4nagios:

mc_pnp4nagios / pnp4nagios functions
============================================

There are many way to configure pnp4nagios.
I have chosen to configure pnp4nagios "Bulk Mode with NPCD and npcdmod" 
(http://docs.pnp4nagios.org/pnp-0.6/config#bulk_mode_with_npcd_and_npcdmod)
because of the lightness of the configuration


'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import copy
import mc_states.utils

import hmac
import hashlib

__name = 'pnp4nagios'

log = logging.getLogger(__name__)


def settings():
    '''
    pnp4nagios settings

    location
        installation directory

    package
        list of packages to install icinga-web
    configuration_directory
        directory where configuration files are located

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

            pnp4nagios
                dictionary to store values used in templates given in
                vh_content_source and vh_top_source

                web_directory
                    location under which webpages of pnp4nagios will be available
                fastcgi_pass
                    socket used to contact fastcgi server in order to interpret php files
                realm
                    message displayed for digest authentication
                htpasswd_file
                    location of file storing users password
                htdoc_dir
                    root location for web_directory


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
            extensions_package
                additional packages to install (such as php5-pgsql or php5-mysql for
                php database connection)
            doc_root
                root location for php-fpm
            session_auto_start
                must be 0 to run icinga-web

        icinga_cfg
            location
                location of icinga.cfg file
            marker_start
                the beginning of the zone which will be replace.
                this zone contains the "process_performance_data" and "broker_module" directives
            marked_end
                the end of the zone which will be replace.
            content
                the replacment content

        npcd_cfg
            dictionary to store configuration of npcd.cfg file
        config_php
            dictionary to store configuration of config.php file

            conf
                subdictionary to store the values of the $conf[] php array variable
            views
                subdictionary to store the values of the $views[] php array variable

                each subdictionary under views corresponds to a subarray. The key of subdictionaries are
                the values for "title" array key
        rra_cfg
            dictionary to store the configuration of rra.cfg file

            RRA_STEP
                value for RRA_STEP
            steps
                list of strings where each string is a line in rra.cfg file

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locs = __salt__['mc_locations.settings']()

        pnp4nagios_reg = __salt__[
            'mc_macros.get_local_registry'](
                'pnp4nagios', registry_format='pack')

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.pnp4nagios', {
                'package': ['pnp4nagios-bin', 'pnp4nagios-web'],
                'configuration_directory': locs['conf_dir']+"/pnp4nagios",
                'nginx': {
                    'domain': "pnp4nagios.localhost",
                    'doc_root': "/usr/share/pnp4nagios/html/",
                    'vh_content_source': "salt://makina-states/files/etc/nginx/sites-available/pnp4nagios.content.conf",
                    'vh_top_source': "salt://makina-states/files/etc/nginx/sites-available/pnp4nagios.top.conf",
                    'pnp4nagios': {
                        'web_directory': "/pnp4nagios",
                        'fastcgi_pass': "unix:/var/spool/www/pnp4nagios_localhost.fpm.sock",
                        'realm': "Authentication",
                        'htpasswd_file': "/etc/icinga/htpasswd.users",
                        'htdocs_dir': "/usr/share/icinga/htdocs/",
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
                    'open_basedir': "/usr/bin/rrdtool:/etc/pnp4nagios/:/usr/share/php/kohana2/system/:/usr/share/php/kohana2/system/config/:/var/lib/pnp4nagios/perfdata/",
                    'doc_root': '/usr/share/pnp4nagios/',
                    #'session_save_path': '/var/lib/php5',
                    'session_auto_start': 0,
                    'extensions_packages': ['php-gettext', 'php-net-socket', 'php-pear', 'php5-sqlite'],
                },
                'icinga_cfg': {
                    'location': "/etc/icinga/icinga.cfg",
                    'marker_start': "# START managed zone pnp4nagios",
                    'marker_end': "# END managed zone pnp4nagios",
                    'content': [
                                   "process_performance_data=1",
                                   "broker_module=/usr/lib/pnp4nagios/npcdmod.o config_file=/etc/pnp4nagios/npcd.cfg",
                               ],
                },
                'npcd_cfg': {
                    'user': "nagios",
                    'group': "nagios",
                    'log_type': "syslog",
                    'log_file': "/var/log/pnp4nagios/npcd.log",
                    'max_logfile_size': 10485760,
                    'log_level': 2,
                    'perfdata_spool_dir': "/var/lib/icinga/spool/",
                    'perfdata_file_run_cmd': "/usr/lib/pnp4nagios/libexec/process_perfdata.pl",
                    'perfdata_file_run_cmd_args': "-b",
                    'identify_npcd': 1,
                    'npcd_max_threads': 5,
                    'sleep_time': 15,
                    'load_threshold': 0.0,
                    'pid_file': "/var/run/npcd.pid",
                    'perfdata_file': "/var/lib/icinga/perfdata.dump",
                    'perfdata_spool_filename': "perfdata",
                    'perfdata_file_processing_interval': 15,
                },
                'config_php': {
                    'conf': {
                        'use_url_rewriting': 1,
                        'rrdtool': "/usr/bin/rrdtool",
                        'graph_width': 500,
                        'graph_height': 100,
                        'zgraph_width': 500,
                        'zgraph_height': 100,
                        'right_zoom_offset': 30,
                        'pdf_width': 675,
                        'pdf_height': 100,
                        'pdf_page_size': "A4",
                        'pdf_margin_top': 30,
                        'pdf_margin_left': 17.5,
                        'pdf_margin_right': 10,
                        'graph_opt': "", 
                        'pdf_graph_opt': "", 
                        'rrdbase': "/var/lib/pnp4nagios/perfdata/",
                        'page_dir': "/etc/pnp4nagios/pages/",
                        'refresh': 90,
                        'max_age': "60*60*6",   
                        'temp': "/var/tmp",
                        'nagios_base': "/cgi-bin/icinga",
                        'multisite_base_url': "/check_mk",
                        'multisite_site': "",
                        'auth_enabled': "FALSE",
                        'livestatus_socket': "unix:/var/lib/icinga/rw/live",
                        'allowed_for_all_services': "",
                        'allowed_for_all_hosts': "",
                        'allowed_for_service_links': "EVERYONE",
                        'allowed_for_host_search': "EVERYONE",
                        'allowed_for_host_overview': "EVERYONE",
                        'allowed_for_pages': "EVERYONE",
                        'overview_range': 1 ,
                        'popup_width': "300px",
                        'ui_theme': 'smoothness',
                        'lang': "en_US",
                        'date_fmt': "d.m.y G:i",
                        'enable_recursive_template_search': 1,
                        'show_xml_icon': 1,
                        'use_fpdf': 1,	
                        'background_pdf': "/etc/pnp4nagios/background.pdf",
                        'use_calendar': 1,
                        'RRD_DAEMON_OPTS': "",
                        'template_dirs': ["/etc/pnp4nagios/templates", "/usr/share/pnp4nagios/html/templates.dist"],
                        'special_template_dir': "/etc/pnp4nagios/templates.special",
                        'mobile_device': "iPhone|iPod|iPad|android",
                    },
                    'views': {
                        '4 Hours': {
                            'start': "(60*60*4)",
                        },
                        '25 Hours': {
                            'start': "(60*60*25)",
                        },
                        'One Week': {
                            'start': "(60*60*25*7)",
                        },
                        'One Month': {
                            'start': "(60*60*24*32)",
                        },
                        'One Year': {
                            'start': "(60*60*24*380)",
                        },
                    },
                },
                'rra_cfg': {
                    'RRA_STEP': 60,
                    'steps': [
                        "RRA:AVERAGE:0.5:1:2880",
                        "RRA:AVERAGE:0.5:5:2880",
                        "RRA:AVERAGE:0.5:30:4320",
                        "RRA:AVERAGE:0.5:360:5840",
                        "RRA:MAX:0.5:1:2880",
                        "RRA:MAX:0.5:5:2880",
                        "RRA:MAX:0.5:30:4320",
                        "RRA:MAX:0.5:360:5840",
                        "RRA:MIN:0.5:1:2880",
                        "RRA:MIN:0.5:5:2880",
                        "RRA:MIN:0.5:30:4320",
                        "RRA:MIN:0.5:360:5840",
                    ],
                },
        })

        __salt__['mc_macros.update_local_registry'](
            'pnp4nagios', pnp4nagios_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
