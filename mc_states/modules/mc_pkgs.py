#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_pkgs:

mc_pkgs / pkgs registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_pkgs

'''
# Import python libs
import logging
import mc_states.api
from distutils.version import LooseVersion

__name = 'pkgs'

log = logging.getLogger(__name__)
PREFIX = 'makina-states.localsettings.{0}'.format(__name)


def settings():
    '''
    pkgs registry

    installmode
        install or update mode (install/latest)
    keyserver
        default GPG server
    dist
        current system dist
    udist
        applicable ubuntu dist,
        For eg, install ubuntu pkgs on a Debian.
    lts_dist
        current distributaion stable release
    force_apt_ipv4
        force apt to use ipv4
    force_apt_ipv6
        force apt to use ipv6
    apt
        ubuntu
            dist
                dist version
            comps
                enabled comps
            mirror
                mirror
            last
                last unstable release
            lts
                stable release
        debian
            stable
                stable release
            dist
                current dist
            comps
                enabled comps
            mirror
                mirror

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        _g = __grains__
        # instlall mode latest is really too slow
        # default_install_mode = 'latest'
        default_install_mode = 'installed'
        env = _s['mc_env.settings']()['env']
        if env in ['prod']:
            default_install_mode = 'installed'

        debian_stable = "wheezy"
        ddist = debian_stable
        ubuntu_old_lts = "trusty"
        ubuntu_lts = "bionic"
        ubuntu_last = "yakkety"
        lts_dist = debian_stable
        os = _g['os'].lower()
        mirrors = {
            # deb_mirror = 'http://ftp.de.debian.org/debian'
            'mirrors_debian_archive': 'http://archive.debian.org/debian/',
            'mirrors_debian_dist': 'http://ftp.fr.debian.org/debian/',
            'mirrors_debian_ovh': 'http://ubuntu.mirrors.ovh.net/ftp.debian.org/debian/',
            'mirrors_ubuntu_dist_fr': 'http://fr.archive.ubuntu.com/ubuntu/',
            'mirrors_ubuntu_dist': 'http://archive.ubuntu.com/ubuntu/',
            'mirrors_ubuntu_ovh': 'http://ubuntu.mirrors.ovh.net/ftp.ubuntu.com/ubuntu/',
            'mirrors_ubuntu_online': 'http://ftp.free.fr/mirrors/ftp.ubuntu.com/ubuntu/',
            'mirrors_ubuntu_plus': 'http://mirror.plusserver.com/ubuntu/ubuntu/',
            'mirrors_ubuntu_ircam': 'http://mirrors.ircam.fr/pub/ubuntu/archive/'}
        # ovh is too much down
        mirrors['mirrors_ubuntu_dist'] = mirrors['mirrors_ubuntu_dist_fr']
        mirrors['mirrors_ubuntu_ovh'] = mirrors['mirrors_ubuntu_dist_fr']
        mirrors['mirrors_debian_ovh'] = mirrors['mirrors_debian_dist']
        # so you start
        mirrors['mirrors_ubuntu_sys'] = mirrors['mirrors_ubuntu_ovh']
        umirror = mirrors['mirrors_ubuntu_plus']
        if _g['os'] in ['Ubuntu']:
            lts_dist = ubuntu_lts
            if LooseVersion(_g['osrelease']) >= LooseVersion('20.04'):
                lts_dist = ubuntu_lts = 'focal'
            elif LooseVersion(_g['osrelease']) >= LooseVersion('18.04'):
                lts_dist = ubuntu_lts = 'bionic'
            elif LooseVersion(_g['osrelease']) >= LooseVersion('16.04'):
                lts_dist = ubuntu_lts = 'xenial'
            elif LooseVersion(_g['osrelease']) >= LooseVersion('14.04'):
                lts_dist = ubuntu_lts = 'trusty'
            elif LooseVersion(_g['osrelease']) >= LooseVersion('12.04'):
                lts_dist = ubuntu_lts = 'precise'
            if LooseVersion(_g['osrelease']) >= LooseVersion('16.04'):
                umirror = '{mirrors_ubuntu_dist}'
            elif _s['mc_nodetypes.is_vagrantvm']():
                umirror = '{mirrors_ubuntu_ircam}'
            elif _g['osrelease'] >= '15.04':
                # umirror = mirrors['dist']
                umirror = '{mirrors_ubuntu_dist_fr}'
            elif _s['mc_nodetypes.is_travis']():
                umirror = '{mirrors_ubuntu_dist}'

        deb_mirror = '{mirrors_debian_dist}'
        if _g['os'] in ['Debian']:
            ddist = _s['mc_utils.get'](
                'lsb_distrib_codename', debian_stable)
            if not ddist:
                ddist = debian_stable
            if _g['osrelease'][0] == '4':
                ddist = debian_stable = "sarge"
                deb_mirror = '{mirrors_debian_archive}'
            elif _g['osrelease'][0] == '5':
                ddist = debian_stable = "lenny"
                deb_mirror = '{mirrors_debian_archive}'
            else:
                ddist = _s['mc_utils.get'](
                    'lsb_distrib_codename', debian_stable)

        for provider in [a for a in mirrors]:
            for test in ['id', 'fqdn', 'domain', 'host', 'nodename']:
                val = _s['mc_utils.get'](test, '')
                if isinstance(val, basestring):
                    if provider in val.lower():
                        umirror = mirrors.get('mirrors_{0}_{1}'.format(os, provider),
                                              mirrors['mirrors_{0}_dist'.format(os)])

        ldist = _s['mc_utils.get']('lsb_distrib_codename', ubuntu_lts)
        udist = ldist
        extra_confs = {}
        if _g['os'] not in ['Ubuntu']:
            udist = ubuntu_lts
        if _g['os_family'] in ['Debian']:
            extra_confs.update({
                '/etc/apt/apt.conf.d/99netfamily': {'mode': '644'},
            })
        if _g['os'] in ['Ubuntu']:
            extra_confs.update({
                # '/etc/apt/apt.conf.d/99release': {'mode': '644'},
                '/etc/apt/apt.conf.d/99clean': {'mode': '644'},
                '/etc/apt/apt.conf.d/99confhold': {'mode': '644'},
                '/etc/apt/apt.conf.d/99gzip': {'mode': '644'},
                '/etc/apt/apt.conf.d/99notrad': {'mode': '644'},
                '/etc/apt/preferences.d/00_proposed.pref': {'mode': '644'},
            })
        DEFAULTS = {
                'installmode': default_install_mode,
                'extra_confs': extra_confs,
                'keyserver': 'pgp.mit.edu',
                'dist': ldist,
                'force_apt_ipv6': False,
                'force_apt_ipv4': True,
                'lts_dist': lts_dist,
                'apt': {
                    'ubuntu': {
                        'mirror': umirror,
                        'dist': udist,
                        'comps': (
                             'main restricted universe multiverse'),
                        'use_backports': True,
                        'last': ubuntu_last,
                        'lts': ubuntu_lts,
                        'old_lts': ubuntu_old_lts,
                    },
                    'debian': {
                        'mirror': deb_mirror,
                        'stable': debian_stable,
                        'use_backports': True,
                        'dist': ddist,
                        'comps': 'main contrib non-free',
                    },
                }}
        DEFAULTS.update(mirrors)
        data = _s['mc_utils.defaults'](PREFIX, DEFAULTS)
        data['use_backports'] = data['apt'].get(
            _g['os'].lower(), {}).get('use_backports', True)
        if _g['os'] in ['Ubuntu']:
            data['use_backports'] = data['apt']['ubuntu']['use_backports']
        elif _g['os'] in ['Debian']:
            if _g['osrelease'][0] == '4':
                data['apt']['debian']['mirror'] = (
                    'http://archive.debian.org/debian/')
            elif _g['osrelease'][0] == '5':
                data['apt']['debian']['mirror'] = (
                    'http://archive.debian.org/debian/')

        data['dcomps'] = data['apt']['debian']['comps']
        data['ddist'] = data['apt']['debian']['dist']
        data['debian_mirror'] = data['apt']['debian']['mirror']
        data['debian_stable'] = data['apt']['debian']['stable']
        data['lts_dist'] = data['lts_dist']
        data['ubuntu_last'] = data['apt']['ubuntu']['last']
        data['ubuntu_lts'] = data['apt']['ubuntu']['lts']
        data['ubuntu_old_lts'] = data['apt']['ubuntu']['old_lts']
        data['ubuntu_mirror'] = data['apt']['ubuntu']['mirror']
        data['ucomps'] = data['apt']['ubuntu']['comps']
        data['ubp'] = data['apt']['ubuntu']['use_backports']
        data['dbp'] = data['apt']['debian']['use_backports']
        data['udist'] = data['apt']['ubuntu']['dist']
        udist = data['udist']
        ddist = data['ddist']
        # more easy managable structure to be use in SLSes and templates
        pkg_data = __salt__['grains.filter_by']({
            'default': {'mirrors': []},
            'Debian': {'use-backports': True, 'mirrors': [
                {'mirror': data['debian_mirror'],
                 'dists': [
                     {'name': ddist, 'comps': data['dcomps']},
                     {'name': ddist+'-updates', 'comps': data['dcomps']}]},
                {'mirror': 'http://security.debian.org/',
                 'dists': [
                     {'name': ddist+'/updates', 'comps': data['dcomps']}]},
            ]},
            'Ubuntu': {'mirrors': [
                {'mirror': data['ubuntu_mirror'],
                 'dists': [
                     {'name': udist, 'comps': data['ucomps']},
                     {'name': udist+'-proposed', 'comps': data['ucomps']},
                     {'name': udist+'-updates', 'comps': data['ucomps']},
                     {'name': udist+'-security', 'comps': data['ucomps']}]},
                {'mirror': 'http://archive.canonical.com/ubuntu',
                 'dists': [{'name': udist, 'comps': 'partner'}]},
            ]}}, grain='os')
        # https://bugs.launchpad.net/ubuntu/+source/apt-setup/+bug/1409555
        # extras repo doest exist anymore
        if _g['os'] in ['Ubuntu'] and _g['osrelease'] < '15.04':
            pkg_data['mirrors'].append({
                'mirror': 'http://extras.ubuntu.com/ubuntu',
                'dists': [{'name': udist, 'comps': 'main'}]})
        if data['use_backports']:
            pkg_data['mirrors'].extend(
                __salt__['grains.filter_by']({
                    'Debian': [
                        {'mirror': data['debian_mirror'],
                         'dists': [{'name': ddist+'-backports',
                                    'comps': data['dcomps']}]}],
                    'Ubuntu': [
                        {'mirror':  data['ubuntu_mirror'],
                         'dists': [{'name': udist+'-backports',
                                    'comps': data['ucomps']}]}
                    ]}, grain='os'))
        if _g['os'] in ['Debian']:
            if (
                data['ddist'] not in ['sid'] and
                _g.get('osrelease', '1')[0] <= '5'
            ):
                pkg_data['mirrors'][0]['dists'].pop(1)
                pkg_data['mirrors'].pop(1)
                pkg_data['mirrors'].pop(1)
                pkg_data['mirrors'].extend(
                    __salt__['grains.filter_by']({
                        'Debian': [
                            {'mirror':
                             'http://archive.debian.org/debian-security',
                             'dists': [{'name': ddist+'/updates',
                                        'comps': data['dcomps']}]},
                            {'mirror':
                             'http://archive.debian.org/debian-volatile',
                             'dists': [{'name': ddist+'/volatile',
                                        'comps': data['dcomps']}]},
                            {'mirror':
                             'http://archive.debian.org/backports.org',
                             'dists': [{'name': ddist+'-backports',
                                        'comps': data['dcomps']}]}
                        ]}), grain='os')
        # retrocompat
        data['ppa_dist'] = data['udist']
        data['pkg_data'] = pkg_data
        data = _s['mc_utils.format_resolve'](data)
        return data
    return _settings()
# vim:set et sts=4 ts=4 tw=80:
