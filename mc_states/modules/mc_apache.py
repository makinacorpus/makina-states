'''
Management of Apache, Makina Corpus version
============================================

If you alter this module and want to test it, do not forget to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_apache

Check the mc_apache states for details. If you use this module as a template for a new module
do not forget to use salt-modules state in makina-states/servies/salt to get this module
included in salt modules (first time, this will build the symlinks linking the module
on /srv/salt/[_modules|_states, etc])::

  salt-call state.sls makina-states.services.salt
'''

# Import python libs
import logging
import mc_states.utils

__name = 'apache'

log = logging.getLogger(__name__)


def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings(REG):
        '''
        This is called from mc_services, loading all Apache default settings

        Theses settings are loaded from defaults+grains+pillar.
        Apache Fine Settings ------------------------------------------------
         Timeout: The number of seconds before receives and sends time out. default
                  is 300 (5min), 1 or 2 min should be enough for any client request
                  (so 60 or 120). beware of DOS!
         KeepAlive: bool: are KeepAlive requests allowed
         MaxKeepAliveRequests: maximum number of allowed KeepAlive requests
                              (compare with MaxClients)
         KeepAliveTimeout: How many seconds should we keep Keepalive conn open (say
                           something between 3 and 5 usually, be careful for DOS!)
         log_level: log level, allowed values are debug, info, notice, warn, error,
                    crit, alert, emerg
         serveradmin_mail: default webmaster mail (used on error pages)
         mpm prefork
           * StartServers: number of server processes to start
           * MinSpareServers: minimum number of server processes which are kept spare
           * MaxSpareServers: maximum number of server processes which are kept spare
           * MaxRequestsPerChild: maximum number of requests a server process serves
                                  set 0 to disable process recylcing
           * MaxClients : (alias MaxRequestWorkers): maximum number of server
                          processes allowed to start
         mpm worker
           * StartServers: initial number of server processes to start
           * MinSpareThreads: minimum number of worker threads which are kept spare
           * MaxSpareThreads: maximum number of worker threads which are kept spare
           * ThreadLimit: ThreadsPerChild can be changed to this maximum value
                          during a graceful restart. ThreadLimit can only be changed
                          by stopping and starting Apache.
           * ThreadsPerChild: constant number of worker threads in each server
                              process
           * MaxRequestsPerChild (alias MaxConnectionsPerChild): maximum number of
                              requests a server process serves set 0 to disable
                              process recylcing
           * MaxClients : (alias MaxRequestWorkers): maximum number of threads
         mpm event
           * all workers settings are used
           * AsyncRequestWorkerFactor: max of concurrent conn is
                                  (AsyncRequestWorkerFactor + 1) * MaxRequestWorkers
        '''
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locations = localsettings['locations']
        apacheStepOne = __salt__['grains.filter_by']({
            'dev': {
                'mpm': 'worker',
                'version': '2.2',
                'Timeout': 120,
                'KeepAlive': True,
                'MaxKeepAliveRequests': 5,
                'KeepAliveTimeout': 5,
                'log_level': 'warn',
                'serveradmin_mail': 'webmaster@localhost',
                'registered_modules': {},
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
                'virtualhosts': {}
            },
            'prod': {
                'mpm': 'worker',
                'version': '2.2',
                'Timeout': 120,
                'KeepAlive': True,
                'MaxKeepAliveRequests': 100,
                'KeepAliveTimeout': 3,
                'log_level': 'warn',
                'serveradmin_mail': 'webmaster@localhost',
                'registered_modules': {},
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
                'virtualhosts': {}
            }},
            grain='default_env',
            default='dev'
        )
        # Ubuntu 13.10 is now providing 2.4 with event by default #
        if (
            grains['lsb_distrib_id'] == "Ubuntu"
            and grains['lsb_distrib_release'] >= 13.10
        ):
            apacheStepOne.update({'mpm': 'event'})
            apacheStepOne.update({'version': '2.4'})

        apacheDefaultSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.http.apache', __salt__['grains.filter_by']({
                'Debian': {
                    'package': 'apache2',
                    'server': 'apache2',
                    'service': 'apache2',
                    'mod_wsgi': 'libapache2-mod-wsgi',
                    'basedir': locations['conf_dir'] + '/apache2',
                    'vhostdir': locations['conf_dir'] + '/apache2/sites-available',
                    'confdir': locations['conf_dir'] + '/apache2/conf.d',
                    'logdir': locations['var_log_dir'] + '/apache2',
                    'wwwdir': locations['srv_dir']
                },
                'RedHat': {
                    'package': 'httpd',
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
        apacheSettings = __salt__['mc_utils.defaults']('makina-states.services.http.apache', apacheDefaultSettings)

        return apacheSettings
    return _settings()

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

    ret = {'result': None,
           'comment': ''}
    full_version = __salt__['apache.version']()
    # Apache/2.4.6 (Ubuntu) -> 2.4.6
    _version=full_version.split("/")[1].split(" ")[0]
    op_version_list = str(version).split(".")  # [2][4]
    current_version_list = str(_version).split(".")  #[2][4][6]
    for number1, number2 in zip(op_version_list, current_version_list):
        if not number1 is number2:
            ret['result'] = False
            ret['comment'] = (
                'Apache requested version {0} is not verified '
                'by current version: {1}'.format(
                    _version, version))
            return ret
    ret['result'] = True
    ret['comment'] = 'Apache version {0} verify requested {1}'.format(
        _version,version)
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
