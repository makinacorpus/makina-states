# -*- coding: utf-8 -*-
'''
.. _module_mc_apache:

mc_apache / apache httpd functions
============================================

If you alter this module and want to test it, do not forget to
deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_apache

Check the mc_apache states for details.

Do not forget to sync salt cache::

  salt-call state.sls makina-states.controllers.salt

'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils

__name = 'apache'

log = logging.getLogger(__name__)
def_vh = 'salt://makina-states/files/etc/apache2/sites-available/default_vh.conf'

def settings():
    '''
    Registry for apache related settings

    heses settings are loaded from defaults + grains + pillar.
    pache Fine Settings

    httpd_user
        apache system user
    mpm
        mpm to use

    mpm-packages
        system related packaged to install the desired mpm

    version
        targeted apache version to switch the configuration for

    log_level
        httpd log level

    fastcgi_params
        mappings of specific params for mod_fastcgi
        Please look the module code and the apache documentation
        if you are not happy with defaults

    fastcgi_project_root
        internal setting

    fastcgi_shared_mode
        internal setting

    fastcgi_enabled
        internal setting

    fastcgi_socket_directory
        internal setting

    serveradmin_mail
        default server admin email

    Timeout
        The number of seconds before receives and sends time out.
        default is 300 (5min), 1 or 2 min should be enough for any
        client request (so 60 or 120). beware of DOS!

    KeepAlive
        bool: are KeepAlive requests allowed

    MaxKeepAliveRequests:
        maximum number of allowed KeepAlive requests
        (compare with MaxClients)

    KeepAliveTimeout:
        How many seconds should we keep Keepalive conn open (say
        something between 3 and 5 usually, be careful for DOS!)

    log_level
       log level, allowed values are debug, info, notice, warn, error,
                                     crit, alert, emerg
    serveradmin_mail
       default webmaster mail (used on error pages)

    mpm prefork

       StartServers
           number of server processes to start

       MinSpareServers
           minimum number of server processes which are kept spare

       MaxSpareServers
           &maximum number of server processes which are kept spare

       MaxRequestsPerChild
           maximum number of requests a server process serves
           set 0 to disable process recylcing
       MaxClients
           (alias MaxRequestWorkers): maximum number of server
           processes allowed to start

    mpm worker

       StartServers
           initial number of server processes to start

       MinSpareThreads
           minimum number of worker threads which are kept spare

       MaxSpareThreads
           maximum number of worker threads which are kept spare

       ThreadLimit
           ThreadsPerChild can be changed to this maximum value
           during a graceful restart. ThreadLimit can only be changed
           by stopping and starting Apache.

       ThreadsPerChild
           constant number of worker threads in each server process

       MaxRequestsPerChild
           (alias MaxConnectionsPerChild):
            maximum number of requests a server process serves
            set 0 to disable process recylcing

       MaxClients
           (alias MaxRequestWorkers): maximum number of threads

    mpm event
       all workers settings are used

       AsyncRequestWorkerFactor
           max of concurrent conn is:
           (AsyncRequestWorkerFactor + 1) * MaxRequestWorkers
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        apacheStepOne = __salt__['mc_utils.dictupdate'](
            {
                'httpd_user': 'www-data',
                'mpm': 'worker',
                'mpm-packages': {},
                'version': '2.2',
                'Timeout': 120,
                'KeepAlive': True,
                'log_level': 'warn',
                'serveradmin_mail': 'webmaster@localhost',
                "fastcgi_params": {
                    "InitStartDelay": 1,
                    "minProcesses": 2,
                    "maxClassProcesses": 20,
                    "startDelay": 5,
                    "killInterval": 300,
                    "gainValue": 0.5,
                    "appConnTimeout": 30,
                    "idleTimeout": 60,
                    "listen_queue_depth": 100,
                    "min_server_life": 30,
                    "multiThreshold": 50,
                    "processSlack": 5,
                },
                'fastcgi_project_root': '',
                'fastcgi_shared_mode': True,
                'fastcgi_enabled': True,
                'fastcgi_socket_directory': (
                    locations['var_dir'] + '/lib/apache2/fastcgi'),
                'allow_bad_modules': {
                    'negotiation': False,
                    'autoindex': False,
                    'cgid': False,
                },
            },
            __salt__['grains.filter_by'](
                {
                    'dev': {
                        'MaxKeepAliveRequests': 5,
                        'KeepAliveTimeout': 5,
                        'prefork': {
                            'StartServers': 5,
                            'MinSpareServers': 5,
                            'MaxSpareServers': 5,
                            'MaxClients': 20,
                            'MaxRequestsPerChild': 300
                        },
                        'worker': {
                            'StartServers': 2,
                            'MinSpareThreads': 25,
                            'MaxSpareThreads': 75,
                            'ThreadLimit': 64,
                            'ThreadsPerChild': 25,
                            'MaxRequestsPerChild': 300,
                            'MaxClients': 200
                        },
                        'event': {
                            'AsyncRequestWorkerFactor': "1.5"
                        },
                        'monitoring': {
                            'allowed_servers': '127.0.0.1 ::1',
                            'extended_status': False
                        },
                        'virtualhosts': {}},
                    'prod': {
                        'MaxKeepAliveRequests': 100,
                        'KeepAliveTimeout': 3,
                        'prefork': {
                            'StartServers': 25,
                            'MinSpareServers': 25,
                            'MaxSpareServers': 25,
                            'MaxClients': 150,
                            'MaxRequestsPerChild': 3000
                        },
                        'worker': {
                            'StartServers': 5,
                            'MinSpareThreads': 50,
                            'MaxSpareThreads': 100,
                            'ThreadLimit': 100,
                            'ThreadsPerChild': 50,
                            'MaxRequestsPerChild': 3000,
                            'MaxClients': 700
                        },
                        'event': {
                            'AsyncRequestWorkerFactor': "4"
                        },
                        'monitoring': {
                            'allowed_servers': '127.0.0.1 ::1',
                            'extended_status': False
                        },
                        'virtualhosts': {
                        }
                    }
                },
                grain='default_env',
                default='dev'
            )
        )
        # Ubuntu 13.10 is now providing 2.4 with event by default #
        if (
            grains['lsb_distrib_id'] == "Ubuntu"
            and "{0}".format(grains['lsb_distrib_release']) >= "13.10"
        ):
            apacheStepOne.update({'mpm': 'event'})
            apacheStepOne.update({'version': '2.4'})
        apacheStepOne['multithreaded_mpm'] = apacheStepOne['mpm']

        apacheDefaultSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.http.apache',
            __salt__['grains.filter_by']({
                'Debian': {
                    'virtualhosts': {
                        'default': {
                            'number': '000',
                            'active': True,
                            'domain': 'default',
                            'vh_template_source': def_vh,
                            'doc_root': '/var/www/default',
                            'log_level': "{log_level}",
                            'serveradmin_mail': '{serveradmin_mail}',
                            'mode': 'production',
                        },
                    },
                    'packages': ['apache2'],
                    'mpm-packages': {
                        'worker': ['apache2-mpm-worker'],
                        'prefork': ['apache2-mpm-prefork'],
                        #'itk': ['apache2-mpm-itk'],
                        'event': ['apache2-mpm-event'],
                    },
                    'mod_packages': {
                        'mod_fcgid': 'libapache2-mod-fcgid',
                        'mod_fastcgi': 'libapache2-mod-fastcgi',
                    },
                    'server': 'apache2',
                    'service': 'apache2',
                    'mod_wsgi': 'libapache2-mod-wsgi',
                    'basedir': locations['conf_dir'] + '/apache2',
                    'vhostdir': (
                        locations['conf_dir'] + '/apache2/sites-available'),
                    'evhostdir': (
                        locations['conf_dir'] + '/apache2/sites-enabled'),
                    'confdir': locations['conf_dir'] + '/apache2/conf.d',
                    'logdir': locations['var_log_dir'] + '/apache2',
                    'wwwdir': locations['srv_dir']
                },
                'RedHat': {
                    'packages': ['httpd'],
                    'server': 'httpd',
                    'service': 'httpd',
                    'mod_wsgi': 'mod_wsgi',
                    'basedir': locations['conf_dir'] + '/httpd',
                    'vhostdir': locations['conf_dir'] + '/httpd/conf.d',
                    'confdir': locations['conf_dir'] + '/httpd/conf.d',
                    'logdir': locations['var_log_dir'] + '/httpd',
                    'wwwdir': locations['var_dir'] + '/www'
                },
            },
                grain='os_family',
                default='Debian',
                merge=apacheStepOne
            )
        )

        # FINAL STEP: merge with data from pillar and grains
        apacheSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.http.apache', apacheDefaultSettings)
        #mpm = apacheSettings.get('mpm', None)
        #apacheSettings['mpm-packages'] = []
        #if __grains__['os_family'] in ['Debian'] and mpm:
        #    apacheSettings['packages'].extend(
        #        'apache2-mpm-{0}'.format(mpm)
        #    )
        return apacheSettings
    return _settings()


def get_version():
    '''
    Ensures the installed apache version matches all the given version number

    For a given 2.2 version 2.2.x current version would return an OK state

    version
        The apache version

    CLI Examples:

    .. code-block:: bash

        salt '*' mc_apache.get_version
    '''
    ret = {}
    full_version = __salt__['apache.version']()
    _version = full_version.split("/")[1].split(" ")[0]
    ret['result'] = {
        # Apache/2.4.6 (Ubuntu) -> 2.4.6
        'version': _version,
        # [2][4]
        # [2][4][6]
        'current_version_list': str(_version).split("."),
    }
    return ret


def check_version(version):
    '''
    Ensures the installed apache version matches all the given version number

    For a given 2.2 version 2.2.x current version would return an OK state

    version
        The apache version

    CLI Examples:

    .. code-block:: bash

        salt '*' mc_apache.check_version 2.4
    '''
    ret = get_version()
    _version = ret['result']['version']
    if not _version.startswith("{0}".format(version)):
        ret['result'] = False
        ret['comment'] = (
            'Apache requested version {0} is not verified '
            'by current version: {1}'.format(
                _version, version))
        return ret
    ret['result'] = True
    ret['comment'] = 'Apache version {0} verify requested {1}'.format(
        _version, version)
    return ret


def a2enmod(module):
    '''
    Runs a2enmod for the given module.

    This will only be functional on Debian-based operating systems (Ubuntu,
    Mint, etc).

    module
        string, module name

    CLI Examples:

    .. code-block:: bash

        salt '*' mc_apache.a2enmod autoindex
    '''
    ret = {}
    command = ['a2enmod', module]

    try:
        status = __salt__['cmd.retcode'](command, python_shell=False)
    except Exception as e:
        return e

    ret['Name'] = 'Apache2 Enable Module'
    ret['Module'] = module
    ret['result'] = False

    if status == 1:
        ret['Status'] = 'Module {0} Not found'.format(module)
    elif status == 0:
        ret['Status'] = 'Module {0} enabled'.format(module)
        ret['result'] = True
    else:
        ret['Status'] = status

    return ret


def a2dismod(module):
    '''
    Runs a2dismod for the given module.

    This will only be functional on Debian-based operating systems (Ubuntu,
    Mint, etc).

    module
        string, module name

    CLI Examples:

    .. code-block:: bash

        salt '*' mc_apache.a2dismod autoindex
    '''
    ret = {}
    command = ['a2dismod', module]

    try:
        status = __salt__['cmd.retcode'](command, python_shell=False)
    except Exception as e:
        return e

    ret['Name'] = 'Apache2 Disable Modules'
    ret['Module'] = module
    ret['result'] = False

    if status == 1:
        ret['Status'] = 'Module {0} Not found'.format(module)
    elif status == 0:
        ret['Status'] = 'Module {0} disabled'.format(module)
        ret['result'] = True
    else:
        ret['Status'] = status

    return ret


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
