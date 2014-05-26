# -*- coding: utf-8 -*-
'''
.. _module_mc_project_2:

mc_project_2 / project settings regitry APIV2
================================================

'''
import datetime
import os
import logging
import socket
import sys
import traceback
import uuid
import yaml


import copy
from salt.utils.odict import OrderedDict
from salt.states import group as sgroup
from salt.states import user as suser
from salt.states import file as sfile
from salt.states import git as sgit
from salt.states import cmd as scmd
import salt.output
import salt.loader
import salt.utils

from mc_states.utils import is_valid_ip
from mc_states.api import (
    splitstrip,
    msplitstrip,
    indent,
    uniquify,
)

import mc_states.project
from mc_states.project import (
    EDITABLE_MODE,
    COOKING_MODE,
    FINAL_MODE,
    ENVS,
    DEFAULTS_SKIPS,
    ProjectInitException,
    ProjectProcedureException,
)


logger = logging.getLogger(__name__)


API_VERSION = '2'
PROJECT_INJECTED_CONFIG_VAR = 'cfg'


DEFAULT_CONFIGURATION = {
    'api_version': API_VERSION,
    'url': 'https://github.com/makinacorpus/{name}.git',
    'pillar_url': 'https://github.com/makinacorpus/{name}-pillar.git',
    'release_artifacs_urls': [],
    #
    'project_branch': 'master',
    'pillar_branch': 'master',
    #
    'installer': 'generic',
    #
    'project_dir': '{projects_dir}/{name}',
    'project_root': '{project_dir}/project',
    'deploy_marker': '{project_root}/.tmp_deploy',
    'salt_root': '{project_root}/.salt',
    'pillar_root': '{project_dir}/pillar',
    'data_root': '{project_dir}/data',
    'deploy_root': '{project_dir}/deploy',
    'archives_root': '{project_dir}/archives',
    'releases_root': '{project_dir}/releases',
    'build_root': '{project_dir}/build',
    'git_root': '{project_dir}/git',
    'project_git_root': '{git_root}/project.git',
    'pillar_git_root': '{git_root}/pillar.git',
    'current_archive_dir': None,
    'current_release_dir': None,
    'main_ip': '127.0.0.1',
    'domain': '{name}.local',
    'domains': None,
    #
    'rollback': False,
    #
    'full': True,
    'default_env': None,
    'operation_mode': None,
    'run_mode': '',
    #
    'user': None,
    'groups': [],
    #
    'defaults': {},
    'env_defaults': {},
    'no_domain': False,
    'os_defaults': {},
    #
    'sls_includes': [],
    #
    'no_user': False,
    'no_reset_perms': False,
    'no_default_includes': False,
    #
    'raw_console_return': False,
    'notify_methods': [],
    #
    'deploy_summary': None,
    'deploy_ret': {},
    'force_reload': False,
    'data': {},
}
STEPS = [
    'deploy',
    'archive',
    'release_sync',
    'configure',
    'build',
    'upgrade',
    'activate',
    'reconfigure',
    'bundle',
    'post_install',
    'rollback',
    'notify',
]

for step in STEPS:
    DEFAULT_CONFIGURATION['skip_{0}'.format(step)] = None


def _state_exec(*a, **kw):
    return __salt__['mc_state.sexec'](*a, **kw)


def _stop_proc(message, step, ret):
    ret['raw_comment'] = message
    ret['result'] = False
    raise ProjectProcedureException(ret['raw_comment'],
                                    salt_step=step,
                                    salt_ret=ret)


def _check_proc(message, step, ret):
    if not ret['result']:
        _stop_proc(message, step, ret)


def _filter_ret(ret, raw=False):
    if not raw and 'raw_comment' in ret:
        del ret['raw_comment']
    return ret


def _outputters(outputter=None):
    outputters = salt.loader.outputters(__opts__)
    if outputter:
        return outputters[outputter]
    return outputters


def _hs(mapping, raw=False):
    color = __opts__.get('color', None)
    __opts__['color'] = not raw
    ret = _outputters('highstate')({'local': mapping})
    __opts__['color'] = color
    return ret


def _raw_hs(mapping):
    return _hs(mapping, raw=True)


def _force_cli_retcode(ret):
     # cli codeerr = 3 in case of failure
     if not ret['result']:
         __context__['retcode'] = 3
     else:
         __context__['retcode'] = 0


def _sls_exec(name, cfg, sls):
    # be sure of the current project beeing loaded in the context
    set_project(cfg)
    cfg = get_project(name)
    ret = _get_ret(name)
    ret.update({'return': None, 'sls': sls, 'name': name})
    old_retcode = __context__.get('retcode', 0)
    cret = __salt__['state.sls'](sls.format(**cfg))
    ret['return'] = cret
    comment = ''
    __context__.setdefault('retcode', 0)
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
                if not state.get('result', False):
                    failed = True
            if failed:
                __context__['retcode'] = 3
                ret['result'] = False
    if __context__['retcode'] > 0:
        ret['result'] = False
        body = ''
        if isinstance(cret, list):
            body += indent(cret)
        _append_comment(ret,
                        'Running {1} for {0} failed:'.format(name, sls),
                        body=body)
    if cret and isinstance(cret, dict):
        _append_comment('SLS execution result of {0} for {1}:'.format(sls,
                                                                      name))
        ret['raw_comment'] += indent(_raw_hs(copy.deepcopy(cret)))
        ret['comment'] += indent(_hs(copy.deepcopy(cret)))
    msplitstrip(ret)
    return ret


def _get_ret(name, *args, **kwargs):
    ret = kwargs.get('ret', None)
    if ret is None:
        ret = {'comment': '',
               'raw_comment': '',
               'result': True,
               'changes': {},
               'name': name}
    return ret


def _colors(color=None):
    colors = salt.utils.get_colors(__opts__.get('color'))
    if color:
        return colors[color]
    return colors


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


def _append_separator(ret, separator='--', separator_color='LIGHT_CYAN'):
    if not 'raw_comment' in ret:
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


def get_default_configuration():
    return copy.deepcopy(DEFAULT_CONFIGURATION)


def _defaultsConfiguration(
    cfg,
    default_env,
    defaultsConfiguration=None,
    env_defaults=None,
    os_defaults=None
):
    salt = __salt__
    if defaultsConfiguration is None:
        defaultsConfiguration = {}
    if os_defaults is None:
        os_defaults = {}
    if env_defaults is None:
        env_defaults = {}
    os_defaults.setdefault(__grains__['os'], {})
    os_defaults.setdefault(__grains__['os_family'], {})
    for k in ENVS:
        env_defaults.setdefault(k, {})
    defaultsConfiguration = salt['mc_utils.dictupdate'](
        defaultsConfiguration,
        salt['grains.filter_by'](
            env_defaults, grain='non_exising_ever_not', default=default_env))
    defaultsConfiguration = salt['mc_utils.dictupdate'](
        defaultsConfiguration,
        salt['grains.filter_by'](os_defaults, grain='os_family'))
    # retro compat 'foo-default-settings'
    defaultsConfiguration = salt['mc_utils.defaults'](
        '{name}-default-settings'.format(**cfg), defaultsConfiguration)
    # new location 'makina-projects.foo.data'
    defaultsConfiguration = salt['mc_utils.defaults'](
        'makina-projects.{name}.data'.format(**cfg), defaultsConfiguration)
    return defaultsConfiguration


def _merge_statuses(ret, cret, step=None):
    for d in ret, cret:
        if not 'raw_comment' in d:
            d['raw_comment'] = ''
    _append_separator(ret)
    if cret['result'] is False:
        ret['result'] = False
    if cret.get('changes', {}) and ('changes' in ret):
        ret['changes'].update(cret)
    if step:
        ret['comment'] += '\n{3}Execution step:{2} {1}{0}{2}'.format(
            step, _colors('YELLOW'), _colors('ENDC'), _colors('RED'))
        ret['raw_comment'] += '\nExecution step: {0}'.format(cret)
    for k in ['raw_comment', 'comment']:
        if k in cret:
            ret[k] += '\n{{{0}}}'.format(k).format(**cret)
    if not ret['result']:
        _append_comment(ret,
                        summary='Deployment aborted due to error',
                        color='RED')
    return ret


def _init_context():
    if not 'ms_projects' in __opts__:
        __opts__['ms_projects'] = OrderedDict()
    if not 'ms_project_name' in __opts__:
        __opts__['ms_project_name'] = None
    if not 'ms_project' in __opts__:
        __opts__['ms_project'] = None


def set_project(cfg):
    _init_context()
    __opts__['ms_project_name'] = cfg['name']
    __opts__['ms_project'] = cfg
    __opts__['ms_projects'][cfg['name']] = cfg
    return cfg


def get_project(name):
    '''Alias of get_configuration for convenience'''
    return get_configuration(name)


def _get_contextual_cached_project(name):
    _init_context()
    # throw KeyError if not already loaded
    cfg = __opts__['ms_projects'][__opts__['ms_project_name']]
    __opts__['ms_project'] = cfg
    __opts__['ms_project_name'] = cfg['name']
    return cfg


def get_configuration(name, *args, **kwargs):
    """
    Return a configuration data structure needed data for
    the project API macros and configurations functions
    project API 2

    name
        name of the project
    url
        the git repository url
    pillar_url
        the git repository pillar_url
    release_artifacs_urls
        URLs to or archives to grab and extract in the deploy folder
        on the final mode
    installer
        the sls files container to installer this is either

            a string without slashs
                this is one installer found in
                the makina-states/projects/<APIVER> directory
                (some valid values: generic zope)

            a string beginning with slashs
                This one is an installer found on the filesystem
                (/path/to/my/dir)

            a string with slashs
                This one is an installer found relativly in the project
                salt root directory (<project_root>/.salt/mydir)
                string without slashs

    default_env
        environnemt to run into (may be dev|prod, better
        to set a grain see bellow)
    operation_mode
        Operation mode (editable, cooking, final)
    project_root
        where to install the project,
    git_root
        root dir for git repositories
    main_ip
        main ip tied to this environment
    domain
        main domain of the installed application if any
    domains
        Additionnal hosts (mapping {host: ip}),
        the main domain will be inserted
    pillar_root
        pillar local dir
    salt_root
        salt local dir
    archives_root
        archives directory
    data_root
        persistent data root
    deploy_root
        deployment directory
    project_git_root
        project local git dir
    pillar_git_root
        pillar local git dir
    full
        set to false to only run the sole project states and not a full
        highstate
    project_branch
        the branch of the project
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

    no_reset_perms
        Do not run fixpermissions
    no_domain
        Do not manage the domains in /etc/hosts

    notify_methods
        which method(s) do we use to notify users about system changes

    rollback
        do we rollback at the end of all processes

    skip_deploy
        Skip the deploy step
    skip_archive
        Skip the archive step
    skip_release_sync
        Skip the release_sync step
    skip_configure
        Skip the configure step
    skip_build
        Skip the build step if any
    skip_reconfigure
        Skip the reconfigure step
    skip_activate
        Skip the activate step
    skip_upgrade
        Skip the upgrade step
    skip_bundle
        Skip the bundle install step if any
    skip_rollback
        Skip the rollback step if any
    skip_notify
        Skip the notify step if any
    skip_post_install
        Skip the post install step

    You can override the non read only default variables
    by pillar/grain like::

        salt grain.setval makina-projects.foo.url 'http://goo/goo.git
        salt grain.setval makina-projects.foo.default_env prod

    You can override the non read only default arbitrary attached defaults
    by pillar/grain like::

        /srv/projects/foo/pillar/init.sls:

        makina-projects.foo.data.conf_port = 1234

    """
    try:
        cfg = _get_contextual_cached_project(name)
        if cfg['force_reload'] or kwargs.get('force_reload', False):
            raise KeyError('reload me!')
        return cfg
    except KeyError:
        pass
    cfg = get_default_configuration()
    cfg['name'] = name
    cfg.update(dict([a
                     for a in kwargs.items()
                     if a[0] in cfg]))
    # we must also ignore keys setted on the call to the function
    # which are explictly setting a value
    ignored_keys = [
        'data',
        'rollback',
    ]
    for k in kwargs:
        if k in cfg:
            ignored_keys.append(k)
    nodetypes_reg = __salt__['mc_nodetypes.registry']()
    salt_settings = __salt__['mc_salt.settings']()
    salt_root = salt_settings['saltRoot']
    if cfg['domains'] is None:
        cfg['domains'] = {}
    if isinstance(cfg['domains'], basestring):
        cfg['domains'] = cfg['domains'].split()
    if isinstance(cfg['domains'], list):
        cfg['domains'] = dict([(a, a)
                               for a in cfg['domains']])
    for adomain in list(cfg['domains']):
        tied_ip = cfg['domains'][adomain]
        # check if it is an hostname and then try to resolve it or
        # let it as an ip
        if not is_valid_ip(tied_ip):
            try:
                hostname, alias, ipaddrlist = socket.gethostbyaddr(tied_ip)
                if ipaddrlist:
                    cfg['domains'][adomain] = ipaddrlist[0]
                else:
                    cfg['domains'][adomain] = cfg['main_ip']
            except Exception:
                # mark this domain as localhost
                cfg['domains'][adomain] = cfg['main_ip']

    if not cfg['no_default_includes']:
        cfg['sls_includes'].extend([
            'makina-states.projects.hooks',
        ])
    cfg['sls_includes'] = uniquify(cfg['sls_includes'])
    if not cfg['default_env']:
        # one of:
        # - makina-projects.fooproject.default_env
        # - fooproject.default_env
        # - default_env
        cfg['default_env'] = __salt__['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(name, 'default_env'),
            __salt__['mc_utils.get'](
                '{0}.{1}'.format(name, 'default_env'),
                __salt__['mc_utils.get']('default_env', 'dev')))
    if not cfg['full'] and not cfg['run_mode']:
        cfg['run_mode'] = '-standalone'
    if not cfg['operation_mode']:
        if cfg['default_env'] in ['prod']:
            cfg['operation_mode'] = FINAL_MODE
        elif cfg['default_env'] in ['staging',
                                    'test',
                                    'qa',
                                    'preprod']:
            cfg['operation_mode'] = COOKING_MODE
        else:
            cfg['operation_mode'] = EDITABLE_MODE

    # set default skippped steps on a specific environment
    # to let them maybe be overriden in pillar
    for val, skips in DEFAULTS_SKIPS.get(
        cfg['operation_mode'], DEFAULTS_SKIPS[EDITABLE_MODE]
    ).items():
        for skip in skips:
            dval = cfg.get(skip, None)
            if dval is None:
                dval = val
            if not dval:
                dval = False
            cfg[skip] = val
    if not cfg['user']:
        cfg['user'] = '{name}-user'
    if not cfg['groups']:
        cfg['groups'].append(__salt__['mc_usergroup.settings']()['group'])
    cfg['groups'] = uniquify(cfg['groups'])
    # those variables are overridable via pillar/grains
    overridable_variables = [
        'release_artifacs_urls',
        'notify_methods',
        'operation_mode',
        'default_env',
        'no_user',
        'no_reset_perms',
        'no_default_includes',
    ]
    for step in STEPS:
        ignored_keys.append('skip_{0}'.format(step))
    # we can override many of default values via pillar/grains
    for k in overridable_variables:
        if k in ignored_keys:
            continue
        cfg[k] = __salt__['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(name, k), cfg[k])
    cfg['data'] = _defaultsConfiguration(cfg,
                                         cfg['default_env'],
                                         defaultsConfiguration=cfg['defaults'],
                                         env_defaults=cfg['env_defaults'],
                                         os_defaults=cfg['os_defaults'])
    # some vars need to be setted just a that time
    cfg['group'] = cfg['groups'][0]
    cfg['projects_dir'] = __salt__['mc_locations.settings']()['projects_dir']

    # finally resolve the format-variabilized dict key entries in
    # arbitrary conf mapping
    cfg['data'] = __salt__['mc_utils.format_resolve'](cfg['data'])
    cfg['data'] = __salt__['mc_utils.format_resolve'](cfg['data'], cfg)

    # finally resolve the format-variabilized dict key entries in global conf
    cfg.update(__salt__['mc_utils.format_resolve'](cfg))
    cfg.update(__salt__['mc_utils.format_resolve'](cfg, cfg['data']))

    # we can try override default values via pillar/grains a last time
    # as format_resolve can have setted new entries
    # we do that only on the global data level and on non read only vars
    if 'data' not in ignored_keys:
        ignored_keys.append('data')
    cfg.update(
        __salt__['mc_utils.defaults'](
            'makina-projects.{0}'.format(name),
            cfg, ignored_keys=ignored_keys))
    now = datetime.datetime.now()
    cfg['chrono'] = '{0}_{1}'.format(
        datetime.datetime.strftime(now, '%Y-%m-%d_%H_%M-%S'),
        str(uuid.uuid4()))
    cfg['current_release_dir'] = os.path.join(
        cfg['releases_root'], cfg['chrono'])
    cfg['current_archive_dir'] = os.path.join(
        cfg['archives_root'], cfg['chrono'])

    # special symlinks inside salt wiring
    cfg['wired_salt_root'] = os.path.join(
        salt_settings['saltRoot'], 'makina-projects', cfg['name'])
    cfg['wired_pillar_root'] = os.path.join(
        salt_settings['pillarRoot'], 'makina-projects', cfg['name'])
    # check if the specified sls installer files container
    # exists
    if '/' not in cfg['installer']:
        installer_path = os.path.join(
            salt_root, 'makina-states/projects/{0}/{1}'.format(
                cfg['api_version'], cfg['installer']))
        if not os.path.exists(installer_path):
            raise ProjectInitException('invalid project type: {0}'.format(
                cfg['installer']))
    # notify methods
    if cfg['operation_mode'] in [EDITABLE_MODE]:
        cfg['notify_methods'].append('stdout')
    if cfg['operation_mode'] in [FINAL_MODE, COOKING_MODE]:
        cfg['notify_methods'].append('mail')
    # check for all sls to be in there
    cfg['installer_path'] = installer_path
    # put the result inside the context
    set_project(cfg)
    return cfg


def _get_filtered_cfg(cfg):
    ignored_keys = [
        'data',
        'name'
        'notify_methods',
        'rollback',
    ]
    to_save = {}
    for sk in cfg:
        val = cfg[sk]
        if sk.startswith('__pub'):
            continue
        if sk in ignored_keys:
            continue
        if isinstance(val, OrderedDict) or isinstance(val, dict):
            continue
        to_save[sk] = val
    return to_save


def set_configuration(name, cfg=None, *args, **kwargs):
    '''set or update a local (grains) project configuration'''
    if not cfg:
        cfg = get_configuration(name, *args, **kwargs)
    __salt__['grains.setval']('makina-projects.{0}'.format(name),
                              _get_filtered_cfg(cfg))
    return get_configuration(name)


def init_user_groups(user, groups=None, ret=None):
    _append_comment(
        ret, summary='Verify user:{0} & groups:{1} for project'.format(
            user, groups))
    _s = __salt__.get
    if not groups:
        groups = []
    if not ret:
        ret = _get_ret(user)
    # create user if any
    for g in groups:
        if not _s('group.info')(g):
            cret = _state_exec(sgroup, 'present', g, system=True)
            if not cret['result']:
                raise ProjectInitException('Can\'t manage {0} group'.format(g))
            else:
                _append_comment(ret, body=indent(cret['comment']))
    if not _s('user.info')(user):
        cret = _state_exec(suser, 'present',
                           user,
                           shell='/bin/bash',
                           gid_from_name=True,
                           remove_groups=False,
                           optional_groups=groups)
        if not cret['result']:
            raise ProjectInitException(
                'Can\'t manage {0} user'.format(user))
        else:
            _append_comment(ret, body=indent(cret['comment']))
    return ret


def init_project_dirs(cfg, ret=None):
    _s = __salt__.get
    if not ret:
        ret = _get_ret(cfg['name'])
    _append_comment(ret, summary=(
        'Initialize or verify core '
        'project layout for {0}').format(cfg['name']))
    # create various directories
    for dr, mode in [
        (cfg['git_root'], '770'),
        (cfg['archives_root'], '770'),
        (cfg['releases_root'], '770'),
        (os.path.dirname(cfg['wired_pillar_root']), '770'),
        (os.path.dirname(cfg['wired_salt_root']), '770'),
        (cfg['deploy_root'], '770'),
        (cfg['build_root'], '770'),
    ]:
        cret = _state_exec(sfile,
                           'directory',
                           dr,
                           makedirs=True,
                           user=cfg['user'],
                           group=cfg['group'],
                           mode='750')
        if not cret['result']:
            raise ProjectInitException(
                'Can\'t manage {0} dir'.format(dr))
        else:
            _append_comment(ret, body=indent(cret['comment']))
    for symlink, target in (
        (cfg['wired_salt_root'], cfg['salt_root']),
        (cfg['wired_pillar_root'], cfg['pillar_root']),
    ):
        cret = _state_exec(sfile, 'symlink', symlink, target=target)
        if not cret['result']:
            raise ProjectInitException(
                'Can\'t manage {0} -> {1} symlink\n{2}'.format(
                    symlink, target, cret))
        else:
            _append_comment(ret, body=indent(cret['comment']))
    return ret


def init_ssh_user_keys(user, failhard=False, ret=None):
    '''Copy root keys from root to a user
    to allow user to share the same key than root to clone distant repos.
    This is useful in vms (local PaaS vm)
    '''
    _append_comment(
        ret, summary='SSH keys management for {0}'.format(user))
    cmd = '''
home="$(awk -F: -v v="{user}" '{{if ($1==v && $6!="") print $6}}' /etc/passwd)";
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
home="$(awk -F: -v v="{user}" '{{if ($1==v && $6!="") print $6}}' /etc/passwd)";
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
    _s = __salt__.get
    cret = _state_exec(scmd, 'run', cmd, onlyif=onlyif, stateful=True)
    if failhard and not cret['result']:
        raise ProjectInitException('SSH keys improperly configured\n'
                                   '{0}'.format(cret))
    else:
        _append_comment(ret, body=indent('SSH keys in place if any'))
    return ret


def init_hooks(name, git, user, group, deploy_hooks=False,
               ret=None, bare=True, api_version=2):
    _s = __salt__.get
    if not ret:
        ret = _get_ret(user)
    _append_comment(
        ret, summary='Git Hooks for {0}'.format(git))
    lgit = git
    if not bare:
        lgit = os.path.join(lgit, '.git')
    cret = _state_exec(sfile, 'managed',
                       name=os.path.join(lgit, 'hooks/pre-receive'),
                       source=(
                           'salt://makina-states/files/projects/2/'
                           'hooks/pre-receive'),
                       defaults={'api_version': api_version, 'name': name},
                       user=user, group=group, mode='750', template='jinja')
    cret = _state_exec(sfile, 'managed',
                       name=os.path.join(lgit, 'hooks/post-receive'),
                       source=(
                           'salt://makina-states/files/projects/2/'
                           'hooks/post-receive'),
                       defaults={'api_version': api_version, 'name': name},
                       user=user, group=group, mode='750', template='jinja')
    cret = _state_exec(sfile, 'managed',
                       name=os.path.join(lgit, 'hooks/deploy_hook.py'),
                       source=(
                           'salt://makina-states/files/projects/2/'
                           'hooks/deploy_hook.py'),
                       defaults={'api_version': api_version, 'name': name},
                       user=user, group=group, mode='750')
    if not cret['result']:
        raise ProjectInitException(
        'Can\'t set git hooks for {0}\n{1}'.format(git, cret['comment']))
    else:
        _append_comment(ret, body=indent(cret['comment']))

def init_bare_repo(git, user, group, deploy_hooks=False, ret=None, bare=True, api_version=2):
    _s = __salt__.get
    if not ret:
        ret = _get_ret(user)
    _append_comment(
        ret, summary='Bare repository managment in {0}'.format(git))
    lgit = git
    if not bare:
        lgit = os.path.join(lgit, '.git')
    if os.path.exists(lgit):
        cmd = 'chown -Rf {0} "{2}"'.format(user, group, git)
        cret = _s('cmd.run_all')(cmd)
        if cret['retcode']:
            raise ProjectInitException(
                'Can\'t set perms for {0}'.format(git))
    parent = os.path.dirname(git)
    cret = _state_exec(sfile, 'directory',
                       parent,
                       makedirs=True,
                       user=user,
                       group=group,
                       mode='770')
    if not cret['result']:
        raise ProjectInitException(
            'Can\'t manage {0} dir'.format(git))
    else:
        _append_comment(ret, body=indent(cret['comment']))
    # initialize an empty git
    cret = _state_exec(sgit,
                       'present',
                       git,
                       user=user,
                       bare=bare,
                       force=True)
    if not cret['result']:
        raise ProjectInitException(
            'Can\'t manage {0} dir'.format(git))
    else:
        _append_comment(ret, body=indent(cret['comment']))
    if len(os.listdir(lgit + '/refs/heads')) < 1:
        if bare:
            cret = _s('cmd.run_all')(
                ('git clone "{0}" "{0}.tmp" &&'
                 ' cd "{0}.tmp" &&'
                 ' touch .empty &&'
                 ' git config user.email "makinastates@paas.tld" &&'
                 ' git config user.name "makinastates" &&'
                 ' git add .empty &&'
                 ' git commit -am initial &&'
                 ' git push origin -u master &&'
                 ' rm -rf "{0}.tmp"').format(lgit),
                runas=user
            )
        else:
            cret = _s('cmd.run_all')(
                ('cd "{0}" && touch .empty &&'
                 ' git config user.email "makinastates@paas.tld" &&'
                 ' git config user.name "makinastates" &&'
                 ' git add .empty &&'
                 ' git commit -am initial').format(git),
                runas=user
            )
        if cret['retcode']:
            raise ProjectInitException(
                'Can\'t add first commit in {0}'.format(git))
        else:
            _append_comment(
                ret, body=indent('Commited first commit in {0}'.format(git)))
    return ret


def init_local_repository(wc,
                          url,
                          user,
                          group,
                          ret=None):
    _s = __salt__.get
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
        raise ProjectInitException(
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
        raise ProjectInitException(
            'Can\'t initialize git dir  {0} dir'.format(wc))
    else:
        _append_comment(ret, body=indent(cret['comment']))


def init_set_remotes(wc, user, url, localgit, ret=None):
    _s = __salt__.get
    _append_comment(
        ret, summary=(
            'Set remotes in {0}\n'
            '    remote: {2}\n'
            '    local: {1}\n'
            ''.format(
                wc, url, localgit)))
    if not ret:
        ret = _get_ret(user)
    # add the local and distant remotes
    for remote, lurl in (('origin', url),
                         ('local', localgit)):
        cret = _s('git.remote_set')(wc, remote, lurl, user=user)
        if not cret:
            raise ProjectInitException(
                'Can\'t initialize git remote '
                '{0} from {1} in {2}'.format(
                    remote, lurl, wc))
        else:
            _append_comment(ret,
                            body=indent('Remote {0} -> {1} set'.format(
                                remote, lurl)))
    return ret


def init_bare_set_remotes(wc, user, url, localgit, ret=None):
    _s = __salt__.get
    _append_comment(
        ret, summary=(
            'Set remotes in {0}\n'
            '    remote: {2}\n'
            '    local: {1}\n'
            ''.format(
                localgit, url, wc)))
    if not ret:
        ret = _get_ret(user)
    # add the local and distant remotes
    for remote, lurl in (('origin', url),
                         ('local', wc)):
        cret = _s('git.remote_set')(localgit, remote, lurl, user=user)
        if not cret:
            raise ProjectInitException(
                'Can\'t initialize git local remote '
                '{0} from {1} in {2}'.format(
                    remote, lurl, wc))
        else:
            _append_comment(ret,
                            body=indent('LocalRemote {0} -> {1} set'.format(
                                remote, lurl)))
    return ret


def init_fetch_last_commits(wc, user, operation_mode, ret=None):
    _s = __salt__.get
    if not ret:
        ret = _get_ret(user)
    origin = get_local_origin()
    _append_comment(
        ret, summary=(
            'Fetch last commits from {1} in working copy: {0}'.format(
                wc, origin)))
    for origin in ['local', 'origin']:
        cret = _s('cmd.run_all')(
            'git fetch {0}'.format(origin), cwd=wc, runas=user)
    if cret['retcode']:
        raise ProjectInitException(
            'Can\'t fetch git in {0}'.format(wc))
    else:
        out = splitstrip('{stdout}\n{stderr}'.format(**cret))
        _append_comment(ret, body=indent(out))
    return ret


def get_local_origin(operation_mode):
    if operation_mode in [EDITABLE_MODE]:
        origin = 'origin'
    else:
        origin = 'local'
    return origin


def init_set_upstream(wc, operation_mode, rev, user, ret=None):
    _s = __salt__.get
    origin = get_local_origin()
    _append_comment(
        ret, summary=(
            'Set upstream: {2}/{1} in {0}'.format(
                wc, rev, origin)))
    # set branch upstreams
    if _s('cmd.run_all')('git --version')['stdout'].split()[-1] < '1.8':
        cret2 = _s('cmd.run_all')(
            'git branch --set-upstream master {1}/{0}'.format(
                rev, origin), cwd=wc, runas=user)
        cret1 = _s('cmd.run_all')(
            'git branch --set-upstream {0} {1}/{0}'.format(rev, origin),
            cwd=wc, runas=user)
        out = splitstrip('{stdout}\n{stderr}'.format(**cret2))
        _append_comment(ret, body=indent(out))
        out = splitstrip('{stdout}\n{stderr}'.format(**cret1))
        _append_comment(ret, body=indent(out))
        if cret2['retcode'] or cret1['retcode']:
            raise ProjectInitException(
                'Can\'t set upstreams for {0}'.format(wc))
    else:
        cret = _s('cmd.run_all')(
            'git branch --set-upstream-to={1}/{0}'.format(rev, origin),
            cwd=wc, runas=user)
        out = splitstrip('{stdout}\n{stderr}'.format(**cret))
        _append_comment(ret, body=indent(out))
        if not cret:
            raise ProjectInitException(
                'Can not set upstream from {2} -> {0}/{1}'.format(
                    origin, rev, wc))

    return ret


def init_sync_working_copies(operation_mode,
                             user,
                             wc,
                             rev,
                             localgit,
                             url=None,
                             ret=None,
                             origin=None):
    _s = __salt__.get
    if not ret:
        ret = _get_ret(wc)
    if origin is None:
        origin = 'origin'
        if operation_mode not in [EDITABLE_MODE]:
            origin = 'local'
    _append_comment(
        ret, summary=(
            'Synchronize working copy {0} from upstream {2}/{1}'.format(
                wc, rev, origin)))
    if operation_mode not in [EDITABLE_MODE]:
        cret = _s('git.reset')(
            wc, '--hard {1}/{0}'.format(rev, origin),
            user=user)
        # in all but dev mode, we use the local remote
        # where users have pushed the code
        if not cret:
            raise ProjectInitException(
                'Can not sync from {1}@{0} in {2}'.format(
                    url, rev, wc))
        else:
            _append_comment(
                ret, body=indent('Repository {1}: {0}\n'.format(cret, wc)))
    else:
        lret = _state_exec(
            sgit, 'latest', url, target=wc, rev=rev, user=user)
        cret = _s('cmd.run_all')(
            'git log --pretty=format:"%h:%s:%an"', cwd=wc, runas=user)
        out = splitstrip('{stdout}\n{stderr}'.format(**cret))
        lines = out.splitlines()
        initial = False
        if len(lines) == 1:
            if 'makinastates' in lines[0]:
                initial = True
        # the local copy is not yet synchronnized with any repo
        if initial or (
            os.listdir(wc) == ['.git']
        ) or (
            not lret['result']
            and 'ambiguous argument \'HEAD\'' in lret['comment']
        ):
            cret = _s('git.reset')(
                wc, '--hard {1}/{0}'.format(rev, origin),
                user=user)
            # in dev mode, no local repo, but we sync it anyway
            # to avoid bugs
            if not cret:
                raise ProjectInitException(
                    'Can not sync from {1}@{0} in {2}'.format(
                        url, rev, wc))
            else:
                _append_comment(
                    ret, body=indent('Repository {1}: {0}\n'.format(cret, wc)))
        else:
            changes = lret['changes']
            if not changes:
                changes = 'Repository {0}: up to date'.format(wc)
            if not lret['result']:
                raise ProjectInitException(
                    'There is something wrong with git update in {0},\n'
                    'you should verify that there is no '
                    'conflict, cherry-pick\n'
                    'or rebase to resolve or any other problem'.format(wc))
            _append_comment(ret, body=indent('{0}\n{1}'.format(lret['comment'],
                                                               changes)))
            cret = _s('cmd.run_all')(
                'cd {1};git fetch local;'
                'cat refs/remotes/local/master>refs/heads/master;'
                'git symbolic-ref HEAD refs/heads/master'.format(
                    rev, localgit),
                cwd=wc,
                runas=user)
            out = splitstrip('{stdout}\n{stderr}'.format(**cret))
            _append_comment(ret, body=indent(out))
    return ret


def init_salt_dir(cfg, ret=None):
    _s = __salt__.get
    if not ret:
        ret = _get_ret(cfg['name'])
    _append_comment(
        ret, summary='Verify or initialise salt & pillar core files')
    user, group = cfg['user'], cfg['group']
    pillar_root = cfg['pillar_root']
    salt_root = cfg['salt_root']
    parent = os.path.dirname(salt_root)
    if not os.path.exists(parent):
        raise ProjectInitException(
            'parent for salt root {0} does not exist'.format(parent))
    cret = _state_exec(sfile, 'directory',
                       salt_root,
                       user=user,
                       group=group,
                       mode='770')
    if not cret['result']:
        raise ProjectInitException(
            'Can\'t manage {0} dir'.format(salt_root))
    else:
        _append_comment(ret, body=indent(cret['comment']))
    files = [os.path.join(salt_root, '{0}.sls'.format(a))
             for a in STEPS]
    for fil in files:
        template = (
            'salt://makina-states/files/projects/{1}/salt/{0}'.format(
                os.path.basename(fil), cfg['api_version']))
        if os.path.exists(fil):
            continue
        cret = _state_exec(sfile, 'managed',
                           name=fil, source=template,
                           defaults={'name': cfg['name'],
                                     'url': cfg['url'],
                                     'pillar_url': cfg['pillar_url']},
                           user=user, group=group, mode='770', template='jinja')
        if not cret['result']:
            raise ProjectInitException(
                'Can\'t create default {0}\n{1}'.format(fil, cret['comment']))
        else:
            _append_comment(ret, body=indent(cret['comment']))
    files = [
        os.path.join(pillar_root, 'init.sls'),
    ]
    for step in STEPS:
        if not os.path.exists(
            os.path.join(cfg['salt_root'], '{0}.sls'.format(step))
        ):
            raise ProjectInitException(
                'Missing step sls {0}.sls in {1}'.format(step,
                                                         cfg['salt_root']))
    for fil in files:
        # if pillar is empty, create it
        if os.path.exists(fil):
            with open(fil) as fic:
                if fic.read().strip():
                    continue
        template = (
            'salt://makina-states/files/projects/2/pillar/{0}'.format(
                os.path.basename(fil)))
        init_data = _get_filtered_cfg(cfg)
        for k in [a for a in init_data]:
            if k not in [
                "api_version",
                "pillar_branch",
                "pillar_url",
                "project_branch",
                "url",
            ]:
                del init_data[k]
        defaults = {
            'name': cfg['name'],
            'cfg': yaml.dump(
                {
                    'makina-projects.{name}'.format(
                        **cfg): init_data
                },  width=80, indent=2, default_flow_style=False
            ),
        }
        cret = _state_exec(sfile, 'managed',
                           name=fil, source=template,
                           defaults=defaults,
                           user=user, group=group, mode='770', template='jinja')
        if not cret['result']:
            raise ProjectInitException(
                'Can\'t create default {0}\n{1}'.format(fil, cret['comment']))
        else:
            _append_comment(ret, body=indent(cret['comment']))
    salt_settings = __salt__['mc_salt.settings']()
    pillar_root = os.path.join(salt_settings['pillarRoot'])
    pillar_top = 'makina-projects.{name}'.format(**cfg)
    pillarf = os.path.join(pillar_root, 'top.sls')
    with open(pillarf) as fpillarf:
        pillars = fpillarf.read()
        if not pillar_top in pillars:
            lines = []
            for line in pillars.splitlines():
                lines.append(line)
                if line == "  '*':":
                    lines.append('    - {0}\n'.format(pillar_top))
            with open(pillarf, 'w') as wpillarf:
                wpillarf.write('\n'.join(lines))
            _append_comment(
                ret, body=indent(
                    'Added to pillar top: {0}'.format(cret['name'])))
    return ret


def refresh_hooks(*args, **kwargs):
    pass


def init_project(name, *args, **kwargs):
    '''
    See common args to feed the neccessary variables to set a project
    You will need at least:

        - A name
        - A type
        - The pillar git repository url
        - The project & salt git repository url

    '''
    _s = __salt__.get
    cfg = get_configuration(name, *args, **kwargs)
    user, groups, group = cfg['user'], cfg['groups'], cfg['group']
    operation_mode = cfg['operation_mode']
    ret = _get_ret(cfg['name'])
    try:
        init_user_groups(user, groups, ret=ret)
        init_ssh_user_keys(user,
                           failhard=operation_mode in [EDITABLE_MODE],
                           ret=ret)
        init_project_dirs(cfg, ret=ret)
        project_git_root = cfg['project_git_root']
        pillar_git_root = cfg['pillar_git_root']
        for git in [project_git_root, pillar_git_root]:
            init_bare_repo(git, user, group, ret=ret, bare=True)
            init_hooks(name, git, user, group, ret=ret, bare=True,
                       api_version=cfg['api_version'])
        for wc, url, rev, localgit in [
            (
                cfg['pillar_root'],
                cfg['pillar_url'],
                cfg['pillar_branch'],
                pillar_git_root,
            ),
            (
                cfg['project_root'],
                cfg['url'],
                cfg['project_branch'],
                project_git_root,
            ),
        ]:
            init_bare_repo(wc, user, group, ret=ret, bare=False)
            init_hooks(name, wc, user, group, ret=ret, bare=False,
                       api_version=cfg['api_version'])
            init_bare_set_remotes(wc, user, url, localgit, ret=ret)
            init_set_remotes(wc, user, url, localgit, ret=ret)
            init_fetch_last_commits(wc, user, operation_mode, ret=ret)
            init_set_upstream(wc, operation_mode, rev, user, ret=ret)
            init_sync_working_copies(
                operation_mode, user, wc, rev, localgit, url=url, ret=ret)
        init_salt_dir(cfg, ret=ret)
    except ProjectInitException, ex:
        trace = traceback.format_exc()
        ret['result'] = False
        _append_comment(ret, summary="{0}".format(ex), body=trace)
    if ret['result']:
        set_configuration(cfg['name'], cfg)
    msplitstrip(ret)
    return _filter_ret(ret, cfg['raw_console_return'])


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
        rollback = cfg['operation_mode'] not in [EDITABLE_MODE]
        # XXX: remove me (True)!
        # rollback = True
    if not error_msg:
        error_msg = ''
    step = step_or_steps[0]
    try:
        try:
            for step in step_or_steps:
                cret = __salt__['mc_project_{1}.{0}'.format(
                    step, cfg['api_version'])](name, *args, **kwargs)
                _merge_statuses(ret, cret, step=step)
        except ProjectProcedureException, pr:
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
            'exception in step {2}.\n'
            '{1}').format(name, ex, step.capitalize(), step)
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


def deploy(name, *args, **kwargs):
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
    if ret['result']:
        guarded_step(cfg, ['release_sync',
                           'configure',
                           'build',
                           'reconfigure',
                           'activate',
                           'upgrade',
                           'bundle',
                           'post_install'],
                     rollback=True,
                     inner_step=True,
                     ret=ret)
    # if the rollback flag has been raised, just do a rollback
    # only rollback if the minimum to rollback is there
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
    guarded_step(cfg, 'notify', ret=ret, *args, **kwargs)
    ret['result'] = result
    _force_cli_retcode(ret)
    return _filter_ret(ret, cfg['raw_console_return'])


def archive(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'archive')
    return cret


def release_sync(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    iret = init_project(name, *args, **kwargs)
    if iret['result']:
        cret = _step_exec(cfg, 'release_sync')
        iret = _merge_statuses(iret, cret)
    return iret


def configure(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'configure')
    return cret


def build(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'build')
    return cret


def reconfigure(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'reconfigure')
    return cret


def activate(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'activate')
    return cret


def upgrade(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'upgrade')
    return cret


def bundle(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'bundle')
    return cret


def post_install(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'post_install')
    #raise Exception('foo')
    return cret


def rollback(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'rollback')
    return cret


def notify(name, *args, **kwargs):
    cfg = get_configuration(name, *args, **kwargs)
    cret = _step_exec(cfg, 'notify')
    return cret
#
