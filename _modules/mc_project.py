# -*- coding: utf-8 -*-
'''
Some usefull small tools
=========================

'''

import unittest
# Import salt libs
import salt.utils
import os
import salt.utils.dictupdate
from salt.exceptions import SaltException

_default_activation_status = object()


def _defaultsData(
    common,
    defaults=None,
    env_defaults=None,
    os_defaults=None
):
    if defaults is None:
        defaults = {}
    if os_defaults is None:
        os_defaults = {'Debian': {}}
    if env_defaults is None:
        env_defaults = {'dev': {}}
    dataGetterStepOne = __salt__['grains.filter_by'](
        env_defaults, grain='default_env', default='dev', merge=defaults)
    dataGetterStepTwo = __salt__['grains.filter_by'](
        os_defaults, grain='os_family', merge=dataGetterStepOne)
    defaultsData = __salt__['mc_utils.dictupdate'](
        dataGetterStepTwo,
        __salt__['pillar.get'](common['name'] + '-default-settings', {})
    )
    return defaultsData

def get_common_vars(
    services,
    name,
    salt_subdir='salt',
    default_env=None,
    project_subdir='project',
    salt_branch='salt',
    project_branch='master',
    pillar_subdir='pillar',
    user=None,
    group=None,
    url='https://github.com/makinacorpus/{name}.git',
    domain='localhost',
    main_ip='127.0.0.1',
    domains=None,
    defaults=None,
    env_defaults=None,
    os_defaults=None,
    sls_includes=None
):
    """
    Return all needed data for the project API macro:

        - services: the loaded services jinja macro
        - name: name of the project
        - default_env: environnemt to run into (may be dev|prod, better
          to set a grain, see bellow)
        - project_subdir: the subdirectory of the project in /srv/projects/foo
        - salt_subdir: the subdirectory of the salt in /srv/salts/foo
        - pillar_subdir: the subdirectory of the pillar in /srv/pillars/foo
        - project_branch: the branch of the project
        - salt_branch: the branch of the project salt tree
        - url: the git repository url
        - domain: main domain of the installed application if any
        - domains: Additionnal hosts (mapping {host: ip}), the main domain will be inserted
                 in this list linked to the 'main_ip'.
        - user: system project user
        - group: system project user group
        - defaults: data mapping for this project to use in states as common.data
        - env_defaults: per environment (eg: prod|dev)  specific defaults data
        - os_defaults: per os (eg: Ubuntu/Debian)  specific defaults data
        - sls_includes: includes to add to the project top includes statement

    You can override default states values by pillar/grain like::

        salt grain.setval makina-projects.foo.url 'http://goo/goo.git
        salt grain.setval makina-projects.foo.default_env prod

    Or in pillar::

        /srv/projects/foo/pillar/init.sls:
        makina-projects.foo.url: http://goo/goo.git
        makina-projects.foo.default_env: prod

    """
    default_sls_includes = [
        'makina-states.controllers.salt_minion',
        'makina-states.services.base.ssh',
        'makina-states.localsettings.hosts',
    ]

    if not sls_includes:
        sls_includes = []

    for i in default_sls_includes:
        if not i in sls_includes:
            sls_includes.append(i)
    if 'vagrantvm' in services.nodetypes.registry['actives']:
        sls_includes.append('makina-states.nodetypes.vagrantvm')

    localsettings = services.localsettings
    if not default_env:
        d = __salt__['mc_utils.get']('default_env', 'dev')
        default_env = __salt__['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(*(name, 'default_env')), d)
    if not user:
        user = '{name}-user'
    if not group:
        group = localsettings.group

    if not domains:
        domains = {}

    if isinstance(domain, basestring):
        domains[domain] = main_ip

    variables = {
        'services': services,
        'localsettings': localsettings,
        'default_env': default_env,
        'name': name,
        'domains': domains,
        'domain': domain,
        'main_ip': main_ip,
        'user': user,
        'group': group,
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
        defaults=defaults,
        env_defaults=env_defaults,
        os_defaults=os_defaults)

    data = __salt__['mc_utils.format_resolve'](
        {
            'services': services,
            'localsettings': localsettings,
            'name': name,
            'domain': domain,
            'domains': domains,
            'root': localsettings.locations['projects_dir'],
            'project_dir': '{root}/{name}',
            'salt_root':    '{project_dir}/{salt_subdir}',
            'project_root': '{project_dir}/{project_subdir}',
            'pillar_root':  '{project_dir}/{pillar_subdir}',
            'salt_branch': salt_branch,
            'project_branch': project_branch,
            'default_env': default_env,
            'user': user,
            'group': group,
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

#
