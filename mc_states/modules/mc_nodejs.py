#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''

.. _module_mc_nodejs:

mc_nodejs / nodejs/npm registry
============================================

'''
# Import python libs
import logging
import mc_states.api
from distutils.version import LooseVersion
import os

__name = 'nodejs'

log = logging.getLogger(__name__)
CUR_VER = '4.6.0'


def ver():
    return CUR_VER


def settings():
    '''
    nodejs

    AS of - 2016-10-02, we do not install anymore nodejs from
    original binary tarball, but we use their ppa, to install nodejs
    onto the system.

    We also now automatically get hashs from nodejs repository if you
    persist to use the prefixed install.

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s, _g = __salt__, __grains__
        locations = _s['mc_locations.settings']()
        # nodejs
        data = _s['mc_utils.defaults'](
            'makina-states.localsettings.nodejs', {
                'shas': {
                    'node-v0.10.26-linux-x86.tar.gz': (
                        'b3bebee7f256644266fccce04f54e2825eccbfc0'),
                    'node-v0.10.26-linux-x64.tar.gz': (
                        'd15d39e119bdcf75c6fc222f51ff0630b2611160'),
                    'node-v0.10.28-linux-x64.tar.gz': (
                        '4b9cf9437decea3d9913b694ea2e9b0a06ced2dd'),
                    'node-v0.10.29-linux-x64.tar.gz': (
                        '570c45653fec04d29d2208bb2967bc88b2821537'),
                    'node-v0.10.36-linux-x64.tar.gz': (
                        '350df861e161c34b97398fc1b440f3d80f174cf9'),
                    'node-v4.3.0-linux-x64.tar.xz': (
                        '8a41afe0d184532c7336d003056badaa0f645f02'),
                    'node-v0.4.9.tar.gz': (
                        "ce9b62baa993b385b1efd66058503ea215a08389"),
                },
                'yarn_install': True,
                'yarn_version': '0.23.0',
                'gpg':  ['9D41F3C3',
                         '6A010C5166006599AA17F08146C2130DFD2497F5',
                         '9554F04D7259F04124DE6B476D5A82AC7E37093B',
                         '94AE36675C464D64BAFA68DD7434390BDBE9B9C5',
                         '0034A06D9D9B0064CE8ADF6BF1747F4AD2306D93',
                         'FD3A5288F042B6850C66B31F09FE44734EB7990E',
                         '71DCFD284A79C3B38668286BC97EC7A07EDE3FC1',
                         'DD8F2338BAE7501E3DD5AC78C273792F7D83545D',
                         'B9AE9905FFD7803F25714661B63B535A4C206CA9',
                         'C4F0DFFF4E8C1A8236409D08E73BC641CC11F4C8',
                         '56730D5401028683275BD23C23EFEFE93C4CFFFE',],

                'versions': [CUR_VER],
                'version': CUR_VER,
                'arch': _g['cpuarch'].replace('x86_64', 'x64'),
                'location': locations['apps_dir']+'/node',
                'packages': {
                    'system': [],
                    CUR_VER: [],
                },
                'repo': 'node_6.x',
                'npmPackages': [],
                'systemNpmPackages': [],
            }
        )
        data['url'] = get_url(version=data['version'],
                              arch=data['arch'],
                              data=data)
        return data
    return _settings()


def get_hash(url, data=None, ttl=60*60*24):
    _s = __salt__

    def _do(url, data):
        fn = os.path.basename(url)
        if not data:
            data = settings()
        try:
            filehash = data['shas'][fn]
        except KeyError:
            try:
                shas = __salt__['http.query'](
                    os.path.dirname(url)+'/SHASUMS256.txt')['body']
            except (KeyError,):
                filehash = None
            else:
                filehash = None
                for line in shas.strip().splitlines():
                    try:
                        sha, nodever = line.split()
                    except (ValueError,):
                        continue
                    if nodever == fn:
                        filehash = 'sha256=' + sha
                        break
        return filehash
    cache_key = __name + '.get_hash{0}'.format(url)
    return _s['mc_utils.memoize_cache'](
        _do, [url, data], key=cache_key, seconds=ttl)


def get_arch(arch=None, data=None):
    if not arch:
        if data is None:
            data = settings()
        arch = data['arch']
    return arch


def get_archive(version=CUR_VER, arch=None, data=None, binary=True, fmt=None):
    arch = get_arch(arch=arch, data=data)
    if not binary:
        archive = "node-v{version}.tar.{fmt}"
    else:
        archive = "node-v{version}-linux-{arch}.tar.{fmt}"
        if LooseVersion(version) >= LooseVersion('4.2.0') and not fmt:
            fmt = 'xz'
    if not fmt:
        fmt = 'gz'
    return archive.format(version=version, arch=arch, fmt=fmt)


def get_url(version=CUR_VER, arch=None, binary=True, data=None, fmt=None):
    if version[:4] in ['0.1.', '0.2.', '0.3.', '0.4.', '0.5.']:
        url = "http://nodejs.org/dist/{archive}"
        binary = True
    else:
        url = 'http://nodejs.org/dist/v{version}/{archive}'
    arch = get_arch(arch=arch, data=data)
    archive = get_archive(version=version, arch=arch, binary=binary, data=data, fmt=fmt)
    return url.format(archive=archive, version=version, fmt=fmt, arch=arch)
# vim:set et sts=4 ts=4 tw=80:
