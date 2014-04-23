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
import mc_states.utils

__name = 'pkgs'

log = logging.getLogger(__name__)


def settings():
    '''
    pkgs registry

    installmode
        install or update mode (install/latest)
    keyserver
        default GPG server
    dist
        current system dist
    lts_dist
        current distributaion stable release
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
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        # instlall mode latest is really too slow
        # default_install_mode = 'latest'
        default_install_mode = 'installed'
        env = saltmods['mc_env.settings']()['env']
        deb_mirror = 'http://ftp.de.debian.org/debian'
        if env in ['prod']:
            default_install_mode = 'installed'

        debian_stable = "wheezy"
        ubuntu_lts = "trusty"
        ubuntu_last = "saucy"
        lts_dist = debian_stable
        deb_mirror = 'http://ftp.de.debian.org/debian'
        if grains['os'] in ['Ubuntu']:
            lts_dist = ubuntu_lts
        if grains['os'] in ['Debian']:
            if grains['osrelease'][0] == '4':
                ddist = debian_stable = "sarge"
                deb_mirror = 'http://archive.debian.org/debian/'
            elif grains['osrelease'][0] == '5':
                ddist = debian_stable = "lenny"
                deb_mirror = 'http://archive.debian.org/debian/'
            else:
                ddist = saltmods['mc_utils.get'](
                    'lsb_distrib_codename', debian_stable)
        mirrors = {
            'ovh': 'http://mirror.ovh.net/ubuntu',
            #'online': 'http://mirror.ovh.net/ubuntu',
            'online': 'http://ftp.free.fr/mirrors/ftp.ubuntu.com/ubuntu',
        }
        umirror = mirrors['ovh']
        for provider in ['ovh', 'online']:
            for test in ['id', 'fqdn', 'domain', 'host', 'nodename']:
                val = saltmods['mc_utils.get'](test, '')
                if isinstance(val, basestring):
                    if provider in val.lower():
                        umirror = mirrors.get(provider, umirror)

        udist = saltmods['mc_utils.get']('lsb_distrib_codename', ubuntu_lts)
        if grains['os'] not in ['Ubuntu']:
            udist = ubuntu_lts
        data = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.pkgs', {
                'installmode': default_install_mode,
                'keyserver': 'pgp.mit.edu',
                'dist': saltmods['mc_utils.get']('lsb_distrib_codename', ''),
                'lts_dist': lts_dist,
                'apt': {
                    'ubuntu': {
                        'mirror': umirror,
                        'dist': udist,
                        'comps': (
                            'main restricted universe multiverse'),
                        'last': ubuntu_last,
                        'lts': ubuntu_lts,
                    },
                    'debian': {
                        'stable': debian_stable,
                        'dist': ddist,
                        'comps': 'main contrib non-free',
                        'mirror': deb_mirror,
                    },
                }})
        if grains['os'] in ['Debian']:
            if grains['osrelease'][0] == '4':
                data['apt']['debian']['mirror'] = 'http://archive.debian.org/debian/'
            elif grains['osrelease'][0] == '5':
                data['apt']['debian']['mirror'] = 'http://archive.debian.org/debian/'

        data['dcomps'] = data['apt']['debian']['comps']
        data['ddist'] = data['apt']['debian']['dist']
        data['debian_mirror'] = data['apt']['debian']['mirror']
        data['debian_stable'] = data['apt']['debian']['stable']
        data['lts_dist'] = data['lts_dist']
        data['ubuntu_last'] = data['apt']['ubuntu']['last']
        data['ubuntu_lts'] = data['apt']['ubuntu']['lts']
        data['ubuntu_mirror'] = data['apt']['ubuntu']['mirror']
        data['ucomps'] = data['apt']['ubuntu']['comps']
        data['udist'] = data['apt']['ubuntu']['dist']
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
