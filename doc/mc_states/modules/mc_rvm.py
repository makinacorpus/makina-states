#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_rvm:

mc_rvm / rvm registry
============================================



If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_rvm

'''
# Import python libs
import logging
import mc_states.api

__name = 'rvm'

log = logging.getLogger(__name__)
RVM_URL = (
    'https://raw.github.com/wayneeseguin/rvm/master/binscripts/rvm-installer')


def settings():
    '''
    rvm registry

    rvm_url
        rvm download url
    rubies
        Activated rubies
    rvm_user
        RVM user
    rvm_group
        RVM group

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s, _g = __salt__, __grains__
        locations = __salt__['mc_locations.settings']()
        pkgs = ['bash',
                'coreutils',
                'gzip',
                'bzip2',
                'gawk',
                'sed',
                'curl',
                'git-core',
                'subversion',
                'build-essential',
                'openssl',
                'libreadline6',
                'libreadline6-dev',
                'curl',
                'git-core',
                'zlib1g',
                'zlib1g-dev',
                'libssl-dev',
                'libyaml-dev',
                'libsqlite3-0',
                'libsqlite3-dev',
                'sqlite3',
                'libxml2-dev',
                'libxslt1-dev',
                'autoconf',
                'libc6-dev',
                'libncurses5-dev',
                'automake',
                'libtool',
                'bison',
                'subversion',
                'ruby']
        if not (_g['os'] in ['Ubuntu'] and _g['osrelease'] >= '15.04'):
            pkgs.append('ruby1.9.3')
        data = _s['mc_utils.defaults'](
            'makina-states.localsettings.rvm', {
                'pkgs': pkgs,
                'url': RVM_URL,
                'rubies': ['1.9.3'],
                'user': 'rvm',
                'group': 'rvm',
                'branch': 'stable',
                'path': locations['rvm_path'],
            })
        return data
    return _settings()
# vim:set et sts=4 ts=4 tw=80:
