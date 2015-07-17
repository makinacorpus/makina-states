# -*- coding: utf-8 -*-
'''

.. _module_mc_localsettings:

mc_localsettings / localsettings variables
============================================
'''

# Import salt libs
import mc_states.api
import re

__name = 'localsettings'
ipsan = re.compile('(\.|-|_)', re.M | re.U)
slssan1 = re.compile('(minions\.)?(old|bm|(vm)(\.(lxc|kvm))?)\.([^.]*\.)?')
slssan2 = re.compile(
    '(makina-states.cloud\.)?(compute_nodes?|(vms?)(\.(lxc|kvm))?)\.')
# this is one of the core regs, we cant cache it
# using the regular cache funcs
_reg = {}


def metadata():
    '''metadata registry for localsettings'''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](__name)
    return _metadata()


def _get_ldapVariables(_s):
    return _s['mc_ldap.settings']()


def _ldapEn(__salt__):
    return __salt__['mc_ldap.ldapEn'](__salt__)


def settings(ttl=15*60):
    '''settings registry for localsettings

    **OBSOLETE, PLEASE USE LOCAL REGISTRIES**
    **MOST MAKINA STATES CORE IS ALREADY MIGRATED**

    WILL DISAPPEAR IN A NEAR FUTURE
    '''
    if not _reg:
        data = {}
        _s = __salt__  # affect to a var to see further pep8 errors
        data['grainsPref'] = 'makina-states.localsettings.'
        data['default_env'] = _s['mc_env.settings']()['env']
        data['locations'] = _s['mc_locations.settings']()
        data['etckeeper'] = _s['mc_etckeeper.settings']()

        data['timezoneSettings'] = _s['mc_timezone.settings']()
        data['rotate'] = _s['mc_logrotate.settings']()

        # LDAP integration
        data['ldapVariables'] = _s['mc_ldap.settings']()
        data['ldapEn'] = data['ldapVariables']['enabled']

        data['nodejsSettings'] = _s['mc_nodejs.settings']()
        data['pythonSettings'] = _s['mc_python.settings']()
        # user management
        data.update(_s['mc_usergroup.settings']())
        data.update(_s['mc_network.settings']())

        # retro compat wrappers
        data['pkgSettings'] = _s['mc_pkgs.settings']()
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
        data['jdkSettings'] = _s['mc_java.settings']()
        data['jdkDefaultVer'] = data['jdkSettings']['default_jdk_ver']

        data['rvmSettings'] = rvmSettings = _s['mc_rvm.settings']()
        data['rvm_url'] = rvmSettings['url']
        data['rubies'] = rvmSettings['rubies']
        data['rvm_user'] = rvmSettings['user']
        data['rvm_group'] = rvmSettings['group']

        data['SSLSettings'] = _s['mc_ssl.settings']()
        localesdef = _s['mc_locales.settings']()
        data['locales'] = localesdef['locales']
        data['default_locale'] = localesdef['locale']
        # expose any defined variable to the callees
        _reg.update(data)
    return _reg


def apparmor_en():
    ret = False
    is_docker = __salt__['mc_nodetypes.is_docker']()
    is_travis = __salt__['mc_nodetypes.is_travis']()
    if __grains__['os'] in ['Ubuntu']:
        ret = True
    return ret and not (is_docker or is_travis)


def registry(ttl=15*60):
    '''registry registry for localsettings'''
    def _do():
        has_nodejs = __salt__['mc_utils.get'](
            'makina-states.localsettings.nodejs', False)
        is_docker = __salt__['mc_nodetypes.is_docker']()
        is_travis = __salt__['mc_nodetypes.is_travis']()
        # only some services will be fully done  on mastersalt side if any
        # in scratch mode, deactivating all default configuration for services
        true = not __salt__['mc_nodetypes.is_scratch']()
        reg = {
            'env': {'active': true},
            'systemd': {'active': true},
            'autoupgrade': {'active': true and not is_docker},
            'apparmor': {'active': true and apparmor_en()},
            'updatedb': {'active': true},
            'nscd': {'active': true and _ldapEn(__salt__)},
            'ldap': {'active': true and _ldapEn(__salt__)},
            'grub': {'active': False},
            'git': {'active': true},
            'dns': {'active': False},
            'hosts': {'active': true and not (is_travis or is_docker)},
            'jdk': {'active': False},
            'etckeeper': {'active': true and not (is_travis or is_docker)},
            'locales': {'active': true},
            'localrc': {'active': true},
            'desktoptools': {'active': False},
            'mvn': {'active': False},
            'timezone': {'active': true},
            'network': {'active': true and not (is_travis or is_docker)},
            'nodejs': {'active': False},
            'npm': {'active': has_nodejs},
            'pkgs.mgr': {'active': true},
            'casperjs': {'active': False},
            'phantomjs': {'active': False},
            'python': {'active': False},
            'pkgs.basepackages': {'active': true},
            'repository_dotdeb': {'active': False},
            'check_raid': {'active': False},
            'shell': {'active': true},
            'sudo': {'active': true},
            'groups': {'active': true},
            'sysctl': {'active': true},
            'ssl': {'active': true},
            'users': {'active': true},
            'screen': {'active': true},
            'vim': {'active': true},
            'rvm': {'active': False}}
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        if 'laptop' in nodetypes_registry['actives']:
            reg.update({'desktoptools': {'active': true},
                        'npm': {'active': true},
                        'nodejs': {'active': true},
                        'jdk': {'active': true},
                        'rvm': {'active': true}})
        reg = __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults=reg)
        return reg
    cache_key = 'mc_localsettings.registry'
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_pillar_fqdn(sls, template):
    '''
    if template name is none, it is a directly
    accessed sls (rendered from a string), here
    we can guess the name from sls
    sls does not have '.' it is a directly
    '''
    fqdn = sls
    tname = template._TemplateReference__context.name
    if tname:
        fqdn = tname
    if '/' in fqdn:
        fqdn = fqdn.split('/')[-1]
    # remove any .sls extension
    fqdn = re.sub('\.sls$', '', fqdn)
    # # remove any domain part in last part on the input filed
    # fqdn = re.sub(
    #     '\+{0}$'.format(domain.replace('.', '\\+')), '', fqdn)
    # extract the basename from the sls inclusion directive or filename
    fqdn = slssan1.sub('', fqdn)
    # extract the basename from the sls inclusion directive or filename, part2
    fqdn = slssan2.sub('', fqdn)
    fqdn = fqdn.replace('+', '.')
    # if domain not in fqdn:
    #     fqdn = '{0}.{1}'.format(fqdn, domain)
    return fqdn


def get_pillar_sw_ip(ip):
    return ipsan.sub('_', ip).replace(
        '@', 'AROBASE').replace(
            '*', 'DOTSTAR')
