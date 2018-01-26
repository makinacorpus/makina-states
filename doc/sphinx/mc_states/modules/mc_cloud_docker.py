# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_docker:

mc_cloud_docker / docker registry for compute nodes
===================================================



'''

# Import python libs
import logging
import os

from mc_states import saltapi
# early in mcpillar, we dont have __salt__
from mc_states.grains.makina_grains import _is_docker


_errmsg = saltapi._errmsg
__name = 'mc_cloud_docker'

log = logging.getLogger(__name__)
VT = 'docker'
PREFIX = 'makina-states.cloud.{0}'.format(VT)


def vt():
    return __salt__['mc_cloud_vm.vt'](VT)


def is_docker():
    """
    Return true if we find a system or grain flag
    that explicitly shows us we are in a DOCKER context
    """
    return _is_docker(_o=__opts__)


def vt_default_settings(cloudSettings, imgSettings):
    '''
    Default docker vm settings

        image
            docker template to use
        backing
            (lvm)
        storage_pools
            pool defs (only lvm is supported for now)
    '''
    _s = __salt__
    vmSettings = _s['mc_utils.dictupdate'](
        _s['mc_cloud_vm.vt_default_settings'](cloudSettings, imgSettings), {
            'vt': VT,
            'bridge': "docker1",
            'host_confs': {
                '/etc/systemd/system/docker.socket': {
                    "mode": "644"},
                '/etc/systemd/system/docker.service': {
                    "mode": "644"},
                '/etc/systemd/system/docker-net-makina.service': {
                    "mode": "644"},
                '/etc/default/docker': {},
                '/etc/default/magicbridge_docker1': {},
                # retrocompatible generation alias
                '/etc/default/docker-net-makina': {
                    'source':
                    'salt://makina-states/files/etc/default'
                    '/magicbridge_docker1'},
                '/etc/init/docker.conf': {},
                '/etc/dnsmasq.d/docker0': {},
                '/etc/dnsmasq.d/docker1': {},
                '/etc/reset-net-bridges': {},
                '/usr/bin/docker-net-makina.sh': {
                    "mode": "755",
                    "template": False,
                    'source': (
                        'salt://makina-states/files/usr/bin/magicbridge.sh'
                    )
                },
                '/usr/bin/docker-service.sh': {}},
            'cli': '/usr/bin/docker',
            'cli_opts': '-d -b {bridge}',
            'docker_version': '1.9.0',
            'binary_url': 'https://github.com/makinacorpus/docker/releases'
                          '/download/mc_1/docker-{docker_version}.xz',
            'hashes': {
                'docker-1.8.2.xz': {
                    'hash': '9e1e3e624847fa1a6d7a9dd6d48a7d0e',
                    'dhash': '1f72779d67eda6c4f704c35edf144e7b',
                },
                'docker-1.9.0.xz': {
                    'hash': '9e1e3e624847fa1a6d7a9dd6d48a7d0e',
                    'dhash': '1f72779d67eda6c4f704c35edf144e7b',
                },
            },
            'defaults': {'gateway': '10.7.0.1',
                         'network': '10.7.0.0',
                         'bridge': '{bridge}',
                         'base_image': 'makinacorpus/makina-states:latest',
                         'backing': 'aufs'}})
    return vmSettings


def vt_extpillar(target, data, **kw):
    '''
    docker extpillar
    '''
    return data


def vm_extpillar(vm, data, *args, **kw):
    '''
    Get per docker specific settings
    '''
    return data
# vim:set et sts=4 ts=4 tw=80:
