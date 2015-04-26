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
from mc_states.grains.makina_grains import is_docker as _is_docker

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
    return _is_docker()


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
            'host_confs': {
                '/etc/systemd/system/docker.socket': {
                    "mode": "644"},
                '/etc/systemd/system/docker.service': {
                    "mode": "644"},
                '/etc/systemd/system/docker-net-makina.service': {
                    "mode": "644"},
                '/etc/default/docker-net-makina': {},
                '/etc/dnsmasq.d/docker0': {},
                '/etc/dnsmasq.d/docker1': {},
                '/etc/reset-net-bridges': {},
                '/usr/bin/docker-net-makina.sh': {}},
            'defaults': {'gateway': '10.7.0.1',
                         'network': '10.7.0.0',
                         'bridge': 'docker1',
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
