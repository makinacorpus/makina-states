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
import copy
# Import python libs
import logging
import mc_states.api

__name = 'apache'

log = logging.getLogger(__name__)
def_vh = (
    'salt://makina-states/files/etc/'
    'apache2/sites-available/default_vh.conf')


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
       max of concurrent conn is::

           (AsyncRequestWorkerFactor + 1) * MaxRequestWorkers
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        www_reg = __salt__['mc_www.settings']()
        locations = __salt__['mc_locations.settings']()
        virtualhosts = {
            'default': {
                'number': '000',
                'active': True,
                'domain': 'default',
                'vh_template_source': def_vh,
                'doc_root': www_reg['doc_root'],
                'log_level': "{log_level}",
                'serveradmin_mail': www_reg['serveradmin_mail'],
                'mode': 'production',
            }}
        apacheStepOne = __salt__['mc_utils.dictupdate'](
            {
                'apacheConfCheck': (
                    "salt://makina-states/_scripts/"
                    "apacheConfCheck.sh"),
                'httpd_user': 'www-data',
                'mpm': 'worker',
                'mpm-packages': {},
                'fastcgi_socket_directory': www_reg[
                    'socket_directory'],
                'virtualhosts': virtualhosts,
                'version': '2.2',
                'Timeout': 120,
                'default_vh_template_source': (
                    "salt://makina-states/files/etc/"
                    "apache2/sites-available/"
                    "virtualhost_template.conf"),
                'default_vh_in_template_source':  (
                    "salt://makina-states/files/etc/"
                    "apache2/includes/"
                    "in_virtualhost_template.conf"),
                'KeepAlive': True,
                'log_level': 'warn',
                'ssl_interface': '*',
                'ssl_ciphers': 'HIGH:!aNULL:!MD5',
                'ssl_protocols': '+SSLv3 +TLSv1 +TLSv1.1 +TLSv1.2',
                'ssl_session_timeout': '600',
                'ssl_session_cache_path': (
                    '/var/cache/apache2/{vhost_basename}'),
                'ssl_session_cache_file_path': (
                    '{ssl_session_cache_path}/session'),
                'ssl_session_cache': (
                    'shmcb:{ssl_session_cache_file_path}(512000)'),
                'ssl_port': '443',
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
                'fastcgi_shared_mode': True,
                'fastcgi_enabled': True,
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
                        }},
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
                    'virtualhosts': virtualhosts,
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
                    'ivhostdir': (
                        locations['conf_dir'] + '/apache2/includes'),
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


def vhost_settings(domain, doc_root, **kwargs):
    '''Used by apache macro

    vh_template_source
        source (jinja) of the file.managed for
        the vhirtualhost template
        default: http://goo.gl/RFgkHE (github)
    serveradmin_mail
        data that may be used on error page
        default is webmaster@<site-name>
    number
        Virtualhost priority number (for apache),
        without a default VH the first one became the
        default virtualhost
    redirect_aliases
        True by default, make a special Virtualhost with
        all server_aliases, all redirecting with a 301
        to the site name, better for SEO.
        But you may need real server_aliases for static
        parallel file servers, for example,
        then set that to True.
    allow_htaccess
        False by default, if your project use .htaccess
        files, then prey for your soul,
        eat some shit, kill yourself and set that to True
    vhost_basename:
        basename of file in /etc/apache2/sites-{enabled,available}
    log_level
        log level
    ssl_interface/interface
        interface of the namevirtualhost (like in "\*:80"),
        default is "\*"
    ssl_port/port
        port of the namevirtualhost (like in "\*:80"),
        default is "80" and "443" for ssl version
    ssl_cert
        ssl_cert content if any
    ssl_key
        ssl_key content if any
    '''
    _s = __salt__
    kwargs['domain'] = domain
    kwargs['doc_root'] = doc_root
    grains = __grains__
    apacheSettings = copy.deepcopy(
        _s['mc_apache.settings']()
    )
    nodetypes_reg = _s['mc_nodetypes.registry']()
    # retro compat
    extra_jinja_apache_variables = kwargs.pop(
        'extra_jinja_apache_variables', {})
    kwargs.update(extra_jinja_apache_variables)
    ##
    kwargs['domain'] = domain
    number = kwargs.setdefault('number', '100')

    kwargs.setdefault(
        'serveradmin_mail', "webmaster@{0}".format(domain))
    server_aliases = kwargs.setdefault('server_aliases', [])
    if not isinstance(server_aliases, list):
        server_aliases = kwargs['server_aliases'] = server_aliases.split()
    old_mode = (
        (grains["lsb_distrib_id"] == "Ubuntu"
         and grains["lsb_distrib_release"] < 13.10)
        or (grains["lsb_distrib_id"] == "Debian"
            and grains["lsb_distrib_release"] <= 7.0))

    mode = "production"
    if nodetypes_reg['is']['devhost']:
        mode = "dev"
    kwargs.setdefault('old_mode', old_mode)
    kwargs.setdefault('log_level', "warn")
    kwargs.setdefault('interface', "*")
    kwargs.setdefault('server_name', domain)
    kwargs.setdefault('port', 80)
    vhost_basename = kwargs.setdefault('vhost_basename', domain)
    kwargs.setdefault('project', vhost_basename.replace('.', '_'))
    kwargs.setdefault('ssl_interface',
                      apacheSettings['ssl_interface'])
    kwargs.setdefault('ssl_protocols',
                      apacheSettings['ssl_protocols'])
    kwargs.setdefault('ssl_port',
                      apacheSettings['ssl_port'])
    kwargs.setdefault('ssl_ciphers',
                      apacheSettings['ssl_ciphers'])
    for i in [
        'ssl_session_cache_path',
        'ssl_session_cache_file_path',
        'ssl_session_cache',
    ]:
        val = kwargs.setdefault(i, apacheSettings[i])
        kwargs[i] = val.format(**kwargs)

    kwargs.setdefault('ssl_session_timeout',
                      apacheSettings['ssl_session_timeout'])
    kwargs.setdefault('redirect_aliases', True)
    kwargs.setdefault('allow_htaccess', False)
    kwargs.setdefault('active', True)
    kwargs.setdefault('mode', mode)
    kwargs.setdefault(
        'vh_template_source',
        apacheSettings['default_vh_template_source'])
    kwargs.setdefault(
        'vh_content_source',
        kwargs.get('vh_in_template_source',
                   apacheSettings['default_vh_in_template_source']))
    kwargs['ivhost'] = (
        "{basedir}/{number}-{domain}"
    ).format(number=number,
             basedir=apacheSettings['ivhostdir'],
             domain=vhost_basename)
    kwargs['evhost'] = (
        "{basedir}/{number}-{domain}"
    ).format(number=number,
             basedir=apacheSettings['evhostdir'],
             domain=vhost_basename)
    kwargs['avhost'] = (
        "{basedir}/{number}-{domain}"
    ).format(number=number,
             basedir=apacheSettings['vhostdir'],
             domain=vhost_basename)
    apacheSettings = _s['mc_utils.dictupdate'](apacheSettings,
                                               kwargs)
    lcert, lkey, lchain = __salt__[
        'mc_ssl.get_configured_cert'](domain, gen=True)
    apacheSettings['ssl_cert'] = lcert + lchain
    apacheSettings['ssl_key'] = lcert + lchain + lkey
    if apacheSettings.get('ssl_cert', ''):
        apacheSettings['ssl_bundle'] = ''
        certs = ['ssl_cert']
        if apacheSettings.get('ssl_cacert', ''):
            if apacheSettings['ssl_cacert_first']:
                certs.insert(0, 'ssl_cacert')
            else:
                certs.append('ssl_cacert')
        for cert in certs:
            apacheSettings['ssl_bundle'] += apacheSettings[cert]
            if not apacheSettings['ssl_bundle'].endswith('\n'):
                apacheSettings['ssl_bundle'] += '\n'
    for k in ['ssl_bundle', 'ssl_key', 'ssl_cert', 'ssl_cacert']:
        apacheSettings.setdefault(
            k + '_path',
            "/etc/ssl/apache/{0}_{1}.pem".format(domain, k))
    return apacheSettings
