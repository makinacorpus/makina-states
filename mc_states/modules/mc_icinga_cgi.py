# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga_cgi:

mc_icinga_cgi / icinga_cgi functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

import hmac
import hashlib

__name = 'icinga_cgi'

log = logging.getLogger(__name__)


def settings():
    '''
    icinga_cgi settings

    location
        installation directory

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        icinga_cgi_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga_cgi', registry_format='pack')
        locs = __salt__['mc_locations.settings']()

        user = "www-data"
        group = "www-data"

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga_cgi', {
                'package': ['icinga-cgi'],
                'configuration_directory': locs['conf_dir']+"/icinga",
                'user': user,
                'group': group,
                'nginx': {
                    'virtualhost': "icinga-cgi.localhost",
                    'doc_root': "/usr/share/icinga-web/pub/",
                    'vh_content_source': "salt://makina-states/files/etc/icinga-cgi/nginx.conf",
                    'vh_top_source': "salt://makina-states/files/etc/icinga-cgi/nginx.top.conf",
                },
                'uwsgi': {
                    'name': "icinga",
                    'config_file': "salt://makina-states/files/etc/icinga-cgi/uwsgi.ini",
                    'enabled': True,
                    'config_data': {
                        'master': "true",
                        'plugins': "cgi",
                        'async': 20,
                        'socket': "127.0.0.1:3030",
                        'uid': user,
                        'gid': group,
                        'cgi': "/cgi-bin/icinga/=/usr/lib/cgi-bin/icinga/",
                        'cgi_allowed_ext': ".cgi",
                    },
                },
                'cgi_cfg': {
                    'main_config_file': "/etc/icinga/icinga.cfg",
                    'standalone_installation': 0,
                    'physical_html_path': "/usr/share/icinga/htdocs",
                    'url_html_path': "/icinga",
                    'icinga_check_command': "/usr/lib/nagios/plugins/check_nagios /var/lib/icinga/status.dat 5 '/usr/sbin/icinga'",
                    'url_stylesheets_path': "/icinga/stylesheets",
                    'http_charset': "utf-8",
                    'refresh_rate': 90,
                    'refresh_type': 1,
                    'escape_html_tags': 1,
                    'result_limit': 50,
                    'show_tac_header': 1,
                    'use_pending_states': 1,
                    'first_day_of_week': 0,
                    'csv_delimiter': ";",
                    'csv_data_enclosure': "'",
                    'suppress_maintenance_downtime': 0,
                    'action_url_target': "main",
                    'notes_url_target': "main",
                    'authorization_config_file': "/etc/icinga/cgiauth.cfg",
                    'use_authentication': 1,
                    'use_ssl_authentication': 0,
                    'lowercase_user_name': 0,
                    'default_user_name': "guest",
                    'authorized_for_system_information': "icingaadmin",
#                    'authorized_contactgroup_for_system_information': "",
                    'authorized_for_configuration_information': "icingaadmin",
#                    'authorized_contactgroup_for_configuration_information': "",
                    'authorized_for_full_command_resolution': "icingaadmin",
#                    'authorized_contactgroup_for_full_command_resolution': "",
                    'authorized_for_system_commands': "icingaadmin",
#                    'authorized_contactgroup_for_system_commands': "",
                    'authorized_for_all_services': "icingaadmin",
                    'authorized_for_all_hosts': "icingaadmin",
#                    'authorized_contactgroup_for_all_service': "",
#                    'authorized_contactgroup_for_all_hosts': "",
                    'authorized_for_all_service_commands': "icingaadmin",
                    'authorized_for_all_host_commands': "icingaadmin",
#                    'authorized_contactgroup_for_all_service_commands': "",
#                    'authorized_contactgroup_for_all_host_commands', "",
#                    'authorized_for_read_only': "",
#                    'authorized_contactgroup_for_read_only': "",
#                    'authorized_for_comments_read_only': "",
#                    'authorized_contactgroup_for_comments_read_only': "",
#                    'authorized_for_downtimes_read_only': "",
#                    'authorized_contactgroup_for_downtimes_read_only': "",
                    'show_all_services_host_is_authorized_for': 1,
                    'show_partial_hostgroups': 0,
                    'show_partial_servicegroups': 0,
                    'statusmap_background_image': "smbackground.gd2",
                    'color_transparency': [255, 255, 255], 
                    'default_statusmap_layout': 5,
                    'host_unreachable_sound': "hostdown.wav",
                    'host_down_sound': "hostdown.wav",
                    'service_critical_sound': "critical.wav",
                    'service_warning_sound': "warning.wav",
                    'service_unknown_sound': "warning.wav",
                    'normal_sound': "noproblem.wav",
                    'status_show_long_plugin_output': 0,
                    'display_status_totals': 0,
                    'highlight_table_rows': 1,
                    'add_notif_num_hard': 28,
                    'add_notif_num_soft': 0,
                    'use_logging': 0,
                    'cgi_log_file': "/usr/share/icinga/htdocs/log/icinga-cgi.log",
                    'cgi_log_rotation_method': "d",
                    'cgi_log_archive_path': "/usr/share/icinga/htdocs/log",
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
                    'showlog_initial_states': 0,
                    'showlog_current_states': 0,
                    'enable_splunk_integration': 0,
#                    'splunk_url': "",
                    'object_cache_file': "/var/cache/icinga/objects.cache",
                    'status_file': "/var/cache/icinga/status.dat",
                    'resource_file': "/etc/icinga/resource.cfg",
                    'command_file': "/var/lib/icinga/rw/icinga.cmd",
                    'check_external_commands': 1,
                    'interval_length': 60,
                    'status_update_interval': 10,
                    'log_file': "/var/log/icinga/icinga.log",
                    'log_rotation_method': "d",
                    'log_archive_path': "/var/log/icinga/archives",
                    'date_format': "us",
                },
        })

        __salt__['mc_macros.update_local_registry'](
            'icinga_cgi', icinga_cgi_reg,
            registry_format='pack')
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
