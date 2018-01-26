# -*- coding: utf-8 -*-
'''

.. _module_mc_tomcat:

mc_tomcat / tomcat functions
============================================
'''

# Import python libs
import logging
import mc_states.api

__name = 'tomcat'

log = logging.getLogger(__name__)


def settings():
    '''
    tomcat settings

    jdk_ver
        jdk version to use (will install packages)
    java_opts
        java opts to give to tomcat start
    java_home
        JAVA_HOME of the jdk to use
    users
        mapping of users, roles & password::

            {
                'admin': {
                  'password': 'admin',
                  'roles': ['admin', 'manager'],
                }
            }

    shutdown_port
        default shutdown port (8005)
    tomcat_user
        tomcat system user
    tomcat_group
        tomcat system group
    address
        default address to listen on
    port
        default http port (8080)
    ssl_port
        default ssl port (8443)
    ajp_port
        default ajp port (8009)
    defaultHost
        default hostname (localhost)
    welcome_files
        list of files to serve as index (index.{htm,html,jsp})
    loglevel_console
        log level console (FINE)
    loglevel_1catalina_org
        log level for defaults vhosts (FINE)
    loglevel_2localhost_org
        log level for defaults vhosts (FINE)
    loglevel_Catalina_localhost_level
        loglevel for catalina section (INFO)
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        locs = __salt__['mc_locations.settings']()
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.java.tomcat7', {
                'jdk_ver': '6',
                'java_home': (
                    locs['usr_dir'] + '/lib/jvm/java-{jdk_ver}-oracle'),
                'java_opts': (
                    '-Djava.awt.headless=true '
                    '-Xms256M -Xmx2048M -XX:MaxPermSize=256m '
                    '-XX:+UseConcMarkSweepGC'),
                'conf_dir': locs['conf_dir'] + '/tomcat7',
                'roles': [],
                'users': {
                    'admin': {
                        'password': 'admin',
                        'roles': ['admin', 'manager'],
                    },
                },
                'shutdown_port': '8005',
                'address': '127.0.0.1',
                'port': '8080',
                'ssl_port': '8443',
                'ajp_port': '8009',
                'defaultHost': 'localhost',
                'welcome_files': ['index.html', 'index.jsp', 'index.htm'],
                'ver': '7',
                'loglevel_console': 'FINE',
                'loglevel_1catalina_org': 'FINE',
                'loglevel_2localhost_org': 'FINE',
                'loglevel_Catalina_localhost_level': 'INFO',
                'tomcat_user': 'tomcat7',
                'tomcat_group': 'tomcat7',
            }
        )
        return data
    return _settings()



#
