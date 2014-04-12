# -*- coding: utf-8 -*-
'''
.. _module_mc_project:

mc_project / project settings regitry switcher and common functions
=====================================================================

'''

from mc_states.project import LAST_PROJECT_API_VERSION
from mc_states import api


APIS = {
    'deploy': {
        '2': 'mc_project_2.deploy',
    },
    'init_project': {
        '2': 'mc_project_2.init_project',
    },
    'archive': {
        '2': 'mc_project_2.archive',
    },
    'release_sync': {
        '2': 'mc_project_2.release_sync',
    },
    'configure': {
        '2': 'mc_project_2.configure',
    },
    'build': {
        '2': 'mc_project_2.build',
    },
    'reconfigure': {
        '2': 'mc_project_2.reconfigure',
    },
    'activate': {
        '2': 'mc_project_2.activate',
    },
    'upgrade': {
        '2': 'mc_project_2.upgrade',
    },
    'bundle': {
        '2': 'mc_project_2.bundle',
    },
    'post_install': {
        '2': 'mc_project_2.post_install',
    },
    'notify': {
        '2': 'mc_project_2.notify',
    },
    'rollback': {
        '2': 'mc_project_2.rollback',
    },
    'get_configuration': {
        '1': 'mc_project_1.get_configuration',
        '2': 'mc_project_2.get_configuration',
    },
    'set_configuration': {
        '2': 'mc_project_2.set_configuration',
    },
}


def _api_switcher(module, name, *args, **kwargs):
    '''Get the right module:

            - from explicitly given api
            - from local project configuration
            - fallback on last API
    '''
    try:
        api_ver = kwargs.pop('api_ver')
    except KeyError:
        api_ver = __salt__['mc_utils.get'](
            'makina-projects.{0}.api_version'.format(name),
            LAST_PROJECT_API_VERSION)
    mod = APIS[module]["{0}".format(api_ver)]
    return __salt__[mod](name, *args, **kwargs)


def get_configuration(name, *args, **kwargs):
    return _api_switcher('get_configuration', name, *args, **kwargs)


def set_configuration(name, *args, **kwargs):
    return _api_switcher('set_configuration', name, *args, **kwargs)


def init_project(name, *args, **kwargs):
    return _api_switcher('init_project', name, *args, **kwargs)


def deploy(name, *args, **kwargs):
    return _api_switcher('deploy', name, *args, **kwargs)


def archive(name, *args, **kwargs):
    return _api_switcher('archive', name, *args, **kwargs)


def release_sync(name, *args, **kwargs):
    return _api_switcher('release_sync', name, *args, **kwargs)


def configure(name, *args, **kwargs):
    return _api_switcher('configure', name, *args, **kwargs)


def build(name, *args, **kwargs):
    return _api_switcher('build', name, *args, **kwargs)


def reconfigure(name, *args, **kwargs):
    return _api_switcher('reconfigure', name, *args, **kwargs)


def activate(name, *args, **kwargs):
    return _api_switcher('activate', name, *args, **kwargs)


def upgrade(name, *args, **kwargs):
    return _api_switcher('upgrade', name, *args, **kwargs)


def bundle(name, *args, **kwargs):
    return _api_switcher('bundle', name, *args, **kwargs)


def post_install(name, *args, **kwargs):
    return _api_switcher('post_install', name, *args, **kwargs)


def doc_root(doc_root=None,
             domain=None,
             project_root=None,
             project=None,
             relative_document_root='www'):
    if not doc_root:
        if not domain and not project:
            raise Exception('Need at least one of domain or project')
        if not project:
            project = gen_id(domain)
        if not project_root:
            project_root = '{0}/{1}/project'.format(
                __salt__['mc.locations.settings']()['projects_dir'], project)
        doc_root = '{0}/{1}'.format(project_root,
                                    relative_document_root)
    return doc_root


def uniquify(seq):
    return api.uniquify(seq)


def gen_id(id):
    return id.replace('.', '-')


def server_aliases(value):
    if not isinstance(value, list):
        value = value.split()
    return value


def get_common_vars(*args, **kwargs):
    '''Retro compat, wrapper to get_configuration'''
    return __salt__['mc_project_1.get_configuration'](*args, **kwargs)
#
