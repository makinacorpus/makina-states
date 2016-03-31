# -*- coding: utf-8 -*-
'''
.. _module_mc_project_2:

mc_project_2 / project settings regitry APIV2
================================================



This is a Corpus Paas reactor, deploy your projects with style, salt style.

This can either:

    - Deploy locally a project
    - Deploy remotely a project over ssh (the remote host must have
      makina-states installed)

'''

import yaml.error
import datetime
import os
import grp
import pipes
import socket
import pprint
import shutil
import traceback
import uuid
import logging
import yaml
import copy
from distutils.version import LooseVersion
from mc_states.version import VERSION
from salt.utils.odict import OrderedDict
import salt.template
from salt.states import group as sgroup
from salt.states import user as suser
from salt.states import file as sfile
from salt.states import git as sgit
from salt.states import cmd as scmd
import salt.output
import salt.loader
import salt.utils
import salt.exceptions
from mc_states.api import (
    splitstrip,
    msplitstrip,
    indent,
    uniquify,
)

import mc_states.saltapi
from salt.ext import six as six

import mc_states.project as projects_api

log = logger = logging.getLogger(__name__)

_MARKER = object()
J = os.path.join
D = os.path.dirname
API_VERSION = '2'
ENVS = projects_api.ENVS
KEEP_ARCHIVES = projects_api.KEEP_ARCHIVES
PROJECT_INJECTED_CONFIG_VAR = 'cfg'
DEFAULT_PROJECT_NAME = 'project'
DEFAULT_COMMIT_MESSAGE = 'salt commit'
INITIAL_COMMIT_MESSAGE = 'initial'
DEFAULT_AUTHOR = 'makina-states'
DEFAULT_EMAIL = '{0}@paas.tld'.format(DEFAULT_AUTHOR)
DEFAULT_CONFIGURATION = {
    'name': None,
    'remote_less': None,
    'minion_id': None,
    'fqdn': None,
    'remote_host': '{fqdn}',
    'default_env': None,
    'installer': 'generic',
    'keep_archives': projects_api.KEEP_ARCHIVES,
    #
    'user': None,
    'groups': [],
    #
    'raw_console_return': False,
    #
    'only': None,
    'only_steps': None,
    #
    'api_version': API_VERSION,
    #
    'defaults': OrderedDict(),
    'env_defaults': OrderedDict(),
    'os_defaults': OrderedDict(),
    #
    'no_user': False,
    'no_default_includes': False,
    # INTERNAL
    'data': OrderedDict(),
    'sls_default_pillar': OrderedDict(),
    'deploy_summary': None,
    'deploy_ret': {},
    'push_pillar_url': 'ssh://root@{this_host}:{this_port}{pillar_git_root}',
    'push_salt_url': 'ssh://root@{this_host}:{this_port}{project_git_root}',
    'project_dir': '{projects_dir}/{name}',
    'project_root': '{project_dir}/project',
    'deploy_marker': '{project_root}/.tmp_deploy',
    'salt_root': '{project_root}/.salt',
    'remote_pillar_dir': (
        '{remote_projects_dir}/{remote_host}/{name}/pillar'),
    'remote_project_dir': (
        '{remote_projects_dir}/{remote_host}/{name}/project'),
    'pillar_root': '{project_dir}/pillar',
    'data_root': '{project_dir}/data',
    'archives_root': '{project_dir}/archives',
    'git_root': '{project_dir}/git',
    'project_git_root': '{git_root}/project.git',
    'git_deploy_hook': '{git_root}/project.git/hooks/deploy_hook.py',
    'pillar_git_root': '{git_root}/pillar.git',
    'current_archive_dir': None,
    'rollback': False,
    'this_host': 'localhost',
    'this_localhost': 'localhost',
    'this_port': '22'}
STEPS = ['deploy',
         'archive',
         'release_sync',
         'install',
         'rotate_archives',
         'rollback',
         'fixperms',
         'notify']
SPECIAL_SLSES = ["{0}.sls".format(a)
                 for a in STEPS
                 if a not in ['deploy',
                              'release_sync',
                              'rotate_archives',
                              'install']]

CUSTOM = '''
custom: bar
'''
TOP = '''
#
# This is the top pillar configuration file, link here all your
# environment configurations files to their respective minions
#
base:
  '*':
    - custom
'''


for step in STEPS:
    DEFAULT_CONFIGURATION['skip_{0}'.format(step)] = None


def _state_exec(*a, **kw):
    return __salt__['mc_state.sexec'](*a, **kw)


def _stop_proc(message, step, ret):
    ret['raw_comment'] = message
    ret['result'] = False
    raise projects_api.ProjectProcedureException(ret['raw_comment'],
                                                 salt_step=step,
                                                 salt_ret=ret)


def _check_proc(message, step, ret):
    if not ret['result']:
        _stop_proc(message, step, ret)


def _filter_ret(ret, raw=False):
    if not raw and 'raw_comment' in ret:
        del ret['raw_comment']
    return ret


def _hs(mapping, raw=False, outputter='highstate'):
    return __salt__['mc_utils.output'](mapping, raw=raw, outputter=outputter)


def _raw_hs(mapping, outputter='highstate'):
    return _hs(mapping, raw=True, outputter=outputter)


def _force_cli_retcode(ret):
    # cli codeerr = 3 in case of failure
    if not ret['result']:
        __context__['retcode'] = 3
    else:
        __context__['retcode'] = 0


def set_makina_states_author(directory,
                             name=DEFAULT_AUTHOR,
                             email=DEFAULT_EMAIL,
                             **kw):
    user, _ = get_default_user_group(**kw)
    force = kw.get('force', False)
    try:
        cemail = __salt__['git.config_get'](cwd=directory, key='user.email', user=user)
    except salt.exceptions.CommandExecutionError:
        cemail = None
    try:
        cname = __salt__['git.config_get'](cwd=directory, key='user.name', user=user)
    except salt.exceptions.CommandExecutionError:
        cname = None
    if force or not cemail:
        __salt__['git.config_set'](cwd=directory, key='user.email', value=email, user=user)
    if force or not cname:
        __salt__['git.config_set'](cwd=directory, key='user.name', value=name, user=user)


def remove_path(path):
    '''Remove a path.'''
    if os.path.exists(path) or os.path.islink(path):
        if os.path.islink(path):
            os.unlink(path)
        elif os.path.isfile(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    else:
        print
        print "'%s' was asked to be deleted but does not exists." % path
        print


def _sls_exec(name, cfg, sls):
    # be sure of the current project beeing loaded in the context
    set_project(cfg)
    cfg = get_project(name)
    ret = _get_ret(name)
    ret.update({'return': None, 'sls': sls, 'name': name})
    old_retcode = __context__.get('retcode', 0)
    pillar = __salt__['mc_utils.dictupdate'](
        copy.deepcopy(cfg['sls_default_pillar']),
        __salt__['mc_utils.copy_dunder'](__pillar__))
    # load an inner execer for our custom slses
    try:
        __salt__['mc_utils.add_stuff_to_opts'](__opts__)
        cret = __salt__['state.sls'](sls.format(**cfg),
                                     concurrent=True, pillar=pillar)
    finally:
        __salt__['mc_utils.remove_stuff_from_opts'](__opts__)
    ret['return'] = cret
    comment = ''
    __context__.setdefault('retcode', 0)
    is_really_valid = None
    failed = False
    if isinstance(cret, dict):
        if not cret:
            ret['result'] = True
            __context__['retcode'] = 0
            _append_comment(ret,
                            'Warning sls:\'{1}\' for project:\'{0}\' '
                            'did not execute any state!'.format(name, sls))

        for lowid, state in cret.items():
            failed = False
            if not isinstance(state, dict):
                # invalid data structure
                failed = True
    else:
        failed = True
    if not failed:
        for lowid, state in cret.items():
            if not state.get('result', False):
                failed = True
            else:
                if is_really_valid is None:
                    is_really_valid = True
            if failed:
                __context__['retcode'] = 3
                is_really_valid = False
                ret['result'] = False
    if (not is_really_valid) and (__context__['retcode'] > 0):
        ret['result'] = False
        body = ''
        if isinstance(cret, list):
            body += indent(cret)
        _append_comment(ret,
                        'Running {1} for {0} failed'.format(name, sls),
                        body=body)
    if cret and isinstance(cret, dict):
        _append_comment('SLS execution result of {0} for {1}:'.format(sls,
                                                                      name))
        ret['raw_comment'] += indent(_raw_hs(copy.deepcopy(cret)))
        ret['comment'] += indent(_hs(copy.deepcopy(cret)))
    msplitstrip(ret)
    return ret


def _get_ret(name=None, *args, **kwargs):
    ret = kwargs.get('ret', None)
    if name is None:
        name = kwargs.get('name', 'noname')
    if ret is None:
        ret = {'comment': '',
               'raw_comment': '',
               'result': True,
               'changes': {},
               'name': name}
    return ret


def _colors(color=None, exact=False):
    if color and not exact:
        color = color.upper()
    return mc_states.saltapi._colors(
        color=color, colorize=__opts__.get('color'))


def _append_comment(ret,
                    summary=None,
                    body=None,
                    color='YELLOW'):
    if body:
        colon = ':'
    else:
        colon = ''
    if summary:
        if 'raw_comment' in ret:
            ret['raw_comment'] += '\n{0}\n'.format(summary)
        if 'comment' in ret:
            ret['comment'] += '\n{0}{2}{3}{1}\n'.format(
                _colors(color), _colors('ENDC'), summary, colon)
    if body:
        rbody = '\n{0}\n'.format(body)
        ret['comment'] += rbody
        if 'raw_comment' in ret:
            ret['raw_comment'] += rbody

    return ret


def _color_log(msg, color, exact=False):
    return "{0}{1}{2}".format(_colors(color, exact=exact),
                              __salt__['mc_utils.magicstring'](msg),
                              _colors('ENDC', exact=exact))


def _append_separator(ret, separator='--', separator_color='LIGHT_CYAN'):
    if 'raw_comment' not in ret:
        ret['raw_comment'] = ''
    if separator:
        ret['raw_comment'] += '\n{0}'.format(separator)
        ret['comment'] += '\n{0}{2}{1}\n'.format(
            _colors(separator_color), _colors('ENDC'), separator)


def _step_exec(cfg, step, failhard=True):
    # be sure of the current project beeing loaded in the context
    name = cfg['name']
    sls = 'makina-projects.{0}.{1}'.format(name, step)
    skip_flag = 'skip_{0}'.format(step)
    skipped = cfg.get(skip_flag, False)
    # XXX: REMOVE ME after tests !!! (False)
    # skipped = False
    if skipped:
        cret = _get_ret(name)
        cret.update({'result': True,
                     'comment': (
                         'Warning: Step {0} for project '
                         '{1} was skipped').format(step, name),
                     'return': None,
                     'name': name})
    else:
        cret = _sls_exec(name, cfg, sls)
    _force_cli_retcode(cret)
    if failhard:
        _check_proc(
            'Deploy step "{0}" for project "{1}" failed, '
            'we can not continued'.format(step, name), step, cret)
    return _filter_ret(cret, cfg['raw_console_return'])


def get_default_configuration(remote_host=None):
    conf = copy.deepcopy(DEFAULT_CONFIGURATION)
    this_host = this_localhost = socket.getfqdn()
    this_port = 22
    if os.path.exists('/this_port'):
        with open('/this_port') as fic:
            this_port = fic.read().splitlines()[0].strip()
    if os.path.exists('/this_host'):
        with open('/this_host') as fic:
            this_host = fic.read().splitlines()[0].strip()
    if not remote_host:
        remote_host = __grains__['fqdn']
    if __salt__['mc_cloud.is_vm']():
        this_host, this_port = __salt__['mc_cloud_vm.vm_host_and_port']()
    conf['remote_host'] = remote_host
    conf['this_host'] = this_host
    conf['this_localhost'] = this_localhost
    conf['this_port'] = this_port
    return conf


def _prepare_configuration(name, *args, **kwargs):
    _s = __salt__
    _g = __grains__
    if not kwargs.get('remote_host', None):
        kwargs.pop('remote_host', None)
    cfg = _get_contextual_cached_project(
        name, remote_host=kwargs.get('remote_host', None))
    if cfg.get('cfg_is_prepared'):
        return cfg
    cfg['name'] = name
    cfg['minion_id'] = _g['id']
    cfg['fqdn'] = _g['fqdn']
    cfg.update(dict([a for a in kwargs.items() if a[0] in cfg]))
    # we must also ignore keys setted on the call to the function
    # which are explictly setting a value
    ignored_keys = ['data', 'rollback']
    for k in kwargs:
        if k in cfg:
            ignored_keys.append(k)
    salt_settings = _s['mc_salt.settings']()
    # special symlinks inside salt wiring
    cfg['wired_salt_root'] = os.path.join(
        salt_settings['salt_root'], 'makina-projects', cfg['name'])
    cfg['wired_pillar_root'] = os.path.join(
        salt_settings['pillar_root'], 'makina-projects', cfg['name'])
    # check if the specified sls installer files container
    if not cfg['default_env']:
        # one of:
        # - makina-projects.fooproject.default_env
        # - fooproject.default_env
        # - default_env
        default_env = __salt__['mc_env.settings']()['env']
        cfg['default_env'] = _s['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(name, 'default_env'),
            _s['mc_utils.get']('{0}.{1}'.format(name, 'default_env'),
                               default_env))

    # set default skippped steps on a specific environment
    # to let them maybe be overriden in pillar
    skipped = {}
    for step in STEPS:
        defaultskip = {
            'notify': True,
            'default': False
        }
        ignored_keys.append('skip_{0}'.format(step))
        skipped['skip_{0}'.format(step)] = kwargs.get(
            'skip_{0}'.format(step),
            defaultskip.get(step, defaultskip['default']))
    only = kwargs.get('only', cfg.get('only', None))
    if only:
        if isinstance(only, basestring):
            only = only.split(',')
        if not isinstance(only, list):
            raise ValueError('invalid only for {1}: {0}'.format(
                only, cfg['name']))
    if only:
        forced = ['skip_deploy'] + ['skip_{0}'.format(o) for o in only]
        for s in [a for a in skipped]:
            if not skipped[s] and s not in forced:
                skipped[s] = True
        for s in forced:
            skipped[s] = False
    cfg.update(skipped)
    #
    if not cfg['user']:
        cfg['user'] = '{name}-user'
    # retro compat, let default_group beeing editor on old prods
    default_group = _s['mc_usergroup.settings']()['group']
    locs = _s['mc_locations.settings']()
    tddir = '{1}/{0}'.format(name, locs['projects_dir'])
    search_editor_dirs = [
        tddir,
        os.path.join(tddir, 'archives'),
        os.path.join(tddir, 'git'),
        os.path.join(tddir, 'data'),
        os.path.join(tddir, 'project')
    ]
    for ddir in search_editor_dirs:
        try:
            st = os.stat(ddir)
            uses_editor = 'editor' == grp.getgrgid(st.st_gid).gr_name
        except (OSError, TypeError, KeyError):
            uses_editor = False
        if uses_editor:
            break
    if not uses_editor:
        default_group = '{name}-grp'
    if default_group not in cfg['groups']:
        cfg['groups'].append(default_group)
    cfg['groups'] = uniquify(cfg['groups'])
    # those variables are overridable via pillar/grains
    overridable_variables = ['default_env',
                             'keep_archives',
                             'no_user',
                             'no_default_includes']

    # we can override many of default values via pillar
    for k in overridable_variables:
        if k in ignored_keys:
            continue
        cfg[k] = _s['mc_utils.get']('{0}:{1}'.format(name, k), cfg[k])
    try:
        cfg['keep_archives'] = int(cfg['keep_archives'])
    except (TypeError, ValueError, KeyError):
        cfg['keep_archives'] = projects_api.KEEP_ARCHIVES
    cfg['ignored_keys'] = ignored_keys
    cfg['cfg_is_prepared'] = True
    return cfg


def load_sample(cfg, *args, **kwargs):
    '''
    Load the project PILLAR.sample back to the cfg
    configuration dict
    '''
    # load sample if present
    if isinstance(cfg, six.string_types):
        cfg = _prepare_configuration(cfg, *args, **kwargs)
    _s = __salt__
    sample = os.path.join(cfg['wired_salt_root'], 'PILLAR.sample')
    sample_data = OrderedDict()
    sample_data_l = OrderedDict()
    if os.path.exists(sample):
        sample_data_l = __salt__['mc_utils.sls_load'](sample)
        sample_data['sls_default_pillar'] = copy.deepcopy(sample_data_l)
        try:
            # sample_data_l = __salt__['mc_utils.cyaml_load'](fic.read())
            if not isinstance(sample_data_l, dict):
                sample_data_l = OrderedDict()
            for k, val in sample_data_l.items():
                # retro compat
                retro = k.startswith('makina-states.') and (k.count('.') < 2)
                # only load first level makina-projects. sections
                if not retro and not k.startswith('makina-projects.'):
                    continue
                if isinstance(val, dict):
                    for k2, val2 in val.items():
                        if isinstance(val2, dict):
                            incfg = sample_data.setdefault(k2, OrderedDict())
                            incfg = _s['mc_utils.dictupdate'](incfg, val2)
                        else:
                            sample_data[k2] = val2
                else:
                    sample_data[k] = val
        except (yaml.error.YAMLError, salt.exceptions.SaltException):
            trace = traceback.format_exc()
            error = (
                '{0}\n{1} is not a valid YAML File for {2}'.format(
                    trace, sample, cfg['name']))
            log.error(error)
            raise ValueError(error)
        except (Exception,):
            trace = traceback.format_exc()
            log.error(trace)
            sample_data = OrderedDict()
            cfg['force_reload'] = True
    return sample_data


def _defaultsConfiguration(
    cfg,
    default_env,
    defaultsConfiguration=None,
    env_defaults=None,
    os_defaults=None
):
    _s = __salt__
    if defaultsConfiguration is None:
        defaultsConfiguration = {}
    sample = load_sample(cfg)
    defaultsConfiguration.update(sample)
    _dict_update = _s['mc_utils.dictupdate']
    if os_defaults is None:
        os_defaults = OrderedDict()
    if env_defaults is None:
        env_defaults = OrderedDict()
    sample_env_defaults = sample.get('env_defaults', OrderedDict())
    if isinstance(sample_env_defaults, dict):
        env_defaults = _dict_update(env_defaults, sample_env_defaults)
    env_defaults = _dict_update(
        env_defaults,
        copy.deepcopy(
            _s['mc_utils.get'](
                'makina-projects.{name}.env_defaults'.format(**cfg),
                OrderedDict())))
    env_defaults = _dict_update(
        env_defaults,
        copy.deepcopy(
            _s['mc_utils.get'](
                'makina-projects.{name}'.format(**cfg),
                OrderedDict()
            ).get('env_defaults', OrderedDict())))
    if not os_defaults:
        os_defaults = _dict_update(
            os_defaults,
            copy.deepcopy(
                _s['mc_utils.get'](
                    'makina-projects.{name}.os_defaults'.format(**cfg),
                    OrderedDict())))
        os_defaults = _dict_update(
            os_defaults,
            copy.deepcopy(
                _s['mc_utils.get'](
                    'makina-projects.{name}'.format(**cfg),
                    OrderedDict()
                ).get('os_defaults', OrderedDict())))

    pillar_data = OrderedDict()
    # load pillar prefix makina-states.projectname and
    # makina-projects.projectname
    # makina-states is the old prefix, retro compat
    for subp in ['states', 'projects']:
        for subk in [a for a in cfg]:
            val = _s['mc_utils.get'](
                        'makina-{subp}.{name}.{subk}'.format(
                            name=cfg['name'], subk=subk, subp=subp),
                        _MARKER)
            if val is not _MARKER:
                pillar_data[subk] = val
            else:
                val = _s['mc_utils.get'](
                    'makina-{subp}.{name}'.format(
                        name=cfg['name'], subp=subp),
                    OrderedDict()
                ).get(subk, _MARKER)
                if val is not _MARKER:
                    pillar_data[subk] = val
    default_env = pillar_data.get('default_env', None) or default_env
    os_defaults.setdefault(__grains__['os'], OrderedDict())
    os_defaults.setdefault(__grains__['os_family'],
                           OrderedDict())
    env_defaults.setdefault(default_env, OrderedDict())
    for k in projects_api.ENVS:
        env_defaults.setdefault(k, OrderedDict())
    defaultsConfiguration = _dict_update(
        defaultsConfiguration, pillar_data)
    if default_env in env_defaults:
        defaultsConfiguration['data'] = _dict_update(
            defaultsConfiguration['data'],
            env_defaults[default_env])
        cfg['default_env'] = default_env
    defaultsConfiguration = _dict_update(
        defaultsConfiguration,
        _s['grains.filter_by'](os_defaults, grain='os_family'))
    prefs = [
        # retro compat 'foo-default-settings'
        '{name}-default-settings'.format(**cfg),
        # new location 'makina-projects.foo.data'
        'makina-projects.{name}.data'.format(**cfg)]
    for pref in prefs:
        defaultsConfiguration = copy.deepcopy(
            _s['mc_utils.defaults'](
                pref, defaultsConfiguration, noresolve=True))
    return defaultsConfiguration


def _merge_statuses(ret, cret, step=None):
    for d in ret, cret:
        if 'raw_comment' not in d:
            d['raw_comment'] = ''
    merge_comment = True
    if 'comment' in cret:
        if not (cret['comment'] and cret['comment'].strip()):
            merge_comment = False
    if merge_comment:
        _append_separator(ret)
    if cret['result'] is False:
        ret['result'] = False
    if cret is ret:
        merge_comment = False
    if cret.get('changes', {}) and ('changes' in ret):
        ret['changes'].update(cret)
    if merge_comment and bool(step):
        ret['comment'] += '\n{3}Execution step:{2} {1}{0}{2}'.format(
            step, _colors('YELLOW'), _colors('ENDC'), _colors('RED'))
        ret['raw_comment'] += '\nExecution step: {0}'.format(cret)
    for k in ['raw_comment', 'comment']:
        if merge_comment and (k in cret):
            try:
                ret[k] += '\n{{{0}}}'.format(k).format(**cret)
            except UnicodeEncodeError:
                if isinstance(cret[k], unicode):
                    ret[k] += cret[k].encode('utf-8')
                else:
                    ret[k] += cret[k].decode('utf-8').encode('utf-8')
    if not ret['result']:
        _append_comment(ret,
                        summary='Deployment aborted due to error',
                        color='RED')
    return ret


def _init_context(name=None, remote_host=None):
    if 'ms_projects' not in __opts__:
        __opts__['ms_projects'] = OrderedDict()
    if 'ms_project' not in __opts__:
        __opts__['ms_project'] = None
    __opts__['ms_project_name'] = None


def set_project(cfg):
    _init_context(cfg.get('name', None))
    __opts__['ms_project'] = cfg
    __opts__['ms_project_name'] = cfg['name']
    __opts__['ms_projects'][(cfg['name'], cfg['remote_host'])] = cfg
    return cfg


def uncache_project(name):
    '''Uncache a configuration after an initial load
    either by it's name or by its structure'''
    if isinstance(name, dict):
        name = name['name']
    __opts__.get('ms_projects', {}).pop(name, None)
    __opts__.pop('ms_project_name', None)
    projects = __opts__.get('ms_projects', {})
    for cfg, remote_host in [a for a in projects]:
        if cfg == name:
            projects.pop((cfg, remote_host), None)


def get_project(name, *args, **kwargs):
    '''
    Alias of get_configuration for convenience
    '''
    return get_configuration(name, *args, **kwargs)


def _get_contextual_cached_project(name, remote_host=None):
    _init_context(name=name, remote_host=remote_host)
    # throw KeyError if not already loaded
    key = (name, remote_host)
    try:
        cfg = __opts__['ms_projects'][key]
    except KeyError:
        dcfg = get_default_configuration(remote_host=remote_host)
        cfg = __opts__['ms_projects'].setdefault(key, dcfg)
    remote_host = cfg['remote_host']
    if remote_host == __grains__['fqdn']:
        __opts__['ms_project'] = cfg
        __opts__['ms_project_name'] = cfg['name']
    __context__['ms_project'] = __opts__['ms_project']
    __context__['ms_projects'] = __opts__['ms_projects']
    return cfg


def get_configuration(name, *args, **kwargs):
    '''
    Return a configuration data structure needed data for
    the project API macros and configurations functions
    project API 2

    name
        name of the project
    remote_less
        Does the project use local remotes (via git hooks) for users
        to push code inside remotes and have the local working copy
        synchronized with those remotes before deploy.
        Default to True, set to False to use local remotes
        If the project directory .git folder exists, and there
        is no local remote created, the local remotes feature
        will also be disabled
    fqdn
        fqdn of the box
    minion_id
        minion_id of the box
    default_env
        environnemt to run into (may be dev|prod, better
        to set a grain see bellow)
    project_root
        where to install the project,
    git_root
        root dir for git repositories
    user
        system project user
    groups
        system project user groups, first group is main
    defaults
        arbitrary data mapping for this project to use in states.
        It will be accessible throught the get_configuration().data var
    env_defaults
        per environment (eg: prod|dev) specific defaults data to override or
        merge inside the defaults one
    os_defaults
        per os (eg: Ubuntu/Debian) specific defaults data to override or merge
        inside the defaults one

    only_install
        Only run the install step (make the others skipped)
    skip_archive
        Skip the archive step
    skip_release_sync
        Skip the release_sync step
    skip_install
        Skip the install phase
    skip_rollback
        Skip the rollback step if any
    skip_notify
        Skip the notify step if any

    Any other kwarg is added to the data dict.

    Internal variables reference

        pillar_root
            pillar local dir
        salt_root
            salt local dir
        archives_root
            archives directory
        data_root
            persistent data root
        project_git_root
            project local git dir
        pillar_git_root
            pillar local git dir
        nodata
            do not compute data
        data
            The final mapping where all defaults will be mangled.
            If you want to add extra parameters in the configuration, you d
            better have to add them to defaults.
        force_reload
            if the project configuration is already present in the context,
            reload it anyway
        sls_includes
            includes to add to the project top includes statement
        no_default_includes
            Do not add salt_minon & other bases sls
            like ssh to default includes
        rollback
            FLAG: do we rollback at the end of all processes

    You can override the non read only default variables
    by pillar/grain like::

        salt grain.setval makina-projects.foo.url 'http://goo/goo.git
        salt grain.setval makina-projects.foo.default_env prod

    You can override the non read only default arbitrary attached defaults
    by pillar/grain like::

        /srv/projects/foo/pillar/init.sls:

        makina-projects.foo.data.conf_port = 1234

    '''
    cfg = _prepare_configuration(name, *args, **kwargs)
    to_reload = (cfg.get('force_reload', None) or
                 kwargs.get('force_reload', None))
    if cfg.get('cfg_is_loaded'):
        if to_reload:
            uncache_project(cfg['name'])
            cfg = _prepare_configuration(name, *args, **kwargs)
            cfg['force_reload'] = True
        else:
            return cfg
    _s = __salt__
    salt_settings = _s['mc_salt.settings']()
    salt_root = salt_settings['salt_root']
    nodata = kwargs.pop('nodata', False)
    ignored_keys = cfg['ignored_keys']
    if nodata:
        cfg['data'] = OrderedDict()
    else:
        cfg.update(
            _defaultsConfiguration(
                cfg,
                cfg['default_env'],
                defaultsConfiguration=cfg['defaults'],
                env_defaults=cfg['env_defaults'],
                os_defaults=cfg['os_defaults']))
    if cfg['data'].get('sls_default_pillar', OrderedDict()):
        cfg['sls_default_pillar'] = cfg['data'].pop('sls_default_pillar')
    # some vars need to be setted just a that time
    cfg['group'] = cfg['groups'][0]
    cfg['projects_dir'] = _s['mc_locations.settings']()['projects_dir']
    cfg['remote_projects_dir'] = _s[
        'mc_locations.settings']()['remote_projects_dir']

    # we can try override default values via pillar/grains a last time
    # as format_resolve can have setted new entries
    # we do that only on the global data level and on non read only vars
    if 'data' not in ignored_keys:
        ignored_keys.append('data')
    cfg.update(
        _s['mc_utils.defaults'](
            'makina-projects.{0}'.format(name),
            cfg, ignored_keys=ignored_keys, noresolve=True))
    # add/override data parameters via arguments given on cmdline
    for k in [a for a in kwargs
              if not a.startswith('__pub') and
              a not in [b for b in DEFAULT_CONFIGURATION]]:
        cfg['data'][k] = kwargs[k]
    # finally resolve the format-variabilized dict key entries in
    # arbitrary conf mapping
    cfg['data'] = _s['mc_utils.format_resolve'](cfg['data'])
    cfg['data'] = _s['mc_utils.format_resolve'](cfg['data'], cfg)

    # finally resolve the format-variabilized dict key entries in global conf
    # the default pillar will also recursively be resolved here
    cfg.update(_s['mc_utils.format_resolve'](cfg))
    cfg.update(_s['mc_utils.format_resolve'](cfg, cfg['data']))

    if cfg['group'] not in cfg['groups']:
        cfg['groups'].insert(0, cfg['group'])

    if cfg['remote_less'] is None:
        cfg['remote_less'] = is_remote_less(cfg)

    now = datetime.datetime.now()
    cfg['chrono'] = '{0}_{1}'.format(
        datetime.datetime.strftime(now, '%Y-%m-%d_%H_%M-%S'),
        str(uuid.uuid4()))
    cfg['current_archive_dir'] = os.path.join(
        cfg['archives_root'], cfg['chrono'])

    # exists
    if '/' not in cfg['installer']:
        installer_path = os.path.join(
            salt_root, 'makina-states/projects/{0}/{1}'.format(
                cfg['api_version'], cfg['installer']))
    # check for all sls to be in there
    cfg['installer_path'] = installer_path
    # put the result inside the context
    cfg['force_reload'] = False
    if not nodata and not (cfg['remote_host'] == __grains__['fqdn']):
        set_project(cfg)
    cfg['cfg_is_loaded'] = True
    return cfg


def _get_filtered_cfg(cfg):
    ignored_keys = ['data',
                    'name',
                    'salt_root',
                    'rollback']
    to_save = {}
    for sk in cfg:
        val = cfg[sk]
        if sk.startswith('skip_'):
            continue
        if sk.startswith('__pub'):
            continue
        if sk in ignored_keys:
            continue
        if isinstance(val, OrderedDict) or isinstance(val, dict):
            continue
        to_save[sk] = val
    return to_save


def set_configuration(name, cfg=None, *args, **kwargs):
    '''
    set or update a local (grains) project configuration
    '''
    if not cfg:
        cfg = get_configuration(name, *args, **kwargs)
    local_conf = __salt__['mc_macros.get_local_registry'](
        'makina_projects', registry_format='pack')
    local_conf[name] = _get_filtered_cfg(cfg)
    # saved registry is now deactivated to simplify things
    # __salt__['mc_macros.update_local_registry'](
    #     'makina_projects', local_conf, registry_format='pack')
    return get_configuration(name)


def get_configuration_item(project, item=_MARKER, **kw):
    '''
    Return an item, maybe filtered or all the config

    in the form::

        {key: <itemKey or 'cfg'>, item: VALUE, cfg: <Whole config dict>}

    CLI examples::

        salt-call --local\
                mc_project_2.get_configuration_item eee git_deploy_hook
        salt-call --local\
                mc_project_2.get_configuration_item eee

    '''
    cfg = get_configuration(project, **kw)
    if item is _MARKER:
        val = cfg
        key = 'cfg'
    else:
        key = item
        val = cfg.get(key, cfg['data'].get(key))
        if key in ['git_deploy_hook']:
            if not os.path.exists(val):
                val = False
    return {'item': val, 'cfg': cfg, 'key': key}


def is_pillar_remote_less(cfg):
    no_remote = (
        (os.path.exists(J(cfg['pillar_root'], '.git')) or
         os.path.exists(J(cfg['pillar_root'], 'init.sls')))and
        not os.path.exists(cfg['pillar_git_root']))
    return no_remote


def is_remote_less(cfg):
    # in makinastates v1 layouts, remoteless is False by default
    remote_less = cfg.get('remote_less', None) or (
        (os.path.exists(J(cfg['project_root'], '.git')) or
         os.path.exists(J(cfg['project_root'], '.salt'))) and
        not os.path.exists(cfg['project_git_root']))
    # if we found remote layout, deactivate remote less
    if (
        os.path.exists(cfg['project_git_root']) and
        os.path.exists(cfg['pillar_git_root'])
    ):
        remote_less = False
    # by default on v2 and later projects, remoteless is now the
    # default
    elif remote_less is None and LooseVersion(VERSION) >= LooseVersion("2.0"):
        remote_less = True
    return remote_less


def init_user_groups(user, groups=None, ret=None):
    _append_comment(
        ret, summary='Verify user:{0} & groups:{1} for project'.format(
            user, groups))
    _s = __salt__
    if not groups:
        groups = []
    if not ret:
        ret = _get_ret(user)
    # create user if any
    for g in groups:
        if not _s['group.info'](g):
            cret = _state_exec(sgroup, 'present', g, system=True)
            if not cret['result']:
                raise projects_api.ProjectInitException(
                    'Can\'t manage {0} group'.format(g))
            else:
                _append_comment(ret, body=indent(cret['comment']))
    if not os.path.exists('/home/users'):
        os.makedirs('/home/users')
        os.chmod('/home/users', 0755)
    if not _s['user.info'](user):
        cret = _state_exec(suser, 'present',
                           user,
                           home='/home/users/{0}'.format(user),
                           shell='/bin/bash',
                           gid_from_name=True,
                           remove_groups=False,
                           optional_groups=groups)
        if not cret['result']:
            raise projects_api.ProjectInitException(
                'Can\'t manage {0} user'.format(user))
        else:
            _append_comment(ret, body=indent(cret['comment']))
    return ret


def init_project_dirs(cfg, ret=None):
    _s = __salt__
    if not ret:
        ret = _get_ret(cfg['name'])
    _append_comment(ret, summary=(
        'Initialize or verify core '
        'project layout for {0}').format(cfg['name']))
    # create various directories
    dirs = [(cfg['archives_root'], '770'),
            (os.path.dirname(cfg['wired_pillar_root']), '770'),
            (os.path.dirname(cfg['wired_salt_root']), '770'),
            (cfg['data_root'], '770')]
    if not cfg['remote_less']:
        dirs.insert(0, (cfg['git_root'], '770'))
    for dr, mode in dirs:
        cret = _state_exec(sfile,
                           'directory',
                           dr,
                           makedirs=True,
                           user=cfg['user'],
                           group=cfg['group'],
                           mode='750')
        if not cret['result']:
            raise projects_api.ProjectInitException(
                'Can\'t manage {0} dir'.format(dr))
    for symlink, target in (
        (cfg['wired_salt_root'], cfg['salt_root']),
        (cfg['wired_pillar_root'], cfg['pillar_root']),
    ):
        cret = _state_exec(sfile, 'symlink', symlink, target=target)
        if not cret['result']:
            raise projects_api.ProjectInitException(
                'Can\'t manage {0} -> {1} symlink\n{2}'.format(
                    symlink, target, cret))
    return ret


def init_ssh_user_keys(user, failhard=False, ret=None):
    '''
    Copy root keys from root to a user
    to allow user to share the same key than root to clone distant repos.
    This is useful in vms (local PaaS vm)
    '''
    _append_comment(
        ret, summary='SSH keys management for {0}'.format(user))
    cmd = '''
home="$(awk -F: -v v="{user}" '{{if ($1==v && $6!="") print $6}}'\
        /etc/passwd)";
cd /root/.ssh;
chown {user} $home;
if [ ! -e $home/.ssh ];then
  mkdir $home/.ssh;
fi;
for i in config id_*;do
  if [ ! -e $home/.ssh/$i ];then
    cp -fv $i $home/.ssh;
  fi;
done;
chown -Rf {user}:{user} $home/.ssh;
chmod -Rf 700 $home/.ssh/*;
echo;echo "changed=false comment='do no trigger changes'"
'''.format(user=user)
    onlyif = '''res=1;
home="$(awk -F: -v v="{user}" '{{if ($1==v && $6!="") print $6}}'\
        /etc/passwd)";
cd /root/.ssh;
if [ "x$(stat -c %U "$home")" != "x$user" ];then
    res=0
fi
for i in config id_*;do
  if [ ! -e $home/.ssh/$i ];then
    res=0;
  fi;
done;
exit $res;'''.format(user=user)
    if not ret:
        ret = _get_ret(user)
    _s = __salt__
    cret = _state_exec(scmd, 'run', cmd, onlyif=onlyif, stateful=True)
    if failhard and not cret['result']:
        raise projects_api.ProjectInitException('SSH keys improperly configured\n'
                                   '{0}'.format(cret))
    return ret


def sync_hooks(name, ret=None, api_version=API_VERSION, *args, **kwargs):
    _s = __salt__
    cfg = get_configuration(name, *args, **kwargs)
    user, groups, group = cfg['user'], cfg['groups'], cfg['group']
    if not ret:
        ret = _get_ret(cfg['name'])
    local_remote = cfg['project_git_root']
    project_git = os.path.join(cfg['project_root'], '.git')
    ms = _s['mc_locations.settings']()['ms']
    params = {
        'WC': ms,
        'FORCE_MARKER': local_remote+'/hooks/force_marker',
        'api_version': api_version, 'name': name}
    if not cfg.get('remote_less', False):
        cret = _state_exec(
            sfile, 'managed',
            name=os.path.join(local_remote, 'hooks/pre-receive'),
            source=(
                'salt://makina-states/files/projects/2/'
                'hooks/pre-receive'),
            defaults=params,
            user=user, group=group, mode='750', template='jinja')
        cret = _state_exec(
            sfile, 'managed',
            name=os.path.join(local_remote, 'hooks/post-receive'),
            source=(
                'salt://makina-states/files/projects/2/'
                'hooks/post-receive'),
            defaults=params,
            user=user, group=group, mode='750', template='jinja')
        cret = _state_exec(
            sfile, 'managed',
            name=os.path.join(local_remote, 'hooks/deploy_hook.py'),
            source=(
                'salt://makina-states/files/projects/2/'
                'hooks/deploy_hook.py'),
            defaults=params,
            user=user, group=group, mode='750')
        cret = _state_exec(
            sfile, 'managed',
            name=os.path.join(project_git, 'hooks/pre-push'),
            source=(
                'salt://makina-states/files/projects/2/'
                'hooks/pre-push'),
            template='jinja',
            defaults=params,
            user=user, group=group, mode='750')
        if not cret['result']:
            raise projects_api.ProjectInitException(
                'Can\'t set git hooks for {0}\n{1}'.format(name, cret['comment']))
        else:
            _append_comment(
                ret, summary='Git Hooks for {0}'.format(name))
    return ret


def get_contextual_cfg_defaults(configs, project=None, remote_host=None):
    thishost = __grains__['fqdn']
    for data in configs:
        if isinstance(data, dict):
            if not project:
                project = data.get('name', None)
            rhost = data.get('remote_host', thishost)
            if (
                (remote_host is None)
                and rhost
                and (rhost  != thishost)
            ):
                remote_host = rhost
    project = get_default_project(project)
    return {'remote_host': remote_host,
            'project': project}


def init_repo(working_copy,
              user=None,
              group=None,
              ret=None,
              bare=True,
              init_salt=False,
              init_pillar=False,
              init_data=None,
              project=None,
              remote_host=None,
              cfg=None,
              remote_less=False,
              api_version=API_VERSION):
    '''
    Initialize an empty git repository, either bare or a working copy

    This can be either:

        - a basic corpus-salt base project template
        - a pillar repo (containing an init.sls)
        - an enmpty directory (containing an empty .empty file just
          for git repo init)

    CLI Examples::

         salt-call --local mc_project.init_repo /foo
         salt-call --local mc_project.init_repo /foo bare=true
         salt-call --local mc_project.init_repo /foo init_salt=True
         salt-call --local mc_project.init_repo /foo init_pillar=True
         salt-call --local mc_project.init_repo /foo bare=true init_salt=True
         salt-call --local mc_project.init_repo /foo bare=true init_pillar=True
    '''
    user, group = get_default_user_group(user=user, group=group)
    _s = __salt__
    # seek project name & remote host
    infos = get_contextual_cfg_defaults(
        [init_data, cfg], project=project, remote_host=remote_host)
    project = infos['project']
    remote_host = infos['remote_host']
    if cfg is None:
        cfg = get_configuration(project, remote_host=remote_host)
    if init_data is None:
        init_data = cfg
    if not ret:
        ret = _get_ret(user)
    pref = 'Bare r'
    if not bare:
        pref = 'R'
    _append_comment(
        ret, summary='{1}epository managment in {0}'.format(working_copy,
                                                            pref))
    lgit = working_copy
    if not bare:
        lgit = os.path.join(lgit, '.git')
    if os.path.exists(lgit):
        cmd = 'chown -Rf {0} "{2}"'.format(user, group, working_copy)
        cret = _s['cmd.run_all'](cmd, python_shell=True)
        if cret['retcode']:
            raise projects_api.ProjectInitException(
                'Can\'t set perms for {0}'.format(working_copy))
    parent = os.path.dirname(working_copy)
    cret = _state_exec(sfile, 'directory',
                       parent,
                       makedirs=True,
                       user=user,
                       group=group,
                       mode='770')
    if not cret['result']:
        raise projects_api.ProjectInitException(
            'Can\'t manage {0} dir'.format(working_copy))
    cret = _state_exec(sgit,
                       'present',
                       working_copy,
                       user=user,
                       bare=bare,
                       force=True)
    if not cret['result']:
        raise projects_api.ProjectInitException(
            'Can\'t manage {0} dir'.format(working_copy))
    create = False
    if len(os.listdir(lgit + '/refs/heads')) < 1:
        cret = git_log(lgit, user=user)
        commits = [a for a in cret.splitlines() if a.startswith('commit ')]
        if len(commits) > 1:
            create = False
        else:
            create = True
    if create:
        if init_salt and init_pillar:
            raise ValueError(
                'init_salt and init_pillar are mutually exclusive')
        igit = working_copy
        if bare:
            igit += '.tmp'
        if remote_less:
            igit = lgit
        try:
            parent = os.path.dirname(igit)
            if not os.path.exists(parent):
                _s['file.makedirs_perms'](
                    parent, user=user, group=group, mode=0750)
            _s['file.set_mode'](parent, 0750)
            _s['file.chown'](parent, user=user, group=group)
            if not os.path.exists(os.path.join(igit, '.git')):
                _s['git.init'](igit, user=user)
            _s['file.set_mode'](igit, 0750)
            _s['file.chown'](igit, user=user, group=group)
            empty = os.path.join(igit, '.empty')
            if not remote_less:
                _s['git.remote_set'](
                    igit, remote='origin', url=working_copy, user=user)
            if bare:
                set_makina_states_author(igit, user=user)
            if init_salt:
                refresh_files_in_working_copy(igit,
                                              user=user,
                                              group=group,
                                              project=project,
                                              init_data=cfg,
                                              force=True,
                                              commit_all=False,
                                              do_push=False,
                                              remote_less=remote_less,
                                              api_version=api_version)
            elif init_pillar:
                init_pillar_dir(
                    igit,
                    init_data=cfg,
                    project=project,
                    user=user,
                    commit_all=False,
                    bare=bare,
                    do_push=False,
                    api_version=api_version,
                    remote_less=remote_less,
                    ret=ret)
            else:
                if not os.path.exists(empty):
                    _s['file.touch'](empty)
                    _s['file.chown'](empty, user, group)
            set_makina_states_author(igit, user=user)
            git_commit(igit, message=INITIAL_COMMIT_MESSAGE,
                       commit_all=True, opts='-f', user=user)
            if bare and not remote_less:
                _s['git.push'](
                    cwd=igit, remote='origin', ref='master:master',
                    opts='--force -u', user=user)
        except Exception:
            log.error(traceback.format_exc())
            raise projects_api.ProjectInitException(
                'Can\'t create init layout in {0}'.format(working_copy))
        finally:
            if bare and (igit != lgit) and (igit != working_copy):
                cret = _s['cmd.run_all']('rm -rf "{0}"'.format(igit),
                                         runas=user)
    return ret


def push_changesets_in(directory,
                       remote='origin',
                       branch="master:master",
                       opts='',
                       **kw):
    '''
    Thin wrapper to git push

        directory
            directory where to act on
        user
            user to push as
        branch
            branch part of the git command
        remote
            remote to push to
        opts
            'origin',
            opts to give

    CLI Examples::

        salt-call --local  mc_project.push_changesets_in /foo
        salt-call --local  mc_project.push_changesets_in /foo opts="-f"
        salt-call --local  mc_project.push_changesets_in /foo opts="-f"
    '''
    user, group = get_default_user_group(**kw)
    try:
        return __salt__['git.push'](
            cwd=directory,
            remote=remote,
            ref=branch,
            opts=opts,
            user=user
        )
    except Exception:
        trace = traceback.format_exc()
        raise projects_api.ProjectInitException(
            'Can\'t push first salt commit in {0}\n{1}'.format(
                directory, trace))


def git_commit(git,
               message=DEFAULT_COMMIT_MESSAGE,
               opts=None,
               commit_all=False,
               commit_opts=None,
               **kw):
    _s = __salt__
    user, group = get_default_user_group(**kw)
    if not opts:
        opts = ''
    if not commit_opts:
        commit_opts = ''
    cret = None
    try:
        if commit_all:
            _s['git.add'](cwd=git, filename='.', opts=opts, user=user)
        status = _s['cmd.run']('git status',
                               env={'LANG': 'C', 'LC_ALL': 'C'},
                               runas=user,
                               cwd=git)
        if 'nothing to commit, working directory clean' not in status:
            cret = _s['git.commit'](git, message, opts=commit_opts, user=user)
    except Exception:
        trace = traceback.format_exc()
        raise projects_api.ProjectInitException(
            'Can\'t commit salt commit in {0}\n{1}'.format(
                git, trace))
    return cret


def init_local_repository(wc, url, user, group, ret=None):
    _s = __salt__
    _append_comment(
        ret, summary='Local git repository initialization in {0}'.format(wc))
    if not ret:
        ret = _get_ret(user)
    parent = os.path.dirname(wc)
    cret = _state_exec(sfile, 'directory',
                       parent,
                       makedirs=True,
                       user=user,
                       group=group,
                       mode='770')
    if not cret['result']:
        raise projects_api.ProjectInitException(
            'Can\'t manage {0} dir'.format(wc))
    else:
        _append_comment(ret, body=indent(cret['comment']))
    # initialize an empty git for pillar & project
    cret = _state_exec(sgit, 'present',
                       wc,
                       bare=False,
                       user=user,
                       force=True)
    if not cret['result']:
        raise projects_api.ProjectInitException(
            'Can\'t initialize git dir  {0} dir'.format(wc))


def set_git_remote(wc, user, localgit, remote='origin', ret=None):
    _s = __salt__
    _append_comment(
        ret, summary=('Set remotes in local copy {0} -> {1}'.format(
            localgit, wc)))
    if not ret:
        ret = _get_ret(user)
    # add the local and distant remotes
    cret = _s['git.remote_set'](localgit, remote=remote, url=wc, user=user)
    if not cret:
        raise projects_api.ProjectInitException(
            'Can\'t initialize git local remote '
            '{0}  in {2}'.format(
                remote, wc))
    return ret


def fetch_last_commits(wc, user, origin='origin', ret=None):
    _s = __salt__
    if not ret:
        ret = _get_ret(user)
    _append_comment(
        ret, summary=('Fetch last commits from {1} '
                      'in working copy: {0}'.format(
                          wc, origin)))
    cret = _s['cmd.run_all'](
        'git fetch {0}'.format(origin), cwd=wc, python_shell=True, runas=user)
    if cret['retcode']:
        raise projects_api.ProjectInitException('Can\'t fetch git in {0}'.format(wc))
    cret = _s['cmd.run_all'](
        'git fetch {0} --tags'.format(origin),
        cwd=wc, python_shell=True, runas=user)
    if cret['retcode']:
        raise projects_api.ProjectInitException('Can\'t fetch git tags in {0}'.format(wc))
    return ret


def git_log(wc, user='root'):
    _s = __salt__
    return _s['cmd.run'](
        'git log', env={'LANG': 'C', 'LC_ALL': 'C'},
        cwd=wc, python_shell=True, runas=user)


def has_no_commits(wc, user='root'):
    nocommits = "fatal: bad default revision 'HEAD'" in git_log(wc, user)
    return nocommits


def set_upstream(wc, rev, user, origin='origin', ret=None):
    _s = __salt__
    _append_comment(
        ret, summary=(
            'Set upstream: {2}/{1} in {0}'.format(
                wc, rev, origin)))
    # set branch upstreams
    try:
        sver = _s['cmd.run_all'](
            'git --version', cwd='/', python_shell=True)['stdout'].split()[-1]
        git_ver = float('.'.join(sver.split('.')[:2]))
    except (ValueError, TypeError):
        git_ver = 1.8
    if has_no_commits(wc, user=user):
        cret2 = _s['cmd.run_all'](
            'git reset --hard {1}/{0}'.format(
                rev, origin), cwd=wc, python_shell=True, runas=user)
        if cret2['retcode'] or cret2['retcode']:
            raise projects_api.ProjectInitException(
                'Can\'t reset to initial state in {0}'.format(wc))
    if git_ver < 1.8:
        cret2 = _s['cmd.run_all'](
            'git branch --set-upstream master {1}/{0}'.format(
                rev, origin), cwd=wc, python_shell=True, runas=user)
        cret1 = _s['cmd.run_all'](
            'git branch --set-upstream {0} {1}/{0}'.format(rev, origin),
            cwd=wc, python_shell=True, runas=user)
        if cret2['retcode'] or cret1['retcode']:
            out = splitstrip('{stdout}\n{stderr}'.format(**cret2))
            _append_comment(ret, body=indent(out))
            out = splitstrip('{stdout}\n{stderr}'.format(**cret1))
            _append_comment(ret, body=indent(out))
            raise projects_api.ProjectInitException(
                'Can\'t set upstreams for {0}'.format(wc))
    else:
        cret = _s['cmd.run_all'](
            'git branch --set-upstream-to={1}/{0}'.format(rev, origin),
            cwd=wc, python_shell=True, runas=user)
        if cret['retcode']:
            out = splitstrip('{stdout}\n{stderr}'.format(**cret))
            _append_comment(ret, body=indent(out))
            raise projects_api.ProjectInitException(
                'Can not set upstream from {2} -> {0}/{1}'.format(
                    origin, rev, wc))
    return ret


def working_copy_in_initial_state(wc, **kw):
    '''
    Test if a directory is at the first git commit
    from this system

    wc
        where to execute
    user
        user to act with

    '''
    _s = __salt__
    user, group = get_default_user_group(**kw)
    cret = _s['cmd.run_all'](
        'git log --pretty=format:"%h:%s:%an"',
        cwd=wc, python_shell=True, runas=user)
    out = splitstrip('{stdout}\n{stderr}'.format(**cret))
    lines = out.splitlines()
    initial = False
    if len(lines) >= 1 and lines[0].count(':') == 2:
        parts = lines[0].split(':')
        if DEFAULT_AUTHOR == parts[2] and INITIAL_COMMIT_MESSAGE == parts[1]:
            initial = True
    return initial


def sync_working_copy(wc,
                      rev=None,
                      ret=None,
                      origin=None,
                      reset=False,
                      **kw):
    '''
    Synchronnze a directory with it's git remote

    directory
        directory to execute into
    reset
        force sync with remote
    user
        user to exec commands as and for new files
    rev
        force rev to reset to
    origin
        origin to sync with
    '''
    _s = __salt__
    rev = get_default_rev(rev)
    user, group = get_default_user_group(**kw)
    if origin is None:
        origin = 'origin'
    ret = _get_ret(**kw)
    _append_comment(
        ret, summary=(
            'Synchronise working copy {0} from upstream {2}/{1}'.format(
                wc, rev, origin)))
    initial = working_copy_in_initial_state(wc, user=user)
    nocommits = "fatal: bad default revision 'HEAD'" in _s['cmd.run'](
        'git log', env={'LANG': 'C', 'LC_ALL': 'C'},
        cwd=wc, runas=user)
    force_sync = False
    set_target='{1}/{0}'.format(rev, origin)
    # the local copy is not yet synchronnized with any repo
    if (
        initial or
        reset or
        nocommits or (
            [a for a in os.listdir(wc)
             if a not in ['.git']] == ['.empty']
        )
    ):
        cret = _s['git.reset'](
            wc, opts='--hard {1}/{0}'.format(rev, origin),
            user=user)
        # in dev mode, no local repo, but we sync it anyway
        # to avoid bugs
        if not cret:
            raise projects_api.ProjectInitException(
                'Can not sync from {1}@{0} in {2}'.format(
                    origin, rev, wc))
    else:
        cret = _s['cmd.run_all']('git pull {1} {0}'.format(rev, origin),
                                 cwd=wc, python_shell=True, runas=user)
        if cret['retcode']:
            force_sync = True
        corigin_log = __salt__['cmd.run_all'](
            'git log {0}/{1}'.format(origin, rev),
            python_shell=True, cwd=wc, user=kw['user'])
        if corigin_log['retcode'] != 0:
            raise projects_api.ProjectInitException(
                'Can not get origin log from {0}/{1} in {2}'.format(
                    origin, rev, wc))
        loc_sha1 = __salt__['git.revision'](wc, user=kw['user'])
        origin_sha1 = corigin_log['stdout'].splitlines()[0].split()[1]
        if loc_sha1 != origin_sha1:
            _append_comment(
                ret, summary=(
                    'Synchronise working copy {0}'
                    ' from upstream {2}/{1}@{3}'.format(
                        wc, rev, origin, origin_sha1)))
            set_target = origin_sha1
            force_sync = True
    if force_sync:
        # finally try to reset hard
        cret = _s['cmd.run_all'](
            'git reset --hard {0}'.format(set_target),
            cwd=wc, user=user)
        if cret['retcode']:
            # try to merge a bit but only what's mergeable
            cret = _s['cmd.run_all'](
                'git merge --ff-only {1}/{0}'.format(rev, origin),
                cwd=wc, python_shell=True, runas=user)
            if cret['retcode']:
                raise projects_api.ProjectInitException(
                    'Can not sync from {0}/{1} in {2}'.format(
                        origin, rev, wc))
    return ret


def get_default_project(project):
    if not project:
        project = DEFAULT_PROJECT_NAME
    return project

def get_default_user_group(user=None, group=None, **kw):
    if not user:
        user = 'root'
    if not group:
        group = 'root'
    return user, group


def init_pillar_dir(directory,
                    init_data=None,
                    user=None,
                    group=None,
                    project=None,
                    commit_all=False,
                    do_push=False,
                    remote_less=False,
                    **kw):
    '''
    Initialize a basic versionned pillar directory

    directory
        directory to execute into
    user
        user to exec commands as and for new files
    group
        group for new files
    commit_all
        do we do a final git add/commit
    do_push
        do we do a final push
    project
        project name
    init_data
        configuration options in the corpus format (see get_configuration)
    '''
    user, group = get_default_user_group(user, group)
    files = [os.path.join(directory, 'init.sls')]
    remote_host = kw.get('remote_host', None)
    infos = get_contextual_cfg_defaults(
        [init_data], project=project, remote_host=remote_host)
    project = infos['project']
    remote_host = infos['remote_host']
    if not init_data:
        init_data = get_configuration(project, remote_host=remote_host)
    set_project(init_data)
    for fil in files:
        # if pillar is empty, create it
        if os.path.exists(fil):
            with open(fil) as fic:
                if fic.read().strip():
                    continue
        template = (
            'salt://makina-states/files/projects/2/pillar/{0}'.format(
                os.path.basename(fil)))
        if not init_data:
            init_data = {}
        init_data = _get_filtered_cfg(init_data)
        for k in [a for a in init_data]:
            if k not in [
                "api_version",
            ]:
                del init_data[k]
        # be sure that the first level is not an empty dict !
        if isinstance(init_data, OrderedDict):
            oinit_data = {}
            for i, val in six.iteritems(oinit_data):
                oinit_data[i] = val
            init_data = oinit_data
        defaults = {
            'name': project,
            'cfg': yaml.dump({
                'makina-projects.{0}'.format(project):
                init_data}, width=80, indent=2, default_flow_style=False)}
        do_push = commit_all = True
        cret = _state_exec(sfile, 'managed',
                           name=fil, source=template,
                           makedirs=True,
                           defaults=defaults, template='jinja',
                           user=user, group=group, mode='770')
        if not cret['result']:
            raise projects_api.ProjectInitException(
                'Can\'t create default {0}\n{1}'.format(fil, cret['comment']))
    if os.path.join(directory, '.git'):
        if commit_all:
            set_makina_states_author(directory, user=user)
            git_commit(directory, commit_all=commit_all, user=user)
        if do_push and not remote_less:
            push_changesets_in(directory, opts='-u', user=user)


def refresh_files_in_working_copy(project_root,
                                  init_data=None,
                                  project=None,
                                  user=None,
                                  group=None,
                                  force=False,
                                  api_version=None,
                                  commit_all=False,
                                  do_push=False,
                                  remote_host=None,
                                  remote_less=False,
                                  *args,
                                  **kwargs):
    if not api_version:
        api_version = API_VERSION
    user, group = get_default_user_group(user=user, group=group)
    project = get_default_project(project)
    ret = _get_ret(*args, **kwargs)
    _append_comment(ret, summary='Verify or initialise some default files')
    infos = get_contextual_cfg_defaults(
        [init_data], project=project, remote_host=remote_host)
    project = infos['project']
    remote_host = infos['remote_host']
    if not init_data:
        init_data = get_configuration(project, remote_host=remote_host)
    if not os.path.exists(
        os.path.join(project_root, '.salt')
    ):
        if not force:
            raise projects_api.TooEarlyError('Too early to call me')
        else:
            ret = init_salt_dir(project_root,
                                user=user,
                                init_data=init_data,
                                project=project,
                                do_push=do_push,
                                commit_all=commit_all,
                                remote_less=remote_less,
                                ret=ret)
    set_project(init_data)
    for fil in ['PILLAR.sample']:
        dest = os.path.join(project_root, '.salt', fil)
        if os.path.exists(dest):
            continue
        template = (
            'salt://makina-states/files/projects/{1}/'
            'salt/{0}'.format(fil, api_version))
        cret = _state_exec(sfile, 'managed',
                           name=dest,
                           source=template, defaults={},
                           user=user, group=group,
                           makedirs=True,
                           mode='770', template='jinja')
        if not cret['result']:
            raise projects_api.ProjectInitException(
                'Can\'t create default {0}\n{1}'.format(
                    fil, cret['comment']))
    if os.path.join(project_root, '.git') and not remote_less:
        if commit_all:
            git_commit(project_root, commit_all=commit_all, user=user)
        if do_push:
            push_changesets_in(project_root, user=user)
    return ret


def init_salt_dir(directory,
                  user=None,
                  group=None,
                  commit_all=False,
                  do_push=False,
                  project=None,
                  init_data=None,
                  remote_less=False,
                  **kw):
    '''
    Initialize a basic corpus project directory

    directory
        directory to execute into
    user
        user to exec commands as and for new files
    group
        group for new files
    commit_all
        do we do a final git add/commit
    do_push
        do we do a final push
    project
        project name
    init_data
        configuration options in the corpus format (see get_configuration)
    '''
    user, group = get_default_user_group(user=user, group=group)
    api_version = kw.get('api_version', API_VERSION)
    _s = __salt__
    ret = _get_ret(**kw)
    _append_comment(
        ret, summary='Verify or initialise salt & pillar core files')
    salt_root = os.path.join(directory, '.salt')
    if not init_data:
        init_data = get_configuration(project)
    set_project(init_data)
    if not os.path.exists(directory):
        raise projects_api.ProjectInitException(
            'directory for salt root {0} does not exist'.format(directory))
    cret = _state_exec(sfile, 'directory',
                       salt_root,
                       user=user,
                       group=group,
                       mode='770')
    if not cret['result']:
        raise projects_api.ProjectInitException(
            'Can\'t manage {0} dir'.format(directory))
    files = [os.path.join(salt_root, a)
             for a in os.listdir(salt_root)
             if a.endswith('.sls') and not os.path.isdir(a)]
    if not files:
        for fil in SPECIAL_SLSES + ['PILLAR.sample',
                                    '00_helloworld.sls']:
            template = (
                'salt://makina-states/files/projects/{1}/'
                'salt/{0}'.format(fil, api_version))
            cret = _state_exec(sfile, 'managed',
                               name=os.path.join(salt_root, '{0}').format(fil),
                               source=template, defaults={},
                               user=user, group=group,
                               makedirs=True,
                               mode='770', template='jinja')
            if not cret['result']:
                raise projects_api.ProjectInitException(
                    'Can\'t create default {0}\n{1}'.format(
                        fil, cret['comment']))
    if os.path.join(directory, '.git') and not remote_less:
        if commit_all:
            git_commit(directory, commit_all=commit_all, user=user)
        if do_push:
            push_changesets_in(directory, user=user)
    return ret


def init_project(name, *args, **kwargs):
    '''
    See common args to feed the neccessary variables to set a project
    You will need at least:

        - A name
        - A type
        - The pillar git repository url
        - The project & salt git repository url

    '''
    _s = __salt__
    cfg = get_configuration(name, *args, **kwargs)
    user, groups, group = cfg['user'], cfg['groups'], cfg['group']
    ret = _get_ret(cfg['name'])
    commit_all = kwargs.get('commit_all', False)
    try:
        init_user_groups(user, groups, ret=ret)
        init_ssh_user_keys(user,
                           failhard=cfg['default_env'] in ['dev'],
                           ret=ret)
        init_project_dirs(cfg, ret=ret)
        project_git_root = cfg['project_git_root']
        pillar_git_root = cfg['pillar_git_root']
        remote_less = is_remote_less(cfg)
        pillar_remote_less = remote_less or is_pillar_remote_less(cfg)
        repos = [
            (
                cfg['pillar_root'],
                get_default_rev(),
                pillar_git_root,
                False,
                False,
                True,
                pillar_remote_less
            ),
            (
                cfg['project_root'],
                get_default_rev(),
                project_git_root,
                True,
                True,
                False,
                remote_less
            ),
        ]

        for (wc, rev, localgit, hook,
             init_salt, init_pillar, lremote_less) in repos:
            # allow to have projects without remote
            if not lremote_less:
                init_repo(localgit, user=user, group=group, ret=ret,
                          init_salt=init_salt, init_pillar=init_pillar,
                          bare=True, init_data=cfg, remote_less=lremote_less)
            init_repo(wc, user=user, group=group, cfg=cfg, ret=ret,
                      bare=False, init_data=cfg, remote_less=lremote_less)
            if not lremote_less:
                for (working_copy, remote) in [
                    (localgit, wc), (wc, localgit)
                ]:
                    set_git_remote(working_copy, user, remote, ret=ret)
                fetch_last_commits(wc, user, ret=ret)
        sync_hooks(name, ret=ret, api_version=cfg['api_version'])
        # to mutally sync remotes, all repos must be created
        # first, so we need to cut off and reiterate over
        # the same iterables, but in 2 times
        for (wc, rev, localgit, hook, init_salt,
             init_pillar, lremote_less) in repos:
            if not lremote_less:
                set_upstream(wc, rev, user, ret=ret)
                sync_working_copy(wc, user=user, rev=rev, ret=ret)
        link(name, *args, **kwargs)
        refresh_files_in_working_copy_kwargs = copy.deepcopy(kwargs)
        for k in [
            'user', 'group', 'project', 'init_data', 'force', 'do_push',
            'remote_less', 'api_version', 'remote_less'
        ]:
            refresh_files_in_working_copy_kwargs.pop(k, None)
        refresh_files_in_working_copy_kwargs['commit_all'] = commit_all
        pillar = os.path.join(cfg['pillar_root'], 'init.sls')
        if not os.path.exists(pillar):
            init_pillar_dir(
                cfg['pillar_root'],
                init_data=cfg,
                project=cfg['name'],
                user=user,
                commit_all=False,
                bare=False,
                do_push=False,
                remote_less=pillar_remote_less,
                ret=ret)
        refresh_files_in_working_copy(cfg['project_root'],
                                      user=user,
                                      group=group,
                                      project=cfg['name'],
                                      init_data=cfg,
                                      force=True,
                                      do_push=True,
                                      remote_less=remote_less,
                                      api_version=cfg['api_version'],
                                      *args,
                                      **refresh_files_in_working_copy_kwargs)
        # in case of remoteless the .salt folder may have just been created
        # in working dir, so link must be redone here
        if remote_less or pillar_remote_less:
            link(name, *args, **kwargs)
        # remove if found, the force marker
        fm = os.path.join(cfg['project_git_root'], 'hooks', 'force_marker')
        if os.path.exists(fm):
            remove_path(fm)
    except projects_api.ProjectInitException, ex:
        trace = traceback.format_exc()
        ret['result'] = False
        _append_comment(ret,
                        summary="{0}".format(ex),
                        color='RED_BOLD',
                        body="{0}{1}{2}".format(
                            _colors('RED'), trace, _colors('ENDC')
                        ))
    if ret['result'] and not remote_less:
        set_configuration(cfg['name'], cfg)
        _append_comment(ret, summary="You can now push to",
                        color='RED',
                        body='Pillar: {0}\nProject: {1}'.format(
                            cfg['push_pillar_url'],
                            cfg['push_salt_url']))
    msplitstrip(ret)
    return _filter_ret(ret, cfg['raw_console_return'])


def reload_cfg(cfg, *args, **kwargs):
    kwargs['force_reload'] = True
    cfg = get_configuration(cfg['name'], *args, **kwargs)
    return cfg


def guarded_step(cfg,
                 step_or_steps,
                 inner_step=False,
                 error_msg=None,
                 rollback=False,
                 *args, **kwargs):
    name = cfg['name']
    ret = _get_ret(name, *args, **kwargs)
    if isinstance(step_or_steps, basestring):
        step_or_steps = [step_or_steps]
    if not step_or_steps:
        return ret
    # only rollback if the minimum to rollback is there
    if rollback and os.path.exists(cfg['project_root']):
        rollback = cfg['default_env'] not in ['dev']
        # XXX: remove me (True)!
        # rollback = True
    if not error_msg:
        error_msg = ''
    step = step_or_steps[0]
    try:
        try:
            for step in step_or_steps:
                set_project(cfg)
                if cfg.get('skip_{0}'.format(step), False):
                    continue
                cret = __salt__['mc_project_{1}.{0}'.format(
                    step, cfg['api_version'])](name, *args, **kwargs)
                _merge_statuses(ret, cret, step=step)
        except projects_api.ProjectProcedureException, pr:
            # if we are not in an inner step, raise in first place !
            # and do not mark for rollback
            if inner_step:
                cfg['rollback'] = rollback
            ret['result'] = False
            # in non editable modes, set the rollback project flag
            _merge_statuses(ret, pr.salt_ret, step=pr.salt_step)
    except Exception, ex:
        error_msg = (
            'Deployment error: {3}\n'
            'Project {0} failed to deploy and triggered a non managed '
            'exception in step: "{2}".\n'
            '{1}').format(name, ex, step, step)
        # if we have a non scheduled exception, we leave the system
        # in place for further inspection
        trace = traceback.format_exc()
        ret['result'] = False
        # in non editable modes, set the rollback project flag
        cfg['rollback'] = rollback
        _append_separator(ret)
        _append_comment(
            ret, summary=error_msg.format(name, ex, step.capitalize(), step),
            body=trace, color='RED')
    return ret


def execute_garded_step(name,
                        step_or_steps,
                        inner_step=False,
                        error_msg=None,
                        rollback=False,
                        *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    return guarded_step(cfg, step_or_steps,
                        inner_step=inner_step,
                        error_msg=error_msg,
                        rollback=rollback,
                        *args, **kwargs)


def sync_modules(name, *args, **kwargs):
    '''
    Install custom modules to the salt modules directory
    in the global module dir,

    Note: we install two symlinks to provide room for overlapping modules
    eg: project1/project/.salt/_modules/foo.py:bar can be called::

          salt-call foo.bar()
          salt-call foo_foo.bar()

    '''
    cfg = get_configuration(name, *args, **kwargs)
    ret = _get_ret(name, *args, **kwargs)
    _s = __salt__
    salt_root = cfg['salt_root']
    system_salt = __opts__['file_roots']['base'][0]
    k = 'salt'
    try:
        saltsettings = __salt__['mc_salt.settings']()[
            'data_mappings']['minion'][k]
    except KeyError:
        saltsettings = __salt__['mc_salt.settings']()
    for config_opt, dirs in saltsettings['saltmods'].items():
        dest = dirs[0]
        _d = os.path.basename(dest)
        orig = os.path.join(salt_root, _d)
        if os.path.isdir(orig):
            for module in [
                a for a in os.listdir(orig)
                if a.endswith('.py')
            ]:
                lnk = os.path.join(orig,  module)
                for j in ['{module}', '{name}_{module}']:
                    i = j.format(**locals())
                    lnkdst = os.path.join(dest, i)
                    if os.path.exists(lnkdst):
                        if os.path.islink(lnkdst):
                            if os.readlink(lnkdst) == lnk:
                                continue
                        _s['file.remove'](lnkdst)
                    if os.path.isfile(lnk):
                        if not os.path.exists(dest):
                            os.makedirs(dest)
                        _append_comment(
                            ret, summary=(
                                'Linking {0} <- {1}'.format(lnkdst, lnk)))
                        _s['file.symlink'](lnk, lnkdst)
    return ret


def deploy(name, *args, **kwargs):
    '''
    Deploy a project

    Only run install step::

        salt-call --local -ldebug mc_project.deploy <name> only=install

    Run only one or certain install step::

        salt-call --local -ldebug mc_project.deploy\\
                <name> only=install only_steps=00_foo
        salt-call --local -ldebug mc_project.deploy\\
                <name> only=install only_steps=00_foo,02_bar

    Only run install & fixperms step::

        salt-call --local -ldebug mc_project.deploy <n> only=install,fixperms

    Deploy entirely (this is what is run whithin the git hook)::

        salt-call --local -ldebug mc_project.deploy <name>

    Skip a particular step::

        salt-call --local -ldebug mc_project.deploy <name>\\
                skip_release_sync=True skip_archive=True skip_notify=True

    '''
    ret = _get_ret(name, *args, **kwargs)
    cfg = get_configuration(name, *args, **kwargs)
    if cfg['skip_deploy']:
        return ret
    # make the deploy_ret dict available in notify sls runners
    # via the __opts__.ms_project.deploy_ret variable
    cfg['deploy_summary'] = None
    cfg['deploy_ret'] = ret
    # in early stages, if something goes wrong, we want/cant do
    # much more that inviting the user to inspect the environment
    # only archive  the minimum to rollback is there
    if os.path.exists(cfg['project_root']):
        guarded_step(cfg, 'archive', ret=ret, *args, **kwargs)
    # okay, if backups are now done and in OK status
    # hand tights for the deployment

    only_steps = kwargs.get('only_steps', None)
    # be sure to have modules pre-synced
    if ret['result']:
        guarded_step(cfg,
                     ['sync_modules'],
                     rollback=True,
                     inner_step=True,
                     ret=ret)

    if ret['result']:
        guarded_step(cfg,
                     ['release_sync'],
                     rollback=True,
                     inner_step=True,
                     ret=ret)
        cfg = get_configuration(name, *args, **kwargs)

    if ret['result']:
        guarded_step(cfg,
                     ['install'],
                     rollback=True,
                     only_steps=only_steps,
                     inner_step=True,
                     ret=ret)
    # if the rollback flag has been raised, just do a rollback
    # only rollback if the minimum to rollback is there
    if ret['result']:
        guarded_step(cfg, 'rotate_archives', ret=ret, *args, **kwargs)
    if cfg['rollback'] and os.path.exists(cfg['project_root']):
        guarded_step(cfg, 'rollback', ret=ret, *args, **kwargs)
    if ret['result']:
        summary = 'Deployment {0} finished successfully for {1}'.format(
            cfg['chrono'], name)
    else:
        summary = 'Deployment {0} failed for {1}'.format(
            cfg['chrono'], name)
    _append_separator(ret)
    _append_comment(ret, summary, color='RED_BOLD')
    cfg['deploy_summary'] = summary
    # notifications should not modify the result status even failed
    result = ret['result']
    msplitstrip(ret)
    guarded_step(cfg, 'fixperms', ret=ret, *args, **kwargs)
    guarded_step(cfg, 'notify', ret=ret, *args, **kwargs)
    ret['result'] = result
    _force_cli_retcode(ret)
    return _filter_ret(ret, cfg['raw_console_return'])


def run_task(name, only_steps, *args, **kwargs):
    '''
    Run one or more tasks inside a project context.

    You can filter steps to run with only_steps

    All sls in ``.salt`` which are a task (all files beginning with task\_ will be searched
    and the one matching only_steps (string or list) will be executed)
    '''
    if not only_steps:
        raise _stop_proc('One task at least must be providen')
    ret = _get_ret(name, *args, **kwargs)
    cfg = get_configuration(name, *args, **kwargs)
    if cfg['skip_deploy']:
        return ret
    # make the deploy_ret dict available in notify sls runners
    # via the __opts__.ms_project.deploy_ret variable
    cfg['deploy_summary'] = None
    cfg['deploy_ret'] = ret
    if ret['result']:
        guarded_step(cfg,
                     ['install'],
                     rollback=False,
                     only_steps=only_steps,
                     task_mode=True,
                     inner_step=True,
                     ret=ret)
    if ret['result']:
        summary = 'Task(s) {0} finished successfully for {1}'.format(
            only_steps, name)
    else:
        summary = 'Task(s) {0} failed for {1}'.format(
            only_steps, name)
    _append_separator(ret)
    _append_comment(ret, summary, color='RED_BOLD')
    cfg['deploy_summary'] = summary
    # notifications should not modify the result status even failed
    msplitstrip(ret)
    _force_cli_retcode(ret)
    return _filter_ret(ret, cfg['raw_console_return'])


def archive(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'archive')
    return cret


def release_sync(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    iret = init_project(name, *args, **kwargs)
    cfg = reload_cfg(cfg)
    return iret


def get_executable_slss_(path, installer_path, installer, task=False):
    def do_filter(sx):
        x = os.path.join(path, sx)
        filtered = True
        if (
            sx in SPECIAL_SLSES
            or (os.path.isdir(x))
            or (not sx.endswith('.sls'))
        ):
            filtered = False
        if task and not sx.startswith('task_'):
            filtered = False
        if not task and sx.startswith('task_'):
            filtered = False
        return filtered
    slses = [a.split('.sls')[0]
             for a in filter(do_filter, os.listdir(path))]

    def sls_sort(a):
        '''
        >>> sorted(['0100_a', '0010_b', '0004_a','100_b',
        ... '0_4', '0_1', '0_2'], key=a)
        ['0004_a', '0010_b', '0100_a', '0_1', '0_2', '0_4', '100_b']
        '''
        return a
    slses.sort(key=sls_sort)
    return slses


def get_executable_slss(path, installer_path, installer):
    return get_executable_slss_(path, installer_path, installer, task=False)


def get_task_slss(path, installer_path, installer):
    return get_executable_slss_(path, installer_path, installer, task=True)


def install(name, only_steps=None, task_mode=False, *args, **kwargs):
    '''
    You can filter steps to run with only_steps
    All sls in .salt which are not special or tasks (beginning with tasks
    will be executed)

    eg::

        salt mc_project.deploy only=install onlystep=00_foo,001_bar
        salt mc_project.deploy only=install onlystep=00_foo

    '''
    if not only_steps:
        only_steps = []
    if isinstance(only_steps, basestring):
        only_steps = only_steps.split(',')
    cfg = get_configuration(name, *args, **kwargs)
    ret = _get_ret(name, *args, **kwargs)
    if ret['result']:
        guarded_step(cfg,
                     ['sync_modules'],
                     rollback=True,
                     inner_step=True,
                     ret=ret)
    if not os.path.exists(cfg['installer_path']):
        raise projects_api.ProjectInitException(
            'invalid project type or installer directory: {0}/{1}'.format(
                cfg['installer'], cfg['installer_path']))
    cret = None
    method = get_executable_slss
    if task_mode:
        method = get_task_slss
    slses = method(
        cfg['wired_salt_root'],
        cfg['installer_path'],
        cfg['installer'])
    if not slses:
        raise _stop_proc('No installation slses '
                         'avalaible for {0}'.format(name), 'install', ret)
    only_steps_search = []
    for s in only_steps:
        only_steps_search.append(s)
        if s.endswith('.sls'):
            only_steps_search.append(s[:-4])
        else:
            only_steps_search.append(s + ".sls")
    for sls in slses:
        skip = False
        if only_steps_search:
            if sls not in only_steps_search:
                skip = True
        if skip:
            log.info(
                'Skipped install step: {1} for {0}'.format(cfg['name'], sls))
            continue
        cret = _step_exec(cfg, sls)
        _merge_statuses(ret, cret)
    return ret


def run_setup(name, step_name,  *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, step)
    return cret


def fixperms(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'fixperms')
    return cret


def link_pillar(names, *args, **kwargs):
    '''
    Add the link wired in pillar folder
    & register the pillar in pillar top

    name
        list of project(s) separated by commas
    '''
    if not isinstance(names, list):
        names = names.split(',')
    names.extend(args)
    ret = _get_ret(*args, **kwargs)
    for name in names:
        cfg = get_configuration(name, nodata=True, *args, **kwargs)
        salt_settings = __salt__['mc_salt.settings']()
        pillar_root = os.path.join(salt_settings['pillar_root'])
        upillar_top = 'makina-projects.{name}'.format(**cfg)
        pillarf = os.path.join(pillar_root, 'top.sls')
        customf = os.path.join(pillar_root, 'custom.sls')
        pillar_top = 'makina-projects.{name}'.format(**cfg)
        link_into_root(
            name, ret,
            cfg['wired_pillar_root'], cfg['pillar_root'], do_link=True)
        if LooseVersion(VERSION) >= LooseVersion("2.0"):
            continue
        added = '    - {0}'.format(pillar_top)
        for f, content in six.iteritems({pillarf: TOP, customf: CUSTOM}):
            if not os.path.exists(f):
                with open(f, 'w') as fic:
                    fic.write(content)
        with open(pillarf) as fpillarf:
            pillars = fpillarf.read().splitlines()
            found = False
            for line in pillars:
                if line.strip().endswith(added.strip()):
                    found = True
                    break
            if not found:
                lines = []
                log = False
                for line in pillars:
                    lines.append(line)
                    if line == "  '*':":
                        log = True
                        lines.append(added)
                with open(pillarf, 'w') as wpillarf:
                    wpillarf.write('\n'.join(lines))
                if log:
                    _append_comment(
                        ret, body=indent(
                            'Added to pillar top: {0}'.format(name)))
    return ret


def unlink_pillar(names, *args, **kwargs):
    '''
    Remove the link wired in pillar folder
    & unregister the pillar in pillar top

    name
        list of project(s) separated by commas
    '''
    if not isinstance(names, list):
        names = names.split(',')
    names.extend(args)
    ret = _get_ret(*args, **kwargs)
    for name in names:
        cfg = get_configuration(name, nodata=True,  *args, **kwargs)
        kwargs.pop('ret', None)
        salt_settings = __salt__['mc_salt.settings']()
        pillar_root = os.path.join(salt_settings['pillar_root'])
        pillarf = os.path.join(pillar_root, 'top.sls')
        pillar_top = 'makina-projects.{name}'.format(**cfg)
        if not LooseVersion(VERSION) >= LooseVersion("2.0"):
            with open(pillarf) as fpillarf:
                pillar_top = '- makina-projects.{name}'.format(**cfg)
                pillars = fpillarf.read()
                if pillar_top in pillars:
                    lines = []
                    log = False
                    for line in pillars.splitlines():
                        if line.endswith(pillar_top):
                            log = True
                            continue
                        lines.append(line)
                    with open(pillarf, 'w') as wpillarf:
                        wpillarf.write('\n'.join(lines))
                    if log:
                        _append_comment(
                            ret, body=indent(
                                'Cleaned pillar top: {0}'.format(name)))
        link_into_root(
            name, ret,
            cfg['wired_pillar_root'], cfg['pillar_root'], do_link=False)
    return ret


def link_into_root(name, ret, link, target, do_link=True):
    '''
    Link a salt managed directory into salt root

    This takes care of not leaving a dangling symlink
    '''
    remove = not do_link
    ftarget = os.path.abspath(target)
    kind = (('pillar' in ftarget) is True) and 'pillar' or 'salt'
    if os.path.islink(link):
        if (
            # target changed
            os.path.abspath(os.readlink(link)) != ftarget or
            # dangling symlink
            not os.path.exists(link)
        ):
            remove = True
        if (
            os.path.abspath(os.readlink(link)) == ftarget
        ):
            do_link = False
    if (
        remove and (os.path.islink(link) or
                    os.path.exists(link))
    ):
        _append_comment(
            ret, body=indent(
                'Cleaned {1} root from {0}'.format(name, kind)))
        remove_path(link)
    if do_link and os.path.exists(ftarget):
        _append_comment(
            ret, body=indent(
                'Linked {0} into {1} root'.format(name, kind)))
        os.symlink(target, link)


def link_salt(names, *args, **kwargs):
    '''
    Link a salt managed directory into salt root
    This takes care of not leaving a dangling symlink
    '''
    if not isinstance(names, list):
        names = names.split(',')
    names.extend(args)
    ret = _get_ret(*args, **kwargs)
    for name in names:
        cfg = get_configuration(name, nodata=True, *args, **kwargs)
        kwargs.pop('ret', None)
        link_into_root(
            name, ret, cfg['wired_salt_root'], cfg['salt_root'], do_link=True)
    return ret


def unlink_salt(names, *args, **kwargs):
    '''
    Remove the link wired in salt folder
    & unregister the pillar in pillar top

    name
        list of project(s) separated by commas
    '''

    if not isinstance(names, list):
        names = names.split(',')
    names.extend(args)
    ret = _get_ret(*args, **kwargs)
    for name in names:
        cfg = get_configuration(name, nodata=True, *args, **kwargs)
        kwargs.pop('ret', None)
        link_into_root(
            name, ret, cfg['wired_salt_root'], cfg['salt_root'], do_link=False)
    return ret


def link(names, *args, **kwargs):
    '''
    Add the link wired in salt folders (pillar & salt)
    & register the pillar in pillar top

    name
        list of project(s) separated by commas

    '''
    ret = _get_ret(*args, **kwargs)
    kwargs.pop('ret', None)
    if not isinstance(names, list):
        names = names.split(',')
    names.extend(args)
    for nm in names:
        link_pillar(nm, ret=ret, *args, **kwargs)
        link_salt(nm, ret=ret, *args, **kwargs)
    return msplitstrip(ret)


def unlink(names, *args, **kwargs):
    '''
    Remove the link wired in salt folders (pillar & salt)

    name
        list of project(s) separated by commas
    '''
    kwargs.pop('ret', None)
    ret = _get_ret(*args, **kwargs)
    if not isinstance(names, list):
        names = names.split(',')
    names.extend(args)
    for nm in names:
        unlink_pillar(nm, ret=ret, *args, **kwargs)
        unlink_salt(nm, ret=ret, *args, **kwargs)
    return msplitstrip(ret)


def rollback(name, *args, **kwargs):
    '''
    Run the rollback corpus step
    '''
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'rollback')
    return cret


def rotate_archives(name, *args, **kwargs):
    '''
    Run the rotate_archives corpus step
    '''
    cfg = get_configuration(name, *args, **kwargs)
    ret = _get_ret(name, *args, **kwargs)
    try:
        if os.path.exists(cfg['archives_root']):
            archives = sorted(os.listdir(cfg['archives_root']))
            to_keep = archives[-cfg['keep_archives']:]
            for archive in archives:
                if archive not in to_keep:
                    remove_path(os.path.join(cfg['archives_root'], archive))
        _append_comment(ret, summary=('Archives cleanup done '))
    except Exception:
        trace = traceback.format_exc()
        ret['result'] = False
        _append_comment(
            ret, color='RED_BOLD',
            summary=('Archives cleanup procedure '
                     'failed:\n{0}').format(trace))
    return ret


def notify(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'notify')
    return cret


def sync_hooks_for_all(*args, **kwargs):
    '''
    Get connection details & projects report
    '''
    pt = get_configuration('project')['projects_dir']
    projects = os.listdir(pt)
    ret = _get_ret('project')
    if projects:
        for pj in projects:
            if os.path.exists(os.path.join(pt, pj, 'project', '.git')):
                ret = _merge_statuses(ret, sync_hooks(pj))
    return ret


def list_projects():
    locs = __salt__['mc_locations.settings']()
    cfgs = OrderedDict()
    if os.path.exists(locs['projects_dir']):
        projects = os.listdir(locs['projects_dir'])
        if projects:
            for pj in projects:
                cfgs[pj] = get_configuration(pj)
                uncache_project(pj)
    for pj in [a for a in cfgs]:
        cfg = cfgs[pj]
        if (
            not os.path.exists(
                os.path.join(cfg['pillar_root'], 'init.sls')
            ) or (
                True in
                [not os.path.exists(
                    os.path.join(cfg['project_root'], '.salt', a)
                ) for a in ['fixperms.sls', 'PILLAR.sample']]
            )
        ):
            cfgs.pop(pj, None)
    return cfgs


def link_projects(projects=None):
    rets = OrderedDict()
    if not projects:
        projects = list_projects()
    for pj in projects:
        rets[pj] = link(pj)
    return rets


def report():
    '''
    Get connection details & projects report

    CLI Examples::

        salt-call --local mc_project.report
    '''
    locs = __salt__['mc_locations.settings']()
    pt = locs['projects_dir']
    ret = ''
    target = __grains__['id']
    dconf = get_default_configuration()

    ips = [a
           for a in __grains__.get('ipv4', [])
           if not a.startswith('127.0')]
    if ips:
        ips = 'IP(s): ' + ', '.join(ips) + '\n'
    if ips.endswith(','):
        ips = ips[:-1]
    if os.path.exists(pt):
        ret += '''
{id}:
{ips}
SSH Config:
Host {dconf[this_localhost]}
Port {dconf[this_port]}
User root
ServerAliveInterval 5

'''.format(id=target, ips=ips, dconf=dconf)
    projects = os.listdir(pt)
    if projects:
        ret += 'Projects:'
        for pj in projects:
            if os.path.isfile(os.path.join(pt, pj)):
                continue
            conf = __salt__[
                'mc_project.get_configuration'](pj)
            ret += '''
Name: {conf[name]}
Pillar: {conf[push_pillar_url]}
Project: {conf[push_salt_url]}
'''.format(conf=conf)
    return ret


def sync_git_directory(directory,
                       origin=None,
                       rev=None,
                       sync_remote='sync',
                       refresh=False,
                       local_branch=None,
                       **kw):

    '''
    Agressively sync a git working copy with its remote

    directory
        directory where to act
    origin
        remote origin <url>
    rev
        changeset to deploy
    local_branch
        local branch to set to
    sync_remote
        name of the remote
    refresh
        if the working copy exists, force the git pull dance

    CLI Examples::

        salt-call --local \\
                mc_project.sync_git_directory /foo origin=git://foo rev=develop
    '''
    cret = OrderedDict()
    try:
        _s = __salt__
        if not os.path.exists(
            os.path.join(directory, '.git', 'config')
        ):
            raise OSError('{0} is not a git working copy'.format(
                directory))
        rev = get_default_rev(rev)
        user, _ = get_default_user_group(**kw)
        cret['clean'] = clean_salt_git_commit(directory)
        if origin:
            _s['git.remote_set'](directory, remote=sync_remote, url=origin, user=user)
        try:
            remotes = _s['git.remotes'](directory, user=user)
        except Exception:
            remotes = {}
        if local_branch is None:
            local_branch = 'master'
        if refresh and (sync_remote in remotes):
            cret['fetch'] = _s['git.fetch'](
                directory, remote=sync_remote, user=user)
            cret['stash_local_changes'] = _s['git.stash'](
                directory,
                user=user)
            cret['go_to_{0}'.format(local_branch)] = _s['git.checkout'](
                directory,
                local_branch,
                user=user)
            cret['sync'] = _s['git.reset'](
                directory,
                opts='--hard {0}/{1}'.format(sync_remote, rev),
                user=user)
    except (
        OSError,
        salt.exceptions.CommandExecutionError,
        projects_api.ProjectNotCleanError
    ) as exc:
        trace = traceback.format_exc()
        raise_exc(
            kw.get('exc_klas',
                   projects_api.BaseRemoteProjectSyncError),
            msg=('{directory}: sync error'),
            detail_msg=('{directory}: sync error'
                        ':\n{scret}'),
            scret=trace,
            cret=cret,
            directory=directory,
            original=exc)
    return cret


def repr_ret(lcret):
    sret = ''
    rets = [lcret]
    if isinstance(lcret, dict):
        raw_res = lcret.get('raw_result', None)
        if isinstance(raw_res, dict):
            rets.append(raw_res)
    done_levels = []
    for cret in rets:
        levels = ['comment', 'trace', 'stdout', 'stderr']
        if any([level in cret for level in levels]):
            out = ''
            for i in levels:
                if (i not in cret) or (i in done_levels):
                    continue
                done_levels.append(i)
                val = cret[i]
                if not val:
                    val = ''
                val = val.strip()
                out += '{0}:\n'.format(i.upper())
                if not val:
                    continue
                try:
                    out += __salt__['mc_utils.magicstring'](val)
                except Exception:
                    out += '{0} failed to repr\n'
                out += '\n'
            if cret.get('retcode'):
                out += 'retcode: {retcode}'.format(**cret)
            sret = out
    if not sret:
        try:
            sret = pprint.pformat(cret)
        except Exception:
            try:
                sret = '{0}'.format(cret)
            except Exception:
                try:
                    sret = repr(cret)
                except Exception:
                    sret = 'failed to repr this result'
    return sret


def raise_exc(klass,
              msg,
              detail_msg=None,
              default_msg='failed',
              *exc_args,
              **exc_kwargs):
    if not detail_msg:
        if msg:
            detail_msg = msg
        else:
            detail_msg = default_msg
    rmsg = None
    try:
        rmsg = detail_msg.format(*exc_args, **exc_kwargs)
    except UnicodeEncodeError:
        if not isinstance(detail_msg, unicode):
            try:
                rmsg = detail_msg.decode('utf-8').format(
                    *exc_args, **exc_kwargs).encode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                rmsg = None
        if not rmsg:
            try:
                rmsg = msg.format(*exc_args, **exc_kwargs)
            except UnicodeEncodeError:
                if not isinstance(msg, unicode):
                    try:
                        rmsg = msg.decode('utf-8').format(
                            *exc_args, **exc_kwargs).encode('utf-8')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        rmsg = None
    if not rmsg:
        msg = default_msg
    if isinstance(rmsg, six.string_types):
        rmsg = __salt__['mc_utils.magicstring'](rmsg)
    raise klass(rmsg, *exc_args, **exc_kwargs)


def clean_salt_git_commit(directory, commit=True, **kw):
    '''
    '''
    user, group = get_default_user_group(**kw)
    cret = OrderedDict()
    cret['st'] = __salt__['cmd.run']('git status',
                                     env={'LANG': 'C', 'LC_ALL': 'C'},
                                     runas=user,
                                     cwd=directory, python_shell=True)
    if 'nothing added to commit but untracked files present' in cret['st']:
        pass
    elif 'nothing to commit' in cret['st']:
        pass
    else:
        try:
            msg = "{0}: git invalid status\n{1}".format(
                directory, cret['st'])
        except Exception:
            msg = "{0}: git invalid status".format(directory)
        raise projects_api.ProjectNotCleanError(msg, ret=cret)
    return cret


#
# REMOTE API
#

def get_default_rev(rev=None, **kw):
    if rev is None:
        rev = kw.get('rev', 'master')
    return rev


def _init_local_remote_directory(host,
                                 project,
                                 directory,
                                 init_salt=False,
                                 init_pillar=False,
                                 init_data=None,
                                 bare=False,
                                 origin=None,
                                 refresh=None,
                                 rev=None,
                                 **kw):
    '''
    Initialize a local git directory to be deployed & synchronized remotely

    This git directory can be initialized as either:

        - an empty repo
        - a pillar repo (./init.sls): if init_pillar=True
        - a salt repo (./.salt): if init_salt=True

    CLI Examples::

        salt-call --local mc_project._init_local_remote_directory\\
                host.fr <project>
        salt-call --local mc_project._init_local_remote_directory\\
                host.fr <project> init_salt=True
        salt-call --local mc_project._init_local_remote_directory\\
                host.fr <project> init_pillar=True
    '''
    _s = __salt__
    exc_klass = kw.get('exc_klass',
                       projects_api.BaseProjectInitException)

    kind = ''
    if bare:
        kind += ' bare'
    if init_salt:
        kind += ' salt'
    elif init_pillar:
        kind += ' pillar'
    if kind:
        kind += ' '
    _remote_log('   - Initialize local{4}copy:'
                '  {2}{3}{0}/{1}'.format(host,
                                         project,
                                         _colors('endc'),
                                         _colors('yellow'),
                                         kind))
    rev = get_default_rev(rev)
    if origin:
        _remote_log('       * origin: {1}{2}{0}'.format(
            origin, _colors('endc'), _colors('light_yellow')),
            color='yellow')
    if rev != get_default_rev():
        _remote_log('       * rev: {1}{2}{0}'.format(
            rev, _colors('endc'), _colors('light_yellow')),
            color='yellow')
    if refresh:
        _remote_log('       * will force the refresh')
    try:
        cret = OrderedDict()
        container = os.path.dirname(directory)
        user, group = get_default_user_group(**kw)
        if not os.path.isdir(container):
            _s['file.makedirs_perms'](
                container, user=user, group=group, mode=750)
        if not os.path.isdir(container):
            raise OSError(
                "Project container creation failed ({0})".format(container))
        empty_directory = False
        if not os.path.exists(directory):
            empty_directory = True
        else:
            empty_directory = bool(
                not [a for a in os.listdir(directory)
                     if a not in ['.', '..']])
        if empty_directory:
            _s['file.remove'](directory)
        maybe_sync = not empty_directory
        if origin:
            if empty_directory:
                cret['clone'] = _s['git.clone'](directory, url=origin, user=user)
                cret['st'] = clean_salt_git_commit(directory)['st']
        else:
            if empty_directory:
                cret['init'] = init_repo(directory,
                                         bare=bare,
                                         init_pillar=init_pillar,
                                         init_salt=init_salt,
                                         init_data=init_data,
                                         user=user,
                                         group=group)
        if maybe_sync and (refresh in [None, True]):
            cret['sync_dir'] = sync_git_directory(
                directory,
                origin=origin,
                refresh=True,
                exc_klass=exc_klass,
                rev=rev,
                user=user)
        set_makina_states_author(directory, user=user)
    except (
        OSError,
        salt.exceptions.CommandExecutionError,
        projects_api.ProjectNotCleanError
    ) as exc:
        scret = traceback.format_exc()
        raise_exc(
            exc_klass,
            msg=('{host}: remote project {project} '
                 'structure init failed'),
            detail_msg=('{host}: remote project {project} '
                        'init failed:\n{scret}'),
            scret=scret,
            cret=cret,
            host=host,
            original=exc,
            project=project)
    return cret


def init_local_remote_pillar(host,
                             project,
                             origin=None,
                             rev=None,
                             **kw):
    _s = __salt__
    # we only need a few constant properties, project is not existing locally
    pcfg = _s['mc_project.get_configuration'](project, remote_host=host)
    directory = os.path.abspath(pcfg['remote_pillar_dir'])
    cret = OrderedDict()
    cret = _init_local_remote_directory(
        host,
        project,
        directory,
        bare=False,
        origin=origin,
        rev=rev,
        #
        init_pillar=True,
        init_data=pcfg,
        exc_klass=(
            projects_api.RemotePillarInitException),
        **kw)
    return cret


def init_local_remote_project(host,
                              project,
                              origin=None,
                              rev=None,
                              **kw):
    _s = __salt__
    # we only need a few constant properties, project is not existing locally
    pcfg = get_configuration(project, remote_host=host)
    cfg = get_configuration(project)
    directory = pcfg['remote_project_dir']
    cret = OrderedDict()
    cret = _init_local_remote_directory(
        host,
        project,
        directory,
        bare=False,
        origin=origin,
        rev=rev,
        # no remote hsot here
        init_data=cfg,
        init_salt=True,
        exc_klass=(
            projects_api.RemoteProjectInitException),
        **kw)
    return cret


def init_remote_structure(host, project, **kw):
    '''
    Initialize a remote project structure over ssh

    CLI Examples::

        salt-call --local mc_project.init_remote_structure host.fr <project>
    '''
    _s = __salt__
    user, group = get_default_user_group(**kw)
    ssh_kw = _s['mc_remote.ssh_kwargs'](kw)
    dkey = 'mc_project_{0}_{1}'.format(host, project)
    cret = __context__.get(dkey, OrderedDict())
    # if we already run, but failed
    # we have cached the result, but we can test to redeploy
    if not isinstance(cret, dict):
        cret = None
    else:
        if not cret.get('result'):
            cret = None
    _remote_log('   - Initialize remote project structure:'
                '  {2}{3}{0}/{1}'.format(host, project,
                                         _colors('endc'),
                                         _colors('yellow')))
    do_raise = kw.get('do_raise', True)
    failed = False
    scret = ''
    if not cret:
        original = None
        try:
            test_structure = _s['mc_remote.ssh'](
                host, (
                    'set -e;'
                    'test -d /srv/salt/makina-projects/{0};'
                    'test -d /srv/pillar/makina-projects/{0};'
                    'test -d /srv/projects/{0}/project;'
                    'test -d /srv/projects/{0}/pillar;'
                    'test -d /srv/projects/{0}/git/pillar.git;'
                    'test -d /srv/projects/{0}/git/project.git'
                ).format(project), no_error_log=True, **ssh_kw)
            if test_structure['retcode']:
                cret = _s['mc_remote.salt_call'](
                    host, 'mc_project.deploy', project, **ssh_kw)
                if cret['retcode'] > 0:
                    failed = True
                elif not cret['result'].get('result', False):
                    failed = True
                scret = repr_ret(cret)
        except Exception as exc:
            trace = traceback.format_exc()
            failed = True
            original = exc
            cret = '{0}'.format(exc)
            scret = trace
        if do_raise and failed:
            raise_exc(
                projects_api.RemoteProjectInitException,
                msg=('{host}: remote project {project} '
                     'structure init failed'),
                detail_msg=('{host}: remote project {project} '
                            'init failed:\n{scret}'),
                scret=scret,
                cret=cret,
                host=host,
                original=original,
                project=project)
    __context__[dkey] = cret
    return __context__[dkey]


def sync_remote_working_copy(host,
                             directory,
                             remote_directory=None,
                             remote_local_copy=None,
                             lremote=None,
                             **kw):

    '''
    CLI examples::

        salt-call --local mc_project.sync_remote_working_copy\\
                a.fr /srv/remote-projects/a.fr
        salt-call --local mc_project.sync_remote_working_copy\\
                a.fr /srv/remote-projects/a.fr /otherdir
    '''

    _remote_log('      - Synchronizing {2}{3}{0}:{1}'.format(
        host, directory, _colors('endc'), _colors('yellow')))
    origin = kw.get('origin', None)
    rev = get_default_rev(**kw)
    _s = __salt__
    user, group = get_default_user_group(**kw)
    ssh_kw = _s['mc_remote.ssh_kwargs'](kw, user=user)
    cret = OrderedDict()
    if not remote_directory:
        remote_directory = directory
    _remote_log(
        '         * remote directory: {1}{2}{0}'.format(
            remote_directory, _colors('endc'), _colors('light_yellow')
        ),
        color='yellow')
    if origin:
        _remote_log('           * origin: {1}{2}{0}'.format(
            origin, _colors('endc'), _colors('light_yellow')),
            color='yellow')
    if rev != get_default_rev():
        _remote_log('           * rev: {1}{2}{0}'.format(
            rev, _colors('endc'), _colors('light_yellow')),
            color='yellow')
    kw['user'] = user
    gforce = '--force master:master'
    tmpbare = "{0}.bare.git".format(os.path.abspath(directory))
    if not lremote:
        lremote = 'localcopy'
    klass = projects_api.RemoteProjectTransferError
    trace = ''
    failed, original = False, None
    try:
        set_makina_states_author(directory, user=user)
        clean_salt_git_commit(directory)
        if not os.path.exists(tmpbare):
            cret['clone'] = _s['git.clone'](tmpbare,
                                            url=directory,
                                            opts='--bare',
                                            user=user)
        cret['remote'] = _s['git.remote_set'](
            directory, remote=lremote, url=tmpbare, user=user)
        cret['push'] = _s['git.push'](
            directory, remote=lremote, ref='', opts=gforce, user=user)
    except (Exception,) as exc:
        trace = traceback.format_exc()
        failed, original = True, exc
        klass = projects_api.RemoteProjectTransferError

    if not failed:
        try:
            cret['sync_files'] = _s['mc_remote.ssh_transfer_dir'](
                host,
                directory,
                remote_directory,
                makedirs=True,
                rsync_opts='--delete -P',
                **ssh_kw)
            if cret['sync_files']['retcode']:
                failed = True
                trace = repr_ret(cret['sync_files'])
            else:
                cret['sync_files'] = cret['sync_files']['stdout']
        except (Exception,) as exc:
            trace = traceback.format_exc()
            failed, original = True, exc
            klass = projects_api.RemoteProjectSyncRemoteError

    if not failed:
        try:
            fixperms = os.path.join(
                os.path.abspath(
                    os.path.dirname(remote_local_copy)),
                'global-reset-perms.sh')
            cret['wc_sync'] = _s['mc_remote.ssh'](
                host,
                'cd "{remote_local_copy}"'
                '&& git remote add "{0}" "{1}" 2>/dev/null;'
                'if [ "x${{?}}" != "x0" ];then'
                ' git remote set-url "{0}" "{1}";'
                'fi'
                '&& set -x 1>/dev/null 2>&1'
                '&& git fetch "{0}"'
                '&& git reset --hard "{0}/master"'
                '&& git push origin {2};'
                'ret=${{?}};'
                'if [ -x "{fixperms}" ];then'
                ' "{fixperms}" 1>/dev/null 2>&1 || /bin/true;'
                'fi;'
                'exit ${{ret}}'
                ''.format(lremote,
                          remote_directory,
                          gforce,
                          remote_local_copy=remote_local_copy,
                          fixperms=fixperms),
                **ssh_kw)
            if cret['wc_sync']['retcode']:
                failed = True
                trace = repr_ret(cret['wc_sync'])
            else:
                cret['wc_sync'] = cret['wc_sync']['stdout']
        except (Exception,) as exc:
            trace = traceback.format_exc()
            failed, original = True, exc
            klass = projects_api.RemoteProjectWCSyncError
    if failed:
        raise_exc(
            klass,
            msg='{host}: directory {directory} sync failed',
            detail_msg=('{host}: directory {directory}'
                        ' sync failed:\n{scret}'),
            scret=trace,
            cret=cret,
            host=host,
            directory=directory,
            original=original)
    return cret


def sync_remote_directory(host,
                          project,
                          directory,
                          remote_directory=None,
                          remote_local_copy=None,
                          origin=None,
                          rev=None,
                          refresh=None,
                          init=None,
                          lremote=None,
                          **kw):

    _remote_log('      - Synchronizing directory'
                ' {3}{4}{0}/{1}:'
                ''.format(host,
                          project,
                          directory,
                          _colors('endc'),
                          _colors('yellow'),
                          _colors('light_yellow')))
    _remote_log(
        '           * {1}{2}{0}'.format(
            directory,
            _colors('yellow'),
            _colors('light_yellow')),
        'yellow')
    _s = __salt__
    cret = OrderedDict()
    if init is None:
        init = False
    try:
        if init:
            cret['init'] = init_local_remote_project(
                host, project,
                origin=origin, rev=rev, refresh=refresh,
                **kw)
        else:
            cret['sync'] = sync_git_directory(
                directory,
                origin=origin, refresh=refresh, rev=rev, **kw)
        cret['remote_sync'] = sync_remote_working_copy(
            host,
            directory,
            remote_directory=remote_directory,
            remote_local_copy=remote_local_copy,
            lremote=lremote,
            **kw)
    except (
        salt.exceptions.CommandExecutionError,
        projects_api.BaseRemoteProjectSyncError,
        projects_api.ProjectNotCleanError
    ) as exc:
        trace = traceback.format_exc()
        raise_exc(
            projects_api.RemoteProjectSyncRemoteError,
            msg='{host}: project {project} sync failed',
            detail_msg='{host}: project {project} sync failed:\n{scret}',
            scret=trace,
            cret=cret,
            host=host,
            original=exc,
            project=project)
    return cret


def sync_remote_pillar(host,
                       project,
                       origin=None,
                       remote_directory=None,
                       remote_local_copy=None,
                       rev=None,
                       init=False,
                       refresh=None,
                       lremote=None,
                       **kw):
    _remote_log('   - Synchronizing pillar on'
                ' {2}{3}{0}/{1}'.format(host,
                                        project,
                                        _colors('endc'),
                                        _colors('yellow')))
    _s = __salt__
    project = get_default_project(project)
    pcfg = _s['mc_project.get_configuration'](project, remote_host=host)
    directory = pcfg['remote_pillar_dir']
    if remote_local_copy is None:
        remote_local_copy = pcfg['pillar_root']
    cret = sync_remote_directory(host,
                                 project,
                                 directory,
                                 remote_directory=remote_directory,
                                 remote_local_copy=remote_local_copy,
                                 origin=origin,
                                 rev=rev,
                                 refresh=refresh,
                                 init=init,
                                 lremote=lremote,
                                 **kw)
    return cret


def sync_remote_project(host,
                        project,
                        origin=None,
                        remote_directory=None,
                        remote_local_copy=None,
                        rev=None,
                        init=False,
                        refresh=None,
                        lremote=None,
                        **kw):
    _remote_log('   - Synchronizing project on'
                ' {2}{3}{0}/{1}'.format(host,
                                        project,
                                        _colors('endc'),
                                        _colors('yellow')))
    _s = __salt__
    project = get_default_project(project)
    pcfg = _s['mc_project.get_configuration'](project, remote_host=host)
    directory = pcfg['remote_project_dir']
    if remote_local_copy is None:
        remote_local_copy = pcfg['project_root']
    cret = sync_remote_directory(host,
                                 project,
                                 directory,
                                 remote_directory=remote_directory,
                                 remote_local_copy=remote_local_copy,
                                 origin=origin,
                                 rev=rev,
                                 refresh=refresh,
                                 init=init,
                                 lremote=lremote,
                                 **kw)
    return cret


def remote_run_task(host, project, task=None, *args, **kw):
    '''
    Run a task from the .salt directory, remotely

    Task can be either given as a kwarg or the first positional argument.

    CLI Examples::


        salt-call --local mc_project.remote_run_task \
                host.fr <project> task=task_helloworld.sls
        salt-call --local mc_project.remote_run_task \
                host.fr <project> task_helloworld.sls
        salt-call --local mc_project.remote_run_task \
                host.fr <project> task_helloworld.sls a=b
    '''
    kw['salt_function'] = 'mc_project.run_task'
    kw['task'] = task
    return remote_deploy(host, project, *args, **kw)


def remote_task(host, project, *args, **kw):
    '''
    Alias to remote_run_task


    CLI Examples::

        salt-call --local mc_project.remote_task \
                host.fr <project> task=task_helloworld.sls
        salt-call --local mc_project.remote_task \
                host.fr <project> task_helloworld.sls
        salt-call --local mc_project.remote_task \
                host.fr <project> task_helloworld.sls a=b
    '''
    return remote_run_task(host, project, *args, **kw)


def remote_deploy(host, project, *args, **kw):
    '''

    Run a deployment task, remotely

    host
        host to deploy onto
    project
        project to deploy
    deploy_kwarg
        deploy kwargs
    deploy_args
        deploy arguments
    deploy_only_steps/only_steps
        set only_steps kwarg (shortcut)
    deploy_only/only
        set only kwarg (shortcut)
    salt_function
        salt deploy function (one of: mc_project.deploy/mc_project.run_task)

    CLI Examples::

        salt-call --local mc_project.remote_deploy \
                host.fr <project>
        salt-call --local mc_project.remote_deploy \
                host.fr <project> only=install,fixperms
        salt-call --local mc_project.remote_deploy \
                host.fr <project> only=install,fixperms only_steps=0.sls
    '''
    _s = __salt__
    _remote_log('   - Deployment: {2}{3}{0}/{1}'.format(host,
                                                        project,
                                                        _colors('endc'),
                                                        _colors('yellow')))
    ssh_kw = _s['mc_remote.ssh_kwargs'](kw)
    kwarg = kw.get('deploy_kwarg', kw.get('kwarg', {}))
    if not isinstance(kw, dict):
        kw = {}
    if not isinstance(kwarg, dict):
        kwarg = {}
    if isinstance(args, six.string_types):
        args = args.split()
    if not isinstance(args, list):
        args = []
    dargs = kw.get('deploy_args', [])
    if isinstance(dargs, six.string_types):
        dargs = dargs.split()
    if not isinstance(dargs, list):
        dargs = []
    args = copy.deepcopy(args)
    args.extend(copy.deepcopy(dargs))
    salt_function = kw.get('project_salt_function',
                           kw.get('salt_function', 'mc_project.deploy'))
    remote_deploy_supported_funs = ['mc_project.deploy', 'mc_project.run_task']
    do_raise = kw.get('do_raise', True)
    original = None
    scret = ''
    failed = False
    task = None
    extra_args = [
        pipes.quote(__salt__['mc_utils.magicstring'](a))
        for a in args]
    if salt_function not in remote_deploy_supported_funs:
        raise ValueError('{0} is not a valid function'.format(salt_function))
    if any([
        salt_function.endswith('.deploy'),
    ]):
        for opts in [
            ('deploy_only', 'only'),
            ('deploy_only_steps', 'only_steps')
        ]:
            for k in opts:
                if (
                    (k in kw)
                    and (k not in kwarg)
                    and (kw.get(k, None) is not None)
                ):
                    kwarg[k] = kw[k]
        # kwarg['only'] = 'install,fixperms'
        for k in ['only', 'only_steps']:
            if k not in kwarg:
                continue
            if isinstance(kwarg[k], list):
                kwarg[k] = ",".join(kwarg[k])
                _remote_log('''  {0}: {1}'''.format(k, kwarg[k]), 'yellow')
    if any([
        salt_function.endswith('.run_task')
    ]):
        task = kwarg.get('task', kw.get('task', None))
        if extra_args and not task:
            task = extra_args[0]
        elif task and not extra_args:
            extra_args = [task]
        if not extra_args:
            failed = True
            cret = scret = ('You must at least select a task as the'
                            ' first arg or via the task keyword parameter')
            original = ValueError(scret)
        else:
            if extra_args[0] != task:
                extra_args.inser(0, task)
            task = extra_args[0]
            extra_args = extra_args[1:]
    if not failed:
        try:
            cfgret = _s['mc_remote.salt_call'](
                host,
                'mc_project.get_configuration_item',
                arg=[project, 'git_deploy_hook'], kwarg=kwarg,
                **ssh_kw)
            hook = False
            if not cfgret['retcode']:
                hook = cfgret['result']['item']
            ssh_kw['ssh_display_content_on_error'] = True
            if hook:
                cmd = '"{0}" -p "{1}"'.format(hook, project)
                for i, sw in six.iteritems({
                    'only': 'only',
                    'only_steps': 'only-steps'
                }):
                    if i in kwarg:
                        cmd += ' --{0}="{1}"'.format(sw, kwarg[i])
                if task:
                    cmd += ' --task="{0}"'.format(task)
                if extra_args:
                    cmd += " {0}".format(" ".join(extra_args))
                cret = _s['mc_remote.ssh'](host, cmd, **ssh_kw)
                if cret['retcode']:
                    failed = True
                    scret = repr_ret(cret)
            if not hook:
                cret = _s['mc_remote.salt_call'](
                    host,
                    salt_function,
                    arg=[project] + extra_args, kwarg=kwarg,
                    **ssh_kw)
                if cret['retcode']:
                    failed = True
                    scret = repr_ret(cret)
        except (
            mc_states.saltapi.SSHExecError,
            salt.exceptions.CommandExecutionError,
            projects_api.ProjectNotCleanError
        ) as exc:

            original = exc
    msg, smsg = '', ''
    if do_raise and failed:
        msg, smsg = _remote_log(
            '   - Deployment {2}{3}{0}/{1}: {2}{4}FAILED'.format(
                host, project,
                _colors('endc'), _colors('yellow'), _colors('light_red')))
        lmsg, lsmsg = _remote_log(
            '   - Deployment {2}{3}{0}/{1}: {2}{4}FAILED'
            '\n{{scret}}'.format(
                host, project,
                _colors('endc'), _colors('yellow'), _colors('light_red')))
        raise_exc(
            projects_api.RemoteProjectDeployError,
            msg=msg,
            detail_msg=lmsg,
            scret=scret,
            cret=cret,
            host=host,
            original=original,
            project=project)
    else:
        msg, smsg = _remote_log(
            '   - Deployment {2}{3}{0}/{1}: {2}{4}OK'.format(
                host, project,
                _colors('endc'), _colors('yellow'), _colors('light_green')))
    cret['z_msg'] = msg
    return cret


def _remote_log(line,
                color='red',
                exact=False,
                output=True,
                level='debug'):
    line = _color_log(line, color, exact=exact)
    if output:
        print(line)
    stripped_line = mc_states.saltapi.strip_colors(line)
    getattr(log, level)(stripped_line)
    return line, stripped_line


def orchestrate(host,
                project,
                init=True,
                init_project=None,
                init_pillar=None,
                init_remote=True,
                sync=True,
                sync_project=None,
                sync_pillar=None,
                refresh=True,
                refresh_pillar=None,
                refresh_project=None,
                deploy=True,
                pillar_origin=None,
                pillar_rev=None,
                origin=None,
                rev=None,
                pre_init_hook=None,
                post_init_hook=None,
                pre_init_remote_hook=None,
                post_init_remote_hook=None,
                pre_sync_hook=None,
                deploy_fun='mc_project.remote_deploy',
                deploy_kwarg=None,
                deploy_args=None,
                post_sync_hook=None,
                pre_hook=None,
                post_hook=None,
                only=None,
                only_steps=None,
                **kw):
    '''
    Orchestrate a project deployment, remotely

    Note:

        a project is composed by it's code & deployment recipe (.salt)
        and it's pillar.

    This:

        - Run the pre init hook if any
        - initiliazes & prepare the code locally
        - Run the post init hook if any
        - Run the pre init remote hook if any
        - May initiliazes the remote project structure
        - Run the post init remote hook if any
        - Run the pre sync hook if any
        - Sync the code to remote buffer directories
        - Sync the remote deployment directories (pillar & project)
        - Run the post sync hook if any
        - Run the pre deploy hook if any
        - Run the deployment procedure (salt-call mc_project.deploy dance)
        - Run the post deploy hook if any


    The deployed code will at first be initialized:
        project code is initialized as either:
            - from an empty structure (shell helloworld)
            - from **git**:

                    origin
                        git url

                    rev
                        git remote tag/branch/changeset

            - from an empty structure (shell helloworld)

        pillar code is initialized as either:
            - from an empty structure (shell helloworld)
            - from **git**:

                    pillar_origin
                        git url

                    pillar_rev
                        git remote tag/branch/changeset

    If the urls were not specified, but the git repositories
    present in the local directories are valid, they will
    be deployed as-is.

    If the git repositories have a valid remote, the sync step
    will use it, even if the "origin/pillar_origin" were not
    specified explicitly

    host
        host where to deploy
    project
        project to deploy onto (name)
    init/init_project/init_pillar
        do we do the full init step
        do we do the init_project step (overrides init).
        do we do the init_pillar step (overrides init).
    init_remote
        do we do the init_remote step
    origin/pillar_origin
        url of the pillar to deploy if any (if None: empty pillar)
    rev/pillar_rev
        changeset if the project/pillar is from a git url (master)
    sync/sync_project/sync_pillar
        do we do the full sync step.
        do we do the sync_project step (overrides sync).
        do we do the sync_pillar step (overrides sync)
    refresh/refresh_project/refresh_pillar
        do we update the code prior to sync.
        do we do the refresh_project step (overrides refresh_project).
        do we do the refresh_project step (overrides refresh)
    deploy
        do we do the deploy step
    deploy_args
        any extra deploy/run_task positional argument
    deploy_kwarg
        any extra deploy/run_task extra argument
    pre_init_hook/post_init_hook/\
    pre_init_remote_hook/post_init_remote_hook/\
    pre_sync_hook/post_sync_hook/\
    pre_hook/post_hook
        deployment hook (see above lifecycle explaination & hook spec)
    only/only_steps
        mc_project.deploy deploy limits arguments(if any)

    An hook is a salt function, in any module with the following signature::

        def hook(host, project, opts, **kw)::
            print("hourray")

    Making in a execution module, /srv/salt/_module/foo.py::

        def hook(host, project, opts, **kw)::
            print("Called on {0}".format(host))

    Can be called like this::

        salt-call --local mc_project.orchestrate h proj init_hook=foo.hook

    CLI Examples::

        salt-call --local mc_project.orchestrate host.fr <project>\\
                origin="https://github.com/makinacorpus/corpus-pgsql.git"
        salt-call --local mc_project.orchestrate host.fr <project>\\
                origin="https://github.com/makinacorpus/corpus-pgsql.git"\\
                rev=stable\\
                pillar_origin="https://github.com/mak/corpus-pillar.git"\\
                rev=stable
        salt-call --local mc_project.orchestrate host.fr <project>\\
                origin="https://github.com/makinacorpus/corpus-pgsql.git"
        salt-call --local mc_project.orchestrate host.fr <project>\\
                deploy_args=['a'] \\
                origin="https://github.com/makinacorpus/corpus-pgsql.git"
        salt-call --local mc_project.orchestrate host.fr <project>\\
                deploy_kwarg={'myparam': 'a'} \\
                origin="https://github.com/makinacorpus/corpus-pgsql.git"

    '''
    _s = __salt__
    _remote_log('Deployment orchestration: {2}{3}{0}/{1}'.format(
        host, project, _colors('endc'), _colors('yellow')))
    pcfg = get_configuration(project, remote_host=host)
    user, group = get_default_user_group(**kw)
    kw['user'] = user
    kw['group'] = group
    crets = OrderedDict()
    kw['remote_config'] = pcfg
    if refresh_project is None:
        refresh_project = refresh
    if refresh_pillar is None:
        refresh_pillar = refresh
    if sync_project is None:
        sync_project = sync
    if sync_pillar is None:
        sync_pillar = sync
    if init_project is None:
        init_project = init
    if init_pillar is None:
        init_pillar = init
    if refresh is None:
        refresh = True
    sync_project = bool(sync_project)
    sync_pillar = bool(sync_pillar)
    init_project = bool(init_project)
    init_pillar = bool(init_pillar)
    refresh_pillar = bool(refresh_pillar)
    refresh_project = bool(refresh_project)
    # remake this available for hooks
    opts = OrderedDict()
    opts['pillar_origin'] = pillar_origin
    opts['pillar_rev'] = pillar_rev
    opts['origin'] = origin
    opts['rev'] = rev
    opts['sync_pillar'] = sync_pillar
    opts['sync_project'] = sync_project
    opts['init_pillar'] = init_pillar
    opts['init_project'] = init_project
    opts['refresh_pillar'] = refresh_pillar
    opts['refresh_project'] = refresh_project
    opts['only'] = only
    opts['only_steps'] = only_steps
    opts['deploy_args'] = deploy_args
    opts['deploy_kwarg'] = deploy_kwarg
    #
    if init_pillar or init_project:
        crets['init_pre'] = remote_project_hook(
            pre_init_hook, host, project, opts, **kw)
    if init_pillar:
        crets['init_pillar'] = init_local_remote_pillar(
            host, project, refresh=False,
            origin=pillar_origin, rev=pillar_rev,
            **kw)
    if init_project:
        crets['init_project'] = init_local_remote_project(
            host, project, refresh=False,
            origin=origin, rev=rev, **kw)
    if init_pillar or init_project:
        crets['init_post'] = remote_project_hook(
            post_init_hook, host, project, opts, **kw)
    if init_remote:
        crets['init_remote_pre'] = remote_project_hook(
            pre_init_remote_hook, host, project, opts, **kw)
        crets['init_remote_structure'] = init_remote_structure(
            host, project, **kw)
        crets['init_remote_post'] = remote_project_hook(
            post_init_remote_hook, host, project, opts, **kw)
    if init_pillar or init_project:
        crets['init_post'] = remote_project_hook(
            post_init_hook, host, project, opts, **kw)
    #
    if sync_pillar or sync_project:
        crets['sync_pre'] = remote_project_hook(
            pre_sync_hook, host, project, opts, **kw)
    if sync_pillar:
        crets['sync_pillar'] = sync_remote_pillar(
            host,
            project,
            origin=pillar_origin,
            rev=pillar_rev,
            init=False,
            refresh=refresh_pillar,
            **kw)
    if sync_project:
        crets['sync_project'] = sync_remote_project(
            host,
            project,
            origin=origin,
            rev=rev,
            refresh=refresh_project,
            init=False,
            **kw)
    if sync_pillar or sync_project:
        crets['sync_post'] = remote_project_hook(
            post_sync_hook, host, project, opts, **kw)
    #
    if deploy:
        ckw = copy.deepcopy(kw)
        ckw['only'] = only
        ckw['only_steps'] = only_steps
        ckw['deploy_kwarg'] = deploy_kwarg
        ckw['deploy_args'] = deploy_args
        crets['deploy_pre'] = remote_project_hook(
            pre_hook, host, project, opts, **ckw)
        crets['deploy'] = _s[deploy_fun](host, project, **ckw)
        crets['deploy_post'] = remote_project_hook(
            post_hook, host, project, opts, **ckw)
    msg, smsg = _remote_log(
        'Deployment orchestration: {2}{3}{0}/{1}:{2}{4} OK'.format(
            host, project,
            _colors('endc'), _colors('yellow'), _colors('light_green')))
    crets['z_msg'] = msg
    return crets


def orchestrate_task(host,
                     project,
                     task,
                     init=True,
                     init_project=None,
                     init_pillar=None,
                     init_remote=True,
                     sync=True,
                     sync_project=None,
                     sync_pillar=None,
                     refresh=True,
                     refresh_pillar=None,
                     refresh_project=None,
                     deploy=True,
                     deploy_args=None,
                     deploy_kwarg=None,
                     pillar_origin=None,
                     pillar_rev=None,
                     origin=None,
                     rev=None,
                     pre_init_hook=None,
                     post_init_hook=None,
                     pre_init_remote_hook=None,
                     post_init_remote_hook=None,
                     pre_sync_hook=None,
                     post_sync_hook=None,
                     pre_hook=None,
                     post_hook=None,
                     only=None,
                     only_steps=None,
                     **kw):
    '''
    Orchestrate a project through mc_project._orchestrate and use
    mc_project.remote_task <TASK NAME>

    CLI Examples::

        salt-call --local mc_project.orchestrate_task host.fr <project> task_make_users \\
                origin="https://github.com/makinacorpus/corpus-pgsql.git"
        salt-call --local mc_project.orchestrate host.fr <project> make_users\\
                origin="https://github.com/makinacorpus/corpus-pgsql.git" task_make_users\\
                rev=stable\\
                pillar_origin="https://github.com/mak/corpus-pillar.git" task_make_users\\
                rev=stable
        salt-call --local mc_project.orchestrate host.fr <project> task_make_users\\
                origin="https://github.com/makinacorpus/corpus-pgsql.git"
        salt-call --local mc_project.orchestrate host.fr <project> task_make_users\\
                deploy_args=['a'] \\
                origin="https://github.com/makinacorpus/corpus-pgsql.git"
        salt-call --local mc_project.orchestrate host.fr <project> task_make_users\\
                deploy_kwarg={'myparam': 'a'} \\
                origin="https://github.com/makinacorpus/corpus-pgsql.git"

    '''
    if isinstance(deploy_args, six.string_types):
        deploy_args = deploy_args.split()
    if not isinstance(deploy_args, list):
        deploy_args = []
    if task not in deploy_args:
        deploy_args.insert(0, task)
    return orchestrate(host,
                       project,
                       init=init,
                       init_project=init_project,
                       init_pillar=init_pillar,
                       init_remote=init_remote,
                       sync=sync,
                       sync_project=sync_project,
                       sync_pillar=sync_pillar,
                       refresh=refresh,
                       refresh_pillar=refresh_pillar,
                       refresh_project=refresh_project,
                       deploy=deploy,
                       pillar_origin=pillar_origin,
                       pillar_rev=pillar_rev,
                       origin=origin,
                       deploy_fun='mc_project.remote_task',
                       deploy_args=deploy_args,
                       deploy_kwarg=deploy_kwarg,
                       rev=rev,
                       pre_init_hook=pre_init_hook,
                       post_init_hook=post_init_hook,
                       pre_init_remote_hook=pre_init_remote_hook,
                       post_init_remote_hook=post_init_remote_hook,
                       pre_sync_hook=pre_sync_hook,
                       post_sync_hook=post_sync_hook,
                       pre_hook=pre_hook,
                       post_hook=post_hook,
                       only=only,
                       only_steps=only_steps,
                       **kw)


def remote_project_hook(hook, host, project, opts, **kw):
    '''
    Execute an hook

    An hook is a salt function, in any module with the following signature::

        def hook(host, project, opts, **kw)::
            print("hourray")
    '''

    if hook and (hook in __salt__):
        log.info('{0}/{1}: Running hook {2}'.format(
            host, project, hook))
        return __salt__[hook](host, project, opts, **kw)
