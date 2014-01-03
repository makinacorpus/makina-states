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


def get_metadata(
    services,
    name,
    salt_subdir='salt',
    default_env=None,
    project_subdir='project',
    salt_branch='salt',
    project_branch='master',
    pillar_subdir='pillar',
    url='https://github.com/makinacorpus/{name}.git'
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

    You can override default states values by pillar/grain like::

        salt grain.setval makina-projects.foo.url 'http://goo/goo.git
        salt grain.setval makina-projects.foo.default_env prod

    Or in pillar::

        /srv/projects/foo/pillar/init.sls:
        makina-projects.foo.url: http://goo/goo.git
        makina-projects.foo.default_env: prod

    """
    localsettings = services.localsettings
    if not default_env:
        d = __salt__['mc_utils.get']('default_env', 'dev')
        default_env = __salt__['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(*(name, 'default_env')), d)
    variables = {
        'services': services,
        'default_env': default_env,
        'name': name,
        'salt_subdir': salt_subdir,
        'project_subdir': project_subdir,
        'salt_branch': salt_branch,
        'project_branch': project_branch,
        'pillar_subdir': pillar_subdir,
        'url': url
    }
    # we can override default values via pillar/grains
    for k, d in variables.items():
        variables[k] = __salt__['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(*(name, k)), d)
    data = __salt__['mc_utils.format_resolve'](
        {
            'name': name,
            'root': localsettings.locations['projects_dir'],
            'project_dir': '{root}/{name}',
            'salt_root':    '{project_dir}/{salt_subdir}',
            'project_root': '{project_dir}/{project_subdir}',
            'pillar_root':  '{project_dir}/{salt_subdir}',
            'salt_branch': salt_branch,
            'project_branch': project_branch,
            'default_env': default_env,
            'url': url,
        }, variables)
    data = __salt__['mc_utils.format_resolve'](data)
    # we can override default values via pillar/grains
    for k, d in data.items():
        variables[k] = __salt__['mc_utils.get'](
            'makina-projects.{0}.{1}'.format(*(name, k)), d)
    return data

#
