#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

.. _module_mc_nodejs:

mc_nodejs / nodejs/npm registry
============================================

'''
# Import python libs
import logging
import mc_states.api
from distutils.version import LooseVersion

__name = 'nodejs'

log = logging.getLogger(__name__)
CUR_VER = '4.3.0'


def settings():
    '''
    nodejs

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        locations = __salt__['mc_locations.settings']()
        # nodejs
        cur_nodejsver = '4.3.0'
        data = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.nodejs', {
                'shas': {
                    'node-v0.10.26-linux-x86.tar.gz': 'b3bebee7f256644266fccce04f54e2825eccbfc0',
                    'node-v0.10.26-linux-x64.tar.gz': 'd15d39e119bdcf75c6fc222f51ff0630b2611160',
                    'node-v0.10.28-linux-x64.tar.gz': '4b9cf9437decea3d9913b694ea2e9b0a06ced2dd',
                    'node-v0.10.29-linux-x64.tar.gz': '570c45653fec04d29d2208bb2967bc88b2821537',
                    'node-v0.10.36-linux-x64.tar.gz': '350df861e161c34b97398fc1b440f3d80f174cf9',
                    'node-v4.3.0-linux-x64.tar.xz': '8a41afe0d184532c7336d003056badaa0f645f02',
                    'node-v0.4.9.tar.gz': "ce9b62baa993b385b1efd66058503ea215a08389",
                },
                'versions': [CUR_VER],
                'version': CUR_VER,
                'arch': __grains__['cpuarch'].replace('x86_64', 'x64'),
                'location': locations['apps_dir']+'/node',
                'packages': {
                    'system': [],
                     CUR_VER: [],
                },
                'npmPackages': [],
                'systemNpmPackages': [],
            }
        )
        data['url'] = get_url(version=data['version'], arch=data['arch'], data=data)
        return data
    return _settings()

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
