# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_docker:

mc_cloud_docker / docker registry for compute nodes
===================================================



'''

# Import python libs
import logging
import mc_states.api

from mc_states import saltapi
from salt.utils.odict import OrderedDict

_errmsg = saltapi._errmsg
__name = 'mc_cloud_docker'

log = logging.getLogger(__name__)
VT = 'docker'
PREFIX = 'makina-states.cloud.{0}'.format(VT)


def vt():
    return __salt__['mc_cloud_vm.vt'](VT)


def is_docker():
    """
    """
    try:
        docker = 'docker' in open('/proc/1/environ').read()
    except (IOError, OSError):
        docker = False
    if not docker:
        docker = bool(__grains__.get('makina.docker'))
    return docker


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
                '/etc/default/docker-net-makina': {},
                '/etc/dnsmasq.d/docker0': {},
                '/etc/dnsmasq.d/docker1': {},
                '/etc/reset-net-bridges': {},
                '/etc/docker-net-makina.sh': {}},
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
