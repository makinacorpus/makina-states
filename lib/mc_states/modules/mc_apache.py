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
        include_modules = ['version', 'rewrite',
                           'expires', 'headers',
                           'deflate', 'setenvif',
                           'socache_shmcb', 'ldap',
                           'authnz_ldap', 'ssl',
                           'status']
        exclude_modules = ['negotiation', 'autoindex', 'cgid']
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
                    "salt://makina-states/files/usr/bin/"
                    "apacheConfCheck.sh"),
                'httpd_user': 'www-data',
                'mpm': 'worker',
                'mpms': ['worker', 'event', 'prefork', 'itk'],
                'mpm-packages': {},
                'fastcgi_socket_directory': www_reg[
                    'socket_directory'],
                'virtualhosts': virtualhosts,
                'version': '2.2',
                'Timeout': 120,
                'vhost_template_source': (
                    '{default_vh_template_source}'),
                'vhost_content_source': (
                    '{default_vh_in_template_source}'),
                # old names, do not change, retrocompat
                'vhost_top_template': (
                    "salt://makina-states/files/etc/"
                    "apache2/includes/"
                    "top_virtualhost_template.conf"),
                'default_vh_template_source': (
                    "salt://makina-states/files/etc/"
                    "apache2/sites-available/"
                    "virtualhost_template.conf"),
                'default_vh_in_template_source':  (
                    "salt://makina-states/files/etc/"
                    "apache2/includes/"
                    "in_virtualhost_template.conf"),
                'KeepAlive': True,
                'exclude_modules': exclude_modules,
                'include_modules': include_modules,
                'log_level': 'warn',
                'ssl_interface': '*',
                'ssl_ciphers': 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA',
                'ssl_protocols': '+TLSv1 +TLSv1.1 +TLSv1.2',
                'ssl_session_timeout': '600',
                'ssl_session_cache': (
                    'shmcb:/var/cache/apache2/ssl_sessions(512000)'),
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
                'no_options_log': True,
                'use_cronolog': True
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
        modmpm = 'mpm_{0}'.format(apacheSettings['mpm'])
        apacheSettings['include_modules'].append(modmpm)
        for mpm in apacheSettings['mpms']:
            if mpm != apacheSettings['mpm']:
                modmpm = 'mpm_{0}'.format(mpm)
                apacheSettings['exclude_modules'].append(modmpm)
        for k in 'include_modules', 'exclude_modules':
            apacheSettings[k] = __salt__['mc_utils.uniquify'](
                apacheSettings[k])
        for i in [
            'ssl_session_cache',
        ]:
            apacheSettings[i] = apacheSettings[i].format(**apacheSettings)
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


def _togglemod(title, action, module, checked):
    ret = {'Name': title,
           'Module': module,
           'status': 0,
           'result': False,
           'changed': True}
    command = [action, '-f', '-m',  module]
    cret = __salt__['cmd.run_all'](command, python_shell=False)
    for k in 'stderr', 'stdout':
        if 'does not exist' in cret[k]:
            cret['retcode'] = 0
            ret['changed'] = False
    status = cret['retcode']
    ret['return'] = cret
    pat = '{0} already {1}'.format(module, checked)
    if pat in cret['stdout']:
        ret['changed'] = False
    if status == 1:
        ret['Status'] = 'Module {0} Not found'.format(module)
    elif status == 0:
        ret['Status'] = 'Module {0} {1}'.format(
            module, checked)
        ret['result'] = True
    else:
        ret['Status'] = status
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
    return _togglemod(
        'Apache2 Enable Module',
        'a2enmod', module, 'enabled')


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

    return _togglemod(
        'Apache2 Disable Module',
        'a2dismod', module, 'disabled')


def vhost_settings(domain, doc_root, **kwargs):
    '''Used by apache macro

    vh_top_source
        source (jinja) of the file.managed for
        the virtualhost template. (empty by default)
        this will be included at the global conf level

    vh_template_source
        source (jinja) of the file.managed for
        the virtualhost template.
        this will be the vhost definitions which in turn include
        the vhost defs
    vh_content_source
        source (jinja) of the file.managed for
        the virtualhost template.
        this will be included at the vhost level
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

    kwargs.setdefault('ssl_session_timeout',
                      apacheSettings['ssl_session_timeout'])
    kwargs.setdefault('redirect_aliases', True)
    kwargs.setdefault('allow_htaccess', False)
    kwargs.setdefault('active', True)
    kwargs.setdefault('mode', mode)

    kwargs.setdefault(
        'vh_template_source',
        apacheSettings['vhost_template_source'])
    kwargs.setdefault(
        'vh_top_source',
        apacheSettings['vhost_top_template'])

    kwargs.setdefault(
        'vh_content_source',
        kwargs.get('vh_in_template_source',
                   apacheSettings['default_vh_in_template_source']))
    kwargs['ivhost'] = (
        "{basedir}/{number}-{domain}"
    ).format(number=number,
             basedir=apacheSettings['ivhostdir'],
             domain=vhost_basename)
    kwargs['ivhosttop'] = (
        "{basedir}/{number}-{domain}-top"
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
    # to disable ssl, ssl_cert must be a empty string
    if apacheSettings.get('ssl_cert', None) != '':
        ssldomain = domain
        if ssldomain in ['default']:
            ssldomain = __grains__['fqdn']
        lcert, lkey, lchain = __salt__[
            'mc_ssl.get_configured_cert'](ssldomain, gen=True)
        apacheSettings.setdefault('ssl_cert',
                                  lcert + lchain)
        apacheSettings.setdefault('ssl_key',
                                  lcert + lchain + lkey)
        apacheSettings.setdefault('ssl_bundle', '')
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
                "/etc/ssl/apache/{0}_{1}.pem".format(ssldomain, k))
    return apacheSettings
