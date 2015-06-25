# -*- coding: utf-8 -*-
'''

.. _state_mc_apache:

mc_apache / apache states
============================================



If you alter this module and want to test it, do not forget to deploy it on
minion using::

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

log = logging.getLogger(__name__)

# Modules explicitly required by states
# Module explicitly excluded by states

_DEFAULT_MPM = 'worker'


def _tied_to_apacheconf(deps):
    tied = False
    for dep in deps:
        for module, stateid in dep.items():
            if module == 'mc_apache':
                tied = True
            if module == 'mc_proxy':
                if stateid.startswith('makina-apache-'):
                    tied = True
        if tied:
            break
    return tied


def _check_apache_loaded(ret):
    if 'apache.version' not in __salt__:
        log.warning(
            'Use of mc_apache method without apache previously '
            'installed via pkg state.'
        )
        ret['result'] = False
        ret['comment'] = (
            'Apache is not installed (salt apache module not loaded), '
            'please use a pkg state to ensure apache is installed as a '
            'dependency of this current state')
    return ret


def _load_modules():
    _MODULES_INCLUDED = __context__.setdefault(
        'mc_apache_MODULES_INCLUDED', [])
    _MODULES_EXCLUDED = __context__.setdefault(
        'mc_apache_MODULES_EXCLUDED', [])
    _MODULES_REGISTERED = __context__.setdefault(
        'mc_apache_MODULES_REGISTERED', [])
    _shared_modules = __context__.setdefault(
        'mc_apache_shared_modules', [])
    _static_modules = __context__.setdefault(
        'mc_apache_static_modules', [])
    if not _shared_modules and not _static_modules:
        modules = __salt__['apache.modules']()
        _static_modules.extend(modules.get('static', []))
        _shared_modules.extend(modules.get('shared', []))
    return (
        _MODULES_INCLUDED,
        _MODULES_EXCLUDED,
        _MODULES_REGISTERED,
        _shared_modules,
        _static_modules)


def _checking_modules(modules_excluded=None,
                      modules_included=None,
                      blind_mode=False):
    (_MODULES_INCLUDED,
     _MODULES_EXCLUDED,
     _MODULES_REGISTERED,
     _shared_modules,
     _static_modules) = _load_modules()
    ret = {'changes': '',
           'result': None,
           'comment': ''}
    # Load current shared and static modules
    _load_modules()
    modifications = []
    comments = []
    if not modules_included:
        modules_included = []
    if not modules_excluded:
        modules_excluded = []
    # manage junction of _MODULES_[INCLUDED/EXCLUDED] and given parameters
    for module in _MODULES_INCLUDED:
        if module in modules_excluded:
            comments.append(
                ("module {0} will not be excluded, "
                 "it was enforced by another state.").format(module))
            modules_excluded.remove(module)
        if module not in modules_included:
            modules_included.append(module)
    for module in _MODULES_EXCLUDED:
        if module not in modules_excluded:
            modules_excluded.append(module)
        if module in modules_included:
            comments.append(
                ("module {0} will not be included, "
                 "it was enforced by another state.").format(module))
            modules_included.remove(module)

    # Now see if we have something to do
    for module in modules_excluded:
        if module in modules_included:
            ret['result'] = False
            comments.append(("ERROR: module {0} cannot be both in exclusion "
                             "and inclusion list.").format(module))
            continue
        elif module + '_module' in _static_modules:
            ret['result'] = False
            comments.append(
                ("ERROR: module {0} cannot be excluded as it "
                 "is not a shared but a static module.").format(module))
            continue
        elif (module + '_module' in _shared_modules) or blind_mode:
            log.info(
                'a2dismod {0}'.format(module)
            )
            if not __opts__['test']:
                result = __salt__['mc_apache.a2dismod'](module)
            else:
                result['result'] = True
            comments.append(
                "Disabling module {0}::{1}".format(module, result['Status']))
            if not result['result']:
                log.warning(
                    'a2dismod {0} : Failure detected'.format(module)
                )
                ret['result'] = False
                continue
            else:
                modifications.append({'action': 'disable',
                                      'module': module})
    for module in modules_included:
        if module + '_module' not in _shared_modules:
            if module + '_module' in _static_modules:
                comments.append(("module {0} is a static module, "
                                 "we do not need activation.").format(module))
            else:
                log.info(
                    'a2enmod {0}'.format(module)
                )
                if not __opts__['test']:
                    result = __salt__['mc_apache.a2enmod'](module)
                else:
                    result['result'] = True
                comments.append("Enabling module {0}::{1}".format(
                    module, result['Status']))
                if not result['result']:
                    log.warning(
                        'a2enmod {0} : Failure detected'.format(module)
                    )
                    ret['result'] = False
                    continue
                else:
                    modifications.append({'action': 'enable',
                                          'module': module})
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
                        'Rollback: Undo a2enmod of {0} using a2dismod'.format(
                            change['module'])
                    )
                    __salt__['mc_apache.a2dismod'](change['module'])
                else:
                    log.warning(
                        'Rollback: Undo a2enmod of {0} using a2dismod'.format(
                            change['module'])
                    )
                    __salt__['mc_apache.a2enmod'](change['module'])
        else:
            changes = [('Shared modules configuration altered, '
                        'You will need to restart Apache server!')]
            for change in modifications:
                if change['action'] is 'enable':
                    changes.append(
                        " [+] Enabling module {0}".format(change['module']))
                else:
                    changes.append(
                        " [-] Disabling module {0}".format(change['module']))
            ret['changes'] = "\n".join(changes)
    ret['comment'] = ("\n" + " " * 19).join(comments)
    if ret['result'] is None:
        ret['result'] = True
    return ret


def include_module(name,
                   modules,
                   **kwargs):
    (_MODULES_INCLUDED,
     _MODULES_EXCLUDED,
     _MODULES_REGISTERED,
     _shared_modules,
     _static_modules) = _load_modules()
    ret = {'name': name,
           'changes': {},
           'result': None,
           'comment': ''}
    comments = []
    ret = _check_apache_loaded(ret)
    if ret['result'] is False:
        return ret

    require_in = __low__.get('require_in', [])
    watch_in = __low__.get('watch_in', [])
    deps = []
    for x in require_in:
        deps.append(x)
    for x in watch_in:
        deps.append(x)
    if not _tied_to_apacheconf(deps):
        ret['result'] = False
        ret['comment'] = (
            'Orphaned include_module {0}, please use a require_in '
            'targeting mc_apache.deployed').format(name)
        return ret

    if type(modules) is not list:
        moduleslist = modules.split()
    else:
        moduleslist = modules
    for module in moduleslist:
        if module in _MODULES_EXCLUDED:
            log.info(
                ('MC_Apache: removing module {0} from exclusion list'
                 ' because of {1}').format(module, name)
            )
            comments.append(
                'Removing module {0} from exclusion list'.format(module))
            _MODULES_EXCLUDED.remove(module)
        if module not in _MODULES_INCLUDED:
            log.info(
                ('MC_Apache: adding module {0} to inclusion list'
                 ' because of {1}').format(module, name)
            )
            comments.append(
                'Adding module {0} in inclusion list'.format(module))
            _MODULES_INCLUDED.append(module)
    ret['comment'] = ("\n" + " " * 19).join(comments)
    ret['result'] = True
    return ret


def exclude_module(name,
                   modules,
                   **kwargs):
    _MODULES_INCLUDED = __context__.setdefault(
        'mc_apache_MODULES_INCLUDED', [])
    _MODULES_EXCLUDED = __context__.setdefault(
        'mc_apache_MODULES_EXCLUDED', [])
    _MODULES_REGISTERED = __context__.setdefault(
        'mc_apache_MODULES_REGISTERED', [])
    _shared_modules = __context__.setdefault(
        'mc_apache_shared_modules', [])
    _static_modules = __context__.setdefault(
        'mc_apache_static_modules', [])
    ret = {'name': name,
           'changes': {},
           'result': None,
           'comment': ''}
    comments = []
    ret = _check_apache_loaded(ret)
    if ret['result'] is False:
        return ret

    require_in = __low__.get('require_in', [])
    watch_in = __low__.get('watch_in', [])
    deps = []
    for x in require_in:
        deps.append(x)
    for x in watch_in:
        deps.append(x)
    if not _tied_to_apacheconf(deps):
        ret['result'] = False
        ret['comment'] = (
            'Orphaned exclude_module {0}, please use a require_in or watch_in '
            'targeting mc_apache.deployed').format(name)
        return ret

    if type(modules) is not list:
        moduleslist = modules.split()
    else:
        moduleslist = modules
    for module in moduleslist:
        if module in _MODULES_INCLUDED:
            log.info(
                ('MC_Apache: removing module {0} from inclusion list'
                 ' because of {1}').format(module, name)
            )
            comments.append(
                'Removing module {0} from inclusion list'.format(module))
            _MODULES_INCLUDED.remove(module)
        if module not in _MODULES_EXCLUDED:
            log.info(
                ('MC_Apache: adding module {0} to exclusion list'
                 ' because of {1}').format(module, name)
            )
            comments.append(
                'Adding module {0} in exclusion list'.format(module))
            _MODULES_EXCLUDED.append(module)
    ret['comment'] = ("\n" + " " * 19).join(comments)
    ret['result'] = True
    return ret


def deployed(name,
             mpm='worker',
             version="2.2",
             serveradmin_mail='webmaster@localhost',
             timeout=120,
             keep_alive=True,
             keep_alive_timeout=5,
             prefork_start_servers=5,
             prefork_min_spare_servers=5,
             prefork_max_spare_servers=5,
             prefork_max_clients=10,
             max_keep_alive_requests=5,
             max_requests_per_child=3000,
             extra_configuration='',
             **kwargs):
    '''
    Ensures that apache is deployed, once, with given version and main settings

    name
        The state name, not used internally

    version
        The apache version

    '''
    _APACHE_DEPLOYED = __context__.setdefault('mc_apache_APACHE_DEPLOYED', False)
    (_MODULES_INCLUDED,
     _MODULES_EXCLUDED,
     _MODULES_REGISTERED,
     _shared_modules,
     _static_modules) = _load_modules()
    ret = {'name': name,
           'changes': {},
           'result': None,
           'comment': ''}
    comments = []
    cret = _check_apache_loaded(ret)
    if cret['result'] is False:
        return cret
    modules_excluded = []
    modules_included = []
    settings = __salt__['mc_apache.settings']()
    # ensure only ONE apache main configuration is applied on this server
    if _APACHE_DEPLOYED:
        ret['result'] = False
        ret['comment'] = (
            'mc_apache.deployed is called several times. '
            'A previous call was made by state {0}. Please ensure you '
            'do not try to alter main apache configuration on several states.'
            ' Use extend.'
            '').format(_APACHE_DEPLOYED)
        return ret
    _APACHE_DEPLOYED = name

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
    cur_mpm = infos.get('server_mpm', 'unknown').lower()
    if mpm in ['unknown']:
        # try to activate mpm
        __salt__['cmd.run']('a2enmod mpm_{0}'.format(mpm), python_shell=True)
        cur_mpm = infos.get('server_mpm', 'unknown').lower()
        for _mpm in [
            a for a in ['event', 'worker', 'prefork']
            if not cur_mpm == a
        ]:
            if mpm not in ['unknown']:
                break
            __salt__['cmd.run']('a2enmod mpm_{0}'.format(_mpm),
                                python_shell=True)
            cur_mpm = infos.get('server_mpm', 'unknown').lower()

    versions = __salt__['mc_apache.get_version']()['result']
    mpm_check_done = False
    blind_mode = False
    workers = [settings['mpm']] + [a for a in ['event', 'worker', 'prefork']
                                   if not a == settings['mpm']]
    if 'unknown' == cur_mpm:
        for mpm in workers:
            cret = __salt__['apache.a2enmod']('mpm_{0}'.format(mpm))
            if 'not found' not in cret.get('Status', '').lower():
                infos = __salt__['apache.fullversion']()
                cur_mpm = infos.get('server_mpm', 'unknown').lower()
                break
    if 'unknown' == cur_mpm:
        # quite certainly a syntax error in current conf
        mpm_check_done = True
        # chicken and eggs problem now is that this current error prevents the
        # mpm alteration, and the mpm is maybe the case of the error...
        # so try to enforce this mpm alteration
        blind_mode = True
        comments.append("WARNING: BLIND MODE: Current apache configuration "
                        "is maybe broken")
    if (
        (versions['version'] and versions['version'] > "2.2")
        and (cur_mpm != mpm or blind_mode)
    ):
        # try to activate the mpm and deactivate the others
        # if mpm are shared modules
        _load_modules()
        mpm_mods = ['mpm_event', 'mpm_worker', 'mpm_prefork']
        mpm_mod = 'mpm_' + cur_mpm
        if blind_mode or (mpm_mod + '_module' in _shared_modules):
            for mpm_item in mpm_mods:
                if mpm_item == 'mpm_' + mpm:
                    modules_included.append(mpm_item)
                else:
                    modules_excluded.append(mpm_item)
            # we'll redo the check after modules activation/de-activation
            if blind_mode:
                comments.append(
                    "1st MPM Check in blind mode, we'll try to "
                    "enforce the mpm shared module, prey that it's "
                    "a shared one.")
            else:
                comments.append(("1st MPM check: Wrong apache mpm module "
                                 "activated: (requested) {0}!={1} (current). "
                                 "we'll try to alter shared modules to "
                                 "fix that").format(mpm, cur_mpm))
        else:
            ret['result'] = False
            comments.append(
                ("ERROR: MPM CHECK: Wrong apache core mpm module "
                 "activated: (requested) {0}!={1} (current). "
                 "And mpm are not shared modules on this installation. "
                 "We need another apache package!").format(mpm, cur_mpm))
            # stop right here
            ret['comment'] = ("\n" + " " * 19).join(comments)
            return ret
    else:
        mpm_check_done = True
        comments.append("MPM check: " + cur_mpm + ", OK")
    result = _checking_modules(modules_excluded, modules_included, blind_mode)
    ctest = __salt__['cmd.run_all']('apache2ctl configtest')
    if ctest['retcode']:
        comments.append('Apache conf is wrong')
        comments.append(ctest['stderr'])
    # Modules management
    if result['comment'] is not '':
        comments.append(result['comment'])
    if result['changes']:
        ret['changes']['modules'] = result['changes']
    if not result['result']:
        ret['result'] = False
        # no need to go further
        ret['comment'] = ("\n" + " " * 19).join(comments)
        return ret
    modules = __salt__['apache.modules']()
    comments.append("Shared modules: " + ",".join(modules['shared']))

    # MPM check (2nd time, not in test mode, it would always fail in test mode)
    if not mpm_check_done and not __opts__['test']:
        infos = __salt__['apache.fullversion']()
        cur_mpm = cur_mpm = infos.get('server_mpm', 'unknown').lower()
        if cur_mpm != mpm:
            ret['result'] = False
            comments.append(
                ('ERROR: 2nd MPM check: Wrong apache core mpm module '
                 'activated: (requested) {0}!={1} (current)'
                 '').format(mpm, cur_mpm)
            )
            # stop right here
            ret['comment'] = ("\n" + " " * 19).join(comments)
            return ret
        else:
            comments.append("2nd MPM check: " + cur_mpm + ", OK")

    if ret['result'] is None:
        ret['result'] = True
    comments.append("Apache deployment: All verifications done.")
    ret['comment'] = ("\n" + " " * 19).join(comments)
    return ret
