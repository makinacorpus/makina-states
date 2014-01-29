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
import salt.utils.odict as odict

log = logging.getLogger(__name__)

_APACHE_DEPLOYED = False
# Modules explicitly required by states
_MODULES_EXCLUDED = []
# Module explicitly excluded by states
_MODULES_INCLUDED = []
# TODO: registered modules?
_MODULES_REGISTERED = []

_shared_modules = []
_static_modules = []

def _load_modules():
    global _shared_modules
    global _static_modules
    if not _shared_modules and not _static_modules:
        modules = __salt__['apache.modules']()
        _static_modules = modules.get('static',[])
        _shared_modules = modules.get('shared',[])

def _checking_modules( modules_excluded=None, modules_included=None, blind_mode=False):
    global _MODULES_INCLUDED
    global _MODULES_EXCLUDED
    global _MODULES_REGISTERED
    global _shared_modules
    global _static_modules
    ret = {'changes': '',
           'result': None,
           'comment': ''}
    # Load current shared and static modules
    _load_modules()
    # Load modules installed from previous run and which have not been excluded
    # since
    #_modules_registered = _load_registered_modules()
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
            comments.append("ERROR: module {0} cannot be both in exclusion and inclusion list.".format(module))
            continue
        elif module+'_module' in _static_modules:
            ret['result'] = False
            comments.append("ERROR: module {0} cannot be excluded as it is not a shared but a static module.".format(module))
            continue
        elif (module+'_module' in _shared_modules) or blind_mode:
            log.info(
                'a2dismod {0}'.format(module)
            )
            if not __opts__['test']:
                result = __salt__['mc_apache.a2dismod'](module)
            else:
                result['result'] = True
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
        if module+'_module' not in _shared_modules:
            if module+'_module' in _static_modules:
                comments.append("module {0} is a static module, we do not need activation.".format(module))
            else:
                log.info(
                    'a2enmod {0}'.format(module)
                )
                if not __opts__['test']:
                    result = __salt__['mc_apache.a2enmod'](module)
                else:
                    result['result'] = True
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
        if ret['result'] is False and not __opts__['test']:
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
    ret['comment'] = ("\n"+" "*19).join(comments)
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

    require_in = __low__.get('require_in', [])
    watch_in = __low__.get('watch_in', [])
    deps = require_in + watch_in
    if not filter(lambda x: 'mc_apache' in x, deps):
        ret['result'] = False
        ret['comment'] = 'Orphaned include_module {0}, please use a require_in targeting mc_apache.deployed'.format(name)
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
    ret['comment']=("\n"+" "*19).join(comments)
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

    require_in = __low__.get('require_in', [])
    watch_in = __low__.get('watch_in', [])
    deps = require_in + watch_in
    if not filter(lambda x: 'mc_apache' in x, deps):
        ret['result'] = False
        ret['comment'] = 'Orphaned exclude_module {0}, please use a require_in targeting mc_apache.deployed'.format(name)
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
    ret['comment']=("\n"+" "*19).join(comments)
    ret['result']=True
    return ret

def deployed(name,
             mpm='prefork',
             version="2.2",
             modules_excluded=None,
             modules_included=None,
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

    '''
    global _APACHE_DEPLOYED
    global _shared_modules

    ret = {'name': name,
           'changes': {},
           'result': None,
           'comment': ''}

    comments = []
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
        comments.append(result['comment'])

    # MPM check
    infos = __salt__['apache.fullversion']()
    cur_mpm = infos.get('server_mpm','unknown')
    mpm_check_done = False
    blind_mode=False
    if 'unknown' == cur_mpm :
        # quite certainly a syntax error in current conf
        mpm_check_done = True
        # chicken and eggs problem now is that this current error prevents the mpm alteration,
        # and the mpm is maybe the case of the error...
        # so try to enforce this mpm alteration
        blind_mode=True
        comments.append("WARNING: BLIND MODE: Current apache configuration is maybe broken")
    if cur_mpm != mpm or blind_mode:
        # try to activate the mpm and deactivate the others
        # if mpm are shared modules
        _load_modules()
        mpm_mods = ['mpm_event','mpm_worker','mpm_prefork']
        mpm_mod = 'mpm_'+cur_mpm
        if blind_mode or (mpm_mod+'_module' in _shared_modules) :
            for mpm_item in mpm_mods:
                if mpm_item == 'mpm_'+ mpm:
                    modules_included.append(mpm_item)
                else:
                    modules_excluded.append(mpm_item)
            # we'll redo the check after modules activation/de-activation
            if blind_mode:
                comments.append("1st MPM Check in blind mode, we'll try to enforce the mpm shared module, prey that it's a shared one.")
            else:
                comments.append("1st MPM check: Wrong apache mpm module activated: (requested) {0}!={1} (current). we'll try to alter shared modules to fix that".format(mpm,cur_mpm))
        else:
            #if module+'_module' in _static_modules:
            ret['result'] = False
            comments.append('ERROR: MPM CHECK: Wrong apache core mpm module activated: (requested) {0}!={1} (current). And mpm are not shared modules on this installation. We need another apache package!'.format(mpm,cur_mpm))
            # stop right here
            ret['comment']=("\n"+" "*19).join(comments)
            return ret
    else:
        mpm_check_done = True
        comments.append("MPM check: "+ cur_mpm + ", OK")

    # Modules management
    result = _checking_modules( modules_excluded, modules_included, blind_mode )
    if result['comment'] is not '' :
        comments.append(result['comment'])
    if result['changes'] :
        ret['changes']['modules'] = result['changes']
    if not result['result'] :
        ret['result'] = False;
        # no need to go further
        ret['comment']=("\n"+" "*19).join(comments)
        return ret
    modules = __salt__['apache.modules']()
    comments.append("Shared modules: "+ ",".join(modules['shared']))

    # MPM check (2nd time, not in test mode, it would always fail in test mode)
    if not mpm_check_done and not __opts__['test']:
        infos = __salt__['apache.fullversion']()
        cur_mpm = cur_mpm = infos.get('server_mpm','unknown')
        if cur_mpm != mpm:
            ret['result'] = False
            comments.append('ERROR: 2nd MPM check: Wrong apache core mpm module activated: (requested) {0}!={1} (current)'.format(mpm,cur_mpm))
            # stop right here
            ret['comment']=("\n"+" "*19).join(comments)
            return ret
        else:
            comments.append("2nd MPM check: "+ cur_mpm + ", OK")

    if ret['result'] is None:
        ret['result'] = True
    comments.append("Apache deployment: All verifications done.")
    ret['comment']=("\n"+" "*19).join(comments)
    return ret

