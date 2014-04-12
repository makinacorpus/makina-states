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
        if env in ['prod']:
            default_install_mode = 'installed'

        debian_stable = "wheezy"
        ubuntu_lts = "precise"
        ubuntu_last = "saucy"
        lts_dist = debian_stable
        if grains['os'] in ['Ubuntu']:
            lts_dist = ubuntu_lts

        data = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.pkgs', {
                'installmode': default_install_mode,
                'keyserver': 'pgp.mit.edu',
                'dist': saltmods['mc_utils.get']('lsb_distrib_codename', ''),
                'lts_dist': lts_dist,
                'apt': {
                    'ubuntu': {
                        'dist': saltmods['mc_utils.get'](
                            'lsb_distrib_codename', ubuntu_lts),
                        'comps': (
                            'main restricted universe multiverse'),
                        'mirror': (
                            'http://ftp.free.fr/mirrors/'
                            'ftp.ubuntu.com/ubuntu'),
                        'last': ubuntu_last,
                        'lts': ubuntu_lts,
                    },
                    'debian': {
                        'stable': debian_stable,
                        'dist': saltmods['mc_utils.get'](
                            'lsb_distrib_codename', debian_stable),
                        'comps': 'main contrib non-free',
                        'mirror': 'http://ftp.de.debian.org/debian',
                    },
                }})
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
