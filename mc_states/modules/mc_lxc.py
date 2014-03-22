# -*- coding: utf-8 -*-
'''

.. _module_mc_lxc:

mc_lxc / lxc registry
============================================

This module contains settings for lxc and helper functions

'''

# Import python libs
import logging
import mc_states.utils
from pprint import pformat
import os
import random
import socket
import copy

from mc_states import saltapi
from salt.utils.odict import OrderedDict

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

    try:
        cgroups = open('/proc/1/cgroup').read().splitlines()
        lxc = not '/' == [a.split(':')[-1]
                          for a in cgroups if ':cpu:' in a][-1]
    except Exception:
        lxc = False
    return lxc


def settings():
    '''Lxc registry

    virt defaults (makina-states.services.virt.lxc)
      is_lxc

    containers
        Mapping of containers defintions classified by host
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        nt_registry = __salt__['mc_nodetypes.registry']()
        ntSettings = __salt__['mc_nodetypes.settings']()
        cloudSettings = __salt__['mc_saltcloud.settings']()
        localsettings = __salt__['mc_localsettings.settings']()
        locations = localsettings['locations']
        lxcSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.virt.lxc', {
                'is_lxc': is_lxc(),
            })
        return lxcSettings
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

