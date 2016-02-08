# -*- coding: utf-8 -*-
'''

.. _module_mc_lxc:

mc_lxc / lxc registry
============================================

This module contains settings for lxc and helper functions

'''

# Import python libs
import logging
import mc_states.api
import random

from mc_states import saltapi
# early in mcpillar, we dont have __salt__
from mc_states.grains.makina_grains import _is_lxc

_errmsg = saltapi._errmsg
__name = 'lxc'

log = logging.getLogger(__name__)


PROJECT_PATH = 'project/makinacorpus/makina-states'
SFTP_URL = 'frs.sourceforge.net:/home/frs/{0}'.format(PROJECT_PATH)
TARGET = '/var/lib/lxc/makina-states'


def gen_mac():
    return ':'.join(map(lambda x: "%02x" % x, [0x00, 0x16, 0x3E,
                                               random.randint(0x00, 0x7F),
                                               random.randint(0x00, 0xFF),
                                               random.randint(0x00, 0xFF)]))


def is_lxc():
    """
    in case of a container, we have the container name in cgroups
    else, it is equal to /

    in lxc:
        ['11:name=systemd:/user/1000.user/1.session',
        '10:hugetlb:/thisname',
        '9:perf_event:/thisname',
        '8:blkio:/thisname',
        '7:freezer:/thisname',
        '6:devices:/thisname',
        '5:memory:/thisname',
        '4:cpuacct:/thisname',
        '3:cpu:/thisname',
        '2:cpuset:/thisname']

    in host:
        ['11:name=systemd:/',
        '10:hugetlb:/',
        '9:perf_event:/',
        '8:blkio:/',
        '7:freezer:/',
        '6:devices:/',
        '5:memory:/',
        '4:cpuacct:/',
        '3:cpu:/',
        '2:cpuset:/']
    """
    return _is_lxc(_o=__opts__)


def is_this_lxc():
    return __salt__['mc_utils.is_this_lxc']()


def get_container(pid):
    return __salt__['mc_utils.get_container'](pid)


def filter_host_pids(pids):
    return __salt__['mc_utils.filter_host_pids'](pids)


def settings():
    '''Lxc registry

    virt defaults (makina-states.services.virt.lxc)
      is_lxc

    containers
        Mapping of containers defintions classified by host
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        lxcSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.virt.lxc', {
                'is_lxc': is_lxc(),
            })
        return lxcSettings
    return _settings()


def test(name="thisisatest"):
    msr = __salt__['mc_loations.msr']()
    vm = {"bridge": "lxcbr1",
          "backing": "dir",
          "ip": "10.5.0.7",
          "bootstrap_shell": "bash",
          "gateway": "10.5.0.1",
          "script": msr + "/_scripts/boot-salt.sh",
          "minion": {"master": __opts__['master'],
                     "master_port": __opts__['master_port']},
          "clone_from": "makina-states-trusty",
          "ssh_username": "ubuntu", "ssh_gateway_key": "/root/.ssh/id_dsa",
          "netmask": "16",
          "password": "testtesttesttest",
          "dnsservers": ["8.8.8.8", "4.4.4.4"],
          "name": name,
          "target": __opts__['id'],
          "mac": "00:16:3e:11:31:64",
          "ssh_gateway_user": "root",
          "script_args": ("-C"),
          "ssh_gateway_port": 22}
    return __salt__['lxc.cloud_init'](name, vm_=vm)
