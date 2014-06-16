# -*- coding: utf-8 -*-
'''
.. _module_mc_icinga_web:

mc_icinga_web / icinga_web functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

import hmac
import hashlib

__name = 'icinga_web'

log = logging.getLogger(__name__)


def settings():
    '''
    icinga_web settings

    location
        installation directory

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        icinga_web_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga_web', registry_format='pack')
        locs = __salt__['mc_locations.settings']()

        # generate default password
        icinga_web_reg = __salt__[
            'mc_macros.get_local_registry'](
                'icinga_web', registry_format='pack')

        password_web_db = icinga_web_reg.setdefault('web.db_password', __salt__['mc_utils.generate_password']())
        password_web_root_account = icinga_web_reg.setdefault('web.root_account_password', __salt__['mc_utils.generate_password']())

        # get default ido password
        password_ido=""
        # TODO

        ido2db_database = {
            'type': "pgsql",
            'host': "localhost",
            'port': 5432,
#            'socket': "",
            'user': "icinga",
            'password': password_ido,
            'name': "icinga_ido",
            'prefix': "icinga_",
        }

        web_database = {
            'type': "pgsql",
            'host': "localhost",
            'port': 5432,
#            'socket': "",
            'user': "icinga",
            'password': password_web_db,
            'name': "icinga_web",
        }

        root_account = {
            'password': password_web_root_account,
            'salt': "0c099ae4627b144f3a7eaa763ba43b10fd5d1caa8738a98f11bb973bebc52ccd",
        }

        has_sgbd = ((('host' in web_database)
                     and (web_database['host']
                          in  [
                              'localhost', '127.0.0.1', grains['host']
                          ]))
                    or ('socket' in web_database))

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.monitoring.icinga_web', {
                'package': ['icinga-web'],
                'configuration_directory': locs['conf_dir']+"/icinga-web",
                'has_pgsql': ('pgsql' == web_database['type']
                              and has_sgbd),
                'has_mysql': ('mysql' == web_database['type']
                              and has_sgbd),
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
                    'virtualhost': "icinga.localhost",
                    'doc_root': "/usr/share/icinga-web/pub/",
                    'vh_content_source': "salt://makina-states/files/etc/icinga-web/nginx.conf",
                    'vh_top_source': "salt://makina-states/files/etc/icinga-web/nginx.top.conf",
                },
                'phpfpm': {
                    'listen': "/var/spool/www/icinga_fpm.sock",
                    'open_basedir': "/usr/share/icinga-web/:/var/cache/icinga-web/:/var/log/icinga-web/",
#                    'extension': [],
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
#                            'read': {
#                                'folders': {},
#                                'files': {},
#                            },
                            'write': {
#                                'folders': {},
                                'files': {
                                    'icinga_pipe': "/var/lib/icinga/rw/icinga.cmd",
                                },
                            },
                            'execute': {
#                                'folders': {},
                                'files': {
                                    'icinga_service': "/usr/bin/service icinga",
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
#                            'ssh_config': {
#                                'host': "debian.www",
#                                'port': 22,
#                                'auth': {
#                                    'type': "key",
#                                    'user': "icinga",
#                                    'private_key': "/usr/local/icinga-web/id_debian",
#                                    'password': "123",
#                                },
#                            },
                            'access': {
                                'useDefaults': "true",
#                                'readwrite': {
#                                    'folders': {},
#                                    'files': {},
#                                },
#                                'read': {
#                                    'folders': {},
#                                    'files': {},
#                                },
#                                'write': {
#                                    'folders': {},
#                                    'files': {},
#                                },
#                                'execute': {
#                                    'folders': {},
#                                    'files': {},
#                                },
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
#                    'loggers': {
#                        'default': "icinga-web",
#                         'loggers': {
#                             'icinga-debug': {
#                                  'class': "AgaviLogger",
#                                  'level': "",
#                             },
#                         },
#                    },
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
#                        'search.numberMinimumLetters': 2,
#                        'search.maximumResults': 200,
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
#                    'settings': {
#                        'available': "false",
#                        'app_name': "My Custom Version",
#                    },
                },
                'sla_xml': {
                    'settings': {
                        'default_timespan': "-1 month",
                        'enabled': "false",
                    }
                },
                'translation_xml': {
#                    'available_locales': {
#                        'default_locale': "de",
#                        'default_timezone': "GMT",
#                        'available_locales': {
#                            'de_DE': {
#                                'description': "Deutsch",
#                            },
#                            'en': {
#                                'description': "English",
#                            },
#                        },
#                    },
#                    'translators': {
#                        'default_domain': "icinga.default",
#                        'translators': {
#                            'date-tstamp': {
#                                'date_formatter': {
#                                    'type': "date",
#                                    'format': "yyyy-MM-dd"
#                                },
#                            },
#                        },
#                    },
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
#                   'dql': {
#                       'TARGET_MYVIEW': {
#                           'content': "<!-- - ... -->",
#                       },
#                   },
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
