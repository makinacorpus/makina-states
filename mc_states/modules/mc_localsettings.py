# -*- coding: utf-8 -*-
'''

.. _module_mc_localsettings:

mc_localsettings / localsettings variables
============================================
'''

# Import salt libs
import mc_states.utils
import re

__name = 'localsettings'


def metadata():
    '''metadata registry for localsettings'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](__name)
    return _metadata()


def _get_ldapVariables(saltmods):
    return saltmods['mc_ldap.settings']()


def _ldapEn(__salt__):
    return __salt__['mc_ldap.ldapEn'](__salt__)


def settings():
    '''settings registry for localsettings

    **OBSOLETE, PLEASE USE LOCAL REGISTRIES**
    **MOST MAKINA STATES CORE IS ALREADY MIGRATED**

    WILL DISAPPEAR IN A NEAR FUTURE
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = {}
        saltmods = __salt__  # affect to a var to see further pep8 errors
        pillar = __pillar__
        resolver = saltmods['mc_utils.format_resolve']
        data['resolver'] = resolver
        data['grainsPref'] = 'makina-states.localsettings.'
        data['default_env'] = saltmods['mc_env.settings']()['env']
        data['locations'] = saltmods['mc_locations.settings']()
        data['etckeeper'] = saltmods['mc_etckeeper.settings']()

        data['timezoneSettings'] = saltmods['mc_timezone.settings']()
        data['rotate'] = saltmods['mc_logrotate.settings']()

        # LDAP integration
        data['ldapVariables'] = saltmods['mc_ldap.settings']()
        data['ldapEn'] = data['ldapVariables']['enabled']

        data['nodejsSettings'] = saltmods['mc_nodejs.settings']()
        data['pythonSettings'] = saltmods['mc_python.settings']()
        # user management
        data.update(saltmods['mc_usergroup.settings']())
        data.update(saltmods['mc_network.settings']())

        # retro compat wrappers
        data['pkgSettings'] = saltmods['mc_pkgs.settings']()
        data['installmode'] = data['pkgSettings']['installmode']
        data['keyserver'] = data['pkgSettings']['keyserver']
        data['dist'] = data['pkgSettings']['dist']
        data['dcomps'] = data['pkgSettings']['apt']['debian']['comps']
        data['ddist'] = data['pkgSettings']['apt']['debian']['dist']
        data['debian_mirror'] = data['pkgSettings']['apt']['debian']['mirror']
        data['debian_stable'] = data['pkgSettings']['apt']['debian']['stable']
        data['ubuntu_last'] = data['pkgSettings']['apt']['ubuntu']['last']
        data['ubuntu_lts'] = data['pkgSettings']['apt']['ubuntu']['lts']
        data['ubuntu_mirror'] = data['pkgSettings']['apt']['ubuntu']['mirror']
        data['ucomps'] = data['pkgSettings']['apt']['ubuntu']['comps']
        data['udist'] = data['pkgSettings']['apt']['ubuntu']['dist']
        data['lts_dist'] = data['pkgSettings']['lts_dist']

        # JDK default version
        data['jdkSettings'] = saltmods['mc_java.settings']()
        data['jdkDefaultVer'] = data['jdkSettings']['default_jdk_ver']

        data['rvmSettings'] = rvmSettings = saltmods['mc_rvm.settings']()
        data['rvm_url'] = rvmSettings['url']
        data['rubies'] = rvmSettings['rubies']
        data['rvm_user'] = rvmSettings['user']
        data['rvm_group'] = rvmSettings['group']

        data['SSLSettings'] = saltmods['mc_ssl.settings']()
        localesdef = saltmods['mc_locales.settings']()
        data['locales'] = localesdef['locales']
        data['default_locale'] = localesdef['locale']
        # expose any defined variable to the callees
        return data
    return _settings()


def registry():
    '''registry registry for localsettings'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        has_nodejs = __salt__['mc_utils.get'](
            'makina-states.localsettings.nodejs', False)
        reg = __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'nscd': {'active': _ldapEn(__salt__)},
            'ldap': {'active': _ldapEn(__salt__)},
            'git': {'active': True},
            'hosts': {'active': True},
            'jdk': {'active': False},
            'etckeeper': {'active': True},
            'locales': {'active': True},
            'localrc': {'active': True},
            'timezone': {'active': True},
            'network': {'active': True},
            'nodejs': {'active': False},
            'npm': {'active': has_nodejs},
            'pkgmgr': {'active': True},
            'python': {'active': False},
            'pkgs': {'active': True},
            'repository_dotdeb': {'active': False},
            'shell': {'active': True},
            'sudo': {'active': True},
            'groups': {'active': True},
            'sysctl': {'active': True},
            'users': {'active': True},
            'vim': {'active': True},
            'rvm': {'active': False},
        })
        return reg
    return _registry()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
