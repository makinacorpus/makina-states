# -*- coding: utf-8 -*-
'''
Management of Apache, Makina Corpus version
============================================

If you alter this module and want to test it, do not forget to deploy it on minion using::

  salt '*' saltutil.sync_states

If you use this state as a template for a new custom state
do not forget to use to get this module included in salt modules.

To comment

.. code-block:: yaml

    apache-main-conf:
      makina-states.apache.deployed:
        - version: 2.2
        - log_level: debug

Or using the "names:" directive, you can put several names for the same IP.
(Do not try one name with space-separated values).

.. code-block:: yaml

    server1:
      host.present:
        - ip: 192.168.0.42
        - names:
          - server1
          - florida
'''

# Import python libs
import logging

# Import salt libs
import salt.utils

log = logging.getLogger(__name__)

_APACHE_DEPLOYED = False
_MODULES_EXCLUDED = []
_MODULES_INCLUDED = []


def _checking_modules( modules_excluded=None, modules_included=None):
    global _MODULES_INCLUDED
    global _MODULES_EXCLUDED
    ret = {'changes': '',
           'result': None,
           'comment': ''}
    modules = __salt__['apache.modules']()
    static_modules = modules['static']
    shared_modules = modules['shared']
    modifications = []
    comments = []
    # manage junction of _MODULES_[INCLUDED/EXCLUDED] and given parameters
    for module in _MODULES_INCLUDED:
        if module in modules_excluded:
            comments.append("module {0} will not be excluded, it was enforced by another state.".format(module))
            modules_excluded.remove(module)
        if module not in modules_included:
            modules_included.append(module)
    for module in _MODULES_EXCLUDED:
        if module not in modules_excluded:
            modules_excluded.append(module)
        if module in modules_included:
            comments.append("module {0} will not be included, it was enforced by another state.".format(module))
            modules_included.remove(module)

    # Now see if we have something to do
    for module in modules_excluded:
        if module in modules_included:
            ret['result'] = False
            comments.append("module {0} cannot be both in exclusion and inclusion list.".format(module))
            continue
        elif module+'_module' in static_modules:
            ret['result'] = False
            comments.append("module {0} cannot be excluded as it is not a shared but a static module.".format(module))
            continue
        elif module+'_module' in shared_modules:
            log.info(
                'a2dismod {0}'.format(module)
            )
            result = __salt__['mc_apache.a2dismod'](module)
            comments.append("Disabling module {0}::{1}".format(module,result['Status']))
            if not result['result']:
                log.warning(
                    'a2dismod {0} : Failure detected'.format(module)
                )
                ret['result']=False
                continue
            else:
                modifications.append({'action':'disable','module':module})
        #else:
        #    comments.append("Module {0} already disabled".format(module))
    for module in modules_included:
        if module+'_module' not in shared_modules:
            if module+'_module' in static_modules:
                comments.append("module {0} is a static module, we do not need activation.".format(module))
            else:
                log.info(
                    'a2enmod {0}'.format(module)
                )
                result = __salt__['mc_apache.a2enmod'](module)
                comments.append("Enabling module {0}::{1}".format(module,result['Status']))
                if not result['result']:
                    log.warning(
                        'a2enmod {0} : Failure detected'.format(module)
                    )
                    ret['result']=False
                    continue
                else:
                    modifications.append({'action':'enable','module':module})
        #else:
        #    comments.append("Module {0} already enabled".format(module))
    if modifications:
        if ret['result'] is False:
            # undo modifications, let's do it next time
            # when the failing module will be fixed
            # so that state modification will be available
            # then, and not now with a failure status
            # (to restart apache when module is activated/disabled)
            for change in modifications:
                if change['action'] is 'enable':
                    log.warning(
                      'Rollback: Undo a2enmod of {0} using a2dismod'.format(change['module'])
                    )
                    __salt__['mc_apache.a2dismod'](change['module'])
                else:
                    log.warning(
                      'Rollback: Undo a2enmod of {0} using a2dismod'.format(change['module'])
                    )
                    __salt__['mc_apache.a2enmod'](change['module'])
        else:
            changes=['Shared modules configuration altered, You will need to restart Apache server!']
            for change in modifications:
                if change['action'] is 'enable':
                    changes.append(" [+] Enabling module {0}".format(change['module']))
                else:
                    changes.append(" [-] Disabling module {0}".format(change['module']))
            ret['changes'] = "\n".join(changes)
    ret['comments'] = "\n".join(comments)
    if ret['result'] is None:
        ret['result'] = True
    return ret

def include_module(name,
                   modules,
                   **kwargs):
    global _MODULES_INCLUDED
    global _MODULES_EXCLUDED
    ret = {'name': name,
           'changes': {},
           'result': None,
           'comment': ''}
    comments = []

    if not filter(lambda x: 'mc_apache.deployed' in x,
                  kwargs.get('require_in', []) ):
        ret['result'] = False
        ret['comment'] = 'Orphaned include_module {0}, use a require_in targeting mc_apache.deployed'.format(name)
        return ret

    if type(modules) is not list:
        moduleslist = modules.split()
    else:
        moduleslist = modules
    for module in moduleslist:
        if module in _MODULES_EXCLUDED:
            log.info(
              'MC_Apache: removing module {0} from exclusion list'
              ' because of {1}'.format(module,name)
            )
            comments.append('Removing module {0} from exclusion list'.format(module))
            _MODULES_EXCLUDED.remove(module)
        if not module in _MODULES_INCLUDED:
            log.info(
              'MC_Apache: adding module {0} to inclusion list'
              ' because of {1}'.format(module,name)
            )
            comments.append('Adding module {0} in inclusion list'.format(module))
            _MODULES_INCLUDED.append(module)
    ret['comment']="\n".join(comments)
    ret['result']=True
    return ret

def exclude_module(name,
                   modules,
                   **kwargs):
    global _MODULES_INCLUDED
    global _MODULES_EXCLUDED
    ret = {'name': name,
           'changes': {},
           'result': None,
           'comment': ''}
    comments = []

    if not filter(lambda x: 'mc_apache.deployed' in x,
                  kwargs.get('require_in', []) ):
        ret['result'] = False
        ret['comment'] = 'Orphaned exclude_module {0}, use a require_in targeting mc_apache.deployed'.format(name)
        return ret

    if type(modules) is not list:
        moduleslist = modules.split()
    else:
        moduleslist = modules
    for module in moduleslist:
        if module in _MODULES_INCLUDED:
            log.info(
              'MC_Apache: removing module {0} from inclusion list'
              ' because of {1}'.format(module,name)
            )
            comments.append('Removing module {0} from inclusion list'.format(module))
            _MODULES_INCLUDED.remove(module)
        if not module in _MODULES_EXCLUDED:
            log.info(
              'MC_Apache: adding module {0} to exclusion list'
              ' because of {1}'.format(module,name)
            )
            comments.append('Adding module {0} in exclusion list'.format(module))
            _MODULES_EXCLUDED.append(module)
    ret['comment']="\n".join(comments)
    ret['result']=True
    return ret

def deployed(name,
             version="2.2",
             modules_excluded=None,
             modules_included=None,
             log_level="warn",
             serveradmin_mail= 'webmaster@localhost',
             timeout= 120,
             keep_alive=True,
             keep_alive_timeout= 5,
             prefork_start_servers= 5,
             prefork_min_spare_servers= 5,
             prefork_max_spare_servers=5,
             prefork_max_clients= 10,
             max_keep_alive_requests= 5,
             max_requests_per_child= 3000,
             extra_configuration='',
             **kwargs):
    '''
    Ensures that apache is deployed, once, with given version and main settings

    name
        The state name, not used internally

    version
        The apache version

    log_level
        The log_level defined in apache
    '''
    global _APACHE_DEPLOYED

    ret = {'name': name,
           'changes': {},
           'result': None,
           'comment': ''}

    if modules_excluded is None:
        modules_excluded = ['negotiation','autoindex','cgid']
    if modules_included is None:
        modules_included = ['rewrite','status','expires','headers','deflate']


    if not __salt__.has_key('apache.version'):
        log.warning(
            'Use of mc_apache.deployed without apache previously installed via pkg state.'
        )
        ret['result'] = False
        ret['comment'] = 'Apache is not installed (salt apache module not loaded), please use a pkg state to ensure apache is installed as a dependency of this current state'
        return ret

    # ensure only one apache main configuration is applied on this server
    if _APACHE_DEPLOYED:
        ret['result'] = False
        ret['comment'] = 'mc_apache.deployed is called several times. A previous call was made by state {0}. Please ensure you do not try to alter main apache configuration on several states'.format(_APACHE_DEPLOYED)
        return ret
    _APACHE_DEPLOYED=name

    # Version check
    result = __salt__['mc_apache.check_version'](version)
    if not result['result']:
        ret['result'] = False
        ret['comment'] = result['comment']
        # stop right here
        return ret
    else:
        ret['comment'] = result['comment']

    infos = __salt__['apache.fullversion']()
    mpm = infos['server_mpm']

    # Modules management
    result = _checking_modules( modules_excluded, modules_included)
    if result['comment'] is not '' :
        ret['comment'] += "\n" + result['comment']
    if result['changes'] :
        ret['changes']['modules'] = result['changes']
    if not result['result'] :
        ret['result'] = False;
        # no need to go further
        return ret
    modules = __salt__['apache.modules']()
    ret['comment'] += "\n"+"Shared modules: "+ ",".join(modules['shared'])

    # LogLevel check

    if ret['result'] is None:
        ret['result'] = True
    ret['comment'] += "\nApache deployment: All verifications done."
    return ret

