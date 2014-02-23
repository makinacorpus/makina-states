# -*- coding: utf-8 -*-
'''
.. _module_mc_project:

mc_project / project settings regitry
======================================

'''

# Import salt libs

_default_activation_status = object()
from mc_states.utils import is_valid_ip
import socket


def uniquify(seq):
    seen = set()
    return [x
            for x in seq
            if x not in seen and not seen.add(x)]


def _defaultsData(
    common,
    default_env,
    defaultsData=None,
    env_defaults=None,
    os_defaults=None
):
    salt = __salt__
    if defaultsData is None:
        defaultsData = {}
    if os_defaults is None:
        os_defaults = {'Debian': {}}
    if env_defaults is None:
        env_defaults = {'dev': {}, 'prod': {}}
        env_defaults.setdefault(default_env, {})
    defaultsData = salt['mc_utils.dictupdate'](
        defaultsData,
        salt['grains.filter_by'](
            env_defaults, grain='non_exising_ever_not', default=default_env))
    defaultsData = salt['mc_utils.dictupdate'](
        defaultsData,
        salt['grains.filter_by'](os_defaults, grain='os_family'))
    defaultsData = salt['mc_utils.defaults'](
        common['name'] + '-default-settings', defaultsData)
    return defaultsData


def get_common_vars(
    name,
    salt_subdir='salt',
    default_env=None,
    project_subdir='project',
    salt_branch='salt',
    project_branch='master',
    pillar_subdir='pillar',
    user=None,
    groups=None,
    salt_root='{project_dir}/salt',
    project_root='{project_dir}/project',
    pillar_root='{project_dir}/pillar',
    url='https://github.com/makinacorpus/{name}.git',
    domain='{name}.local',
    domains=None,
    main_ip='127.0.0.1',
    defaults=None,
    env_defaults=None,
    os_defaults=None,
    sls_includes=None,
    no_user=False,
    no_salt=False,
    full=True,
    no_domain=False,
    no_reset_perms=False,
    no_default_includes=False,
    *args, **kwargs
):

    """
    Return all needed data for the project API macro:

    services
        the loaded services jinja macro
    name
        name of the project
    default_env
        environnemt to run into (may be dev|prod, better
        to set a grain see bellow)
    project_subdir
        the subdirectory of the project in /srv/projects/foo
    salt_root
        where to install the salt branch
    project_root
        where to install the project,
    salt_subdir
        the subdirectory of the salt in /srv/salts/foo
    pillar_subdir
        the subdirectory of the pillar in /srv/pillars/foo
    full
        set to false to only run the sole project states and not a full highstate
    project_branch
        the branch of the project
    salt_branch
        the branch of the project salt tree
    url
        the git repository url
    domain
        main domain of the installed application if any
    domains
        Additionnal hosts (mapping {host: ip}), the main domain will be inserted
        in this list linked to the 'main_ip'.
    user
        system project user
    groups
        system project user groups, first group is main
    defaults
        data mapping for this project to use in states as common.data
    env_defaults
        per environment (eg: prod|dev)  specific defaults data
    os_defaults
        per os (eg: Ubuntu/Debian)  specific defaults data
    sls_includes
        includes to add to the project top includes statement
    no_salt
        Do not manage the salt branch
    no_domain
        Do not manage the domains in /etc/hosts
    no_reset_perms
        Do not run fixpermissions
    no_default_includes
        Do not add salt_minon & other bases sls
        like ssh to default includes

    You can override default states values by pillar/grain like::

        salt grain.setval makina-projects.foo.url 'http://goo/goo.git
        salt grain.setval makina-projects.foo.default_env prod

    Or in pillar::

        /srv/projects/foo/pillar/init.sls:
        makina-projects.foo.url: http://goo/goo.git
        makina-projects.foo.default_env: prod

    """
    runmode = not full and '-standalone' or ''
    nodetypes_reg = __salt__['mc_nodetypes.registry']()
    localsettings = __salt__['mc_localsettings.settings']()
    if domains is None:
        domains = {}
    if groups is None:
        groups = []
    if not sls_includes:
        sls_includes = []
    if full:
        sls_includes = (
            ['makina-states.services.base.ssh-users',
             'makina-states.localsettings.hosts']
            + sls_includes)
    if not no_default_includes:
        sls_includes.extend([
            'makina-states.controllers.salt-hooks',
            'makina-states.projects.hooks',
        ])
        if nodetypes_reg['has']['vagrantvm']:
            sls_includes.append(
                'makina-states.nodetypes.vagrantvm-standalone')
    sls_includes = uniquify(sls_includes)

    if not default_env:
        # one of:
        # - makina-projects.fooproject.default_env
        # - fooproject.default_env
        # - default_env
        default_env = __salt__['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(name, 'default_env'), 
            __salt__['mc_utils.get']('{0}.{1}'.format(name, 'default_env'), 
            __salt__['mc_utils.get']('default_env', 'dev')))
    if not user:
        user = '{name}-user'
    if not groups:
        groups.append(localsettings['group'])
    groups = uniquify(groups)
    if isinstance(domains, basestring):
        domains = domains.split()
    if isinstance(domains, list):
        domains = dict([(a, a) for a in domains])
    for adomain in list(domains):
        tied_ip = domains[adomain]
        # check if it is an hostname and then try to resolve it or
        # let it as an ip
        if not is_valid_ip(tied_ip):
            try:
                hostname, alias, ipaddrlist = socket.gethostbyaddr(tied_ip)
                if ipaddrlist:
                    domains[adomain] = ipaddrlist[0]
                else:
                    domains[adomain] = main_ip
            except Exception:
                # mark this domain as localhost
                domains[adomain] = main_ip
    if isinstance(domain, basestring):
        domains[domain] = main_ip
    variables = {
        'full': full,
        'default_env': default_env,
        'name': name,
        'domains': domains,
        'alternate_domains': [a for a in domains if not a == domain],
        'domain': domain,
        'main_ip': main_ip,
        'user': user,
        'group': groups[0],
        'groups': groups,
        'salt_subdir': salt_subdir,
        'project_subdir': project_subdir,
        'salt_branch': salt_branch,
        'project_branch': project_branch,
        'pillar_subdir': pillar_subdir,
        'url': url,
        'sls_includes': sls_includes,
    }
    # we can override default values via pillar/grains
    for k, d in variables.items():
        variables[k] = __salt__['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(*(name, k)), d)
    defaultsData = _defaultsData(
        variables,
        default_env,
        defaultsData=defaults,
        env_defaults=env_defaults,
        os_defaults=os_defaults)
    data = __salt__['mc_utils.format_resolve'](
        {
            'no_user': no_user,
            'no_salt': no_salt,
            'no_domain': no_domain,
            'no_reset_perms': no_reset_perms,
            'name': name,
            'domain': domain,
            'domains': domains,
            'alternate_domains': [a for a in domains if not a == domain],
            'projects_dir': localsettings['locations']['projects_dir'],
            'project_dir': '{projects_dir}/{name}',
            'salt_root':    salt_root,
            'project_root': project_root,
            'pillar_root': pillar_root,
            'salt_branch': salt_branch,
            'project_branch': project_branch,
            'default_env': default_env,
            'user': user,
            'full': full,
            'groups': groups,
            'group': groups[0],
            'url': url,
            'data': defaultsData,
            'sls_includes': sls_includes,
        }, variables)
    data = __salt__['mc_utils.format_resolve'](data)
    # we can try override default values via pillar/grains a last time
    for k, d in data.items():
        variables[k] = __salt__['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(*(name, k)), d)
    return data


def gen_id(id):
    return id.replace('.', '-')


def doc_root(doc_root=None,
             domain=None,
             project_root=None,
             project=None,
             relative_document_root='www'):
    localsettings = __salt__['mc_localsettings.settings']()
    if not doc_root:
        if not domain and not project:
            raise Exception('Need at least one of domain or project')
        if not project:
            project = gen_id(domain)
        if not project_root:
            project_root = '{0}/{1}/project'.format(
                localsettings['locations']['projects_dir'], project)
        doc_root = '{0}/{1}'.format(project_root,
                                    relative_document_root)
    return doc_root


def server_aliases(value):
    if not isinstance(value, list):
        value = value.split()
    return value
#
