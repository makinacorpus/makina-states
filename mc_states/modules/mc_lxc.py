# -*- coding: utf-8 -*-
'''

.. _module_mc_lxc:

mc_lxc / lxc registry
============================================

If you alter this module and want to test it, do not forget to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_lxc

'''

# Import python libs
import logging
import mc_states.utils
import random
import copy

from salt.utils.odict import OrderedDict

__name = 'lxc'

log = logging.getLogger(__name__)


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

    containers
        Mapping of containers defintions
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        locations = localsettings['locations']

        lxcSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.virt.lxc', {
                'is_lxc': is_lxc(),
                'dnsservers': ['8.8.8.8', '4.4.4.4'],
                'defaults' : {
                    'size': None,  # via profile
                    'gateway': '10.5.0.1',
                    'master': None,
                    'master_port': '4506',
                    'image': 'ubuntu',
                    'network': '10.5.0.0',
                    'netmask': '16',
                    'netmask_full': '255.255.0.0',
                    'default_template': 'ubuntu',
                    'bridge': 'lxcbr1',
                    'sudo': True,
                    'use_bridge': True,
                    'backing': 'lvm',
                    'users': ['root', 'sysadmin'],
                    'ssh_username': 'ubuntu',
                    'vgname': 'data',
                    'lvname': 'data',
                    'lxc_conf': [],
                    'lxc_conf_unset': [],
                },
                'containers': {
                    __grains__['id']: {},
                    #'target': {
                    #  'containerid': {
                    #  'name': 'foo'
                    #  'backing': 'lvm'
                    #}
                },
                'lxc_cloud_profiles': {
                    'xxxtrem': {
                        'size': '2000g',
                    },
                    'xxtrem': {
                        'size': '1000g',
                    },
                    'xtrem': {
                        'size': '500g',

                    },
                    'xxxlarge': {
                        'size': '100g',

                    },
                    'xxlarge': {
                        'size': '50g',
                    },
                    'large': {
                        'size': '20g',

                    },
                    'medium': {
                        'size': '10g',
                    },
                    'small': {
                        'size': '5g',
                    },
                    'xsmall': {
                        'size': '3g',
                    },
                    'xxsmall': {
                        'size': '1g',
                    },
                    'xxxsmall': {
                        'size': '500m',
                    },
                },
            }
        )
        if not lxcSettings['defaults']['master']:
            lxcSettings['defaults']['master'] = lxcSettings['defaults']['gateway']
        for target in [t for t in lxcSettings['containers']]:
            # filter dicts and overiddes
            for container in lxcSettings['containers'][target]:
                lxc_data = lxcSettings['containers'][target][container]
                lxc_data['mac'] = __salt__['mc_lxc.find_mac_for_container'](
                    target, container, lxc_data)
                for i in ['ip', 'password']:
                    if not i in lxc_data:
                        raise Exception('Missing data {1}\n:{0}'.format(i, lxc_data))
                    # shortcut name for profiles
                    # small -> ms-target-small
                    profile = lxc_data.get('profile', 'medium')
                    if profile in lxcSettings['lxc_cloud_profiles']:
                        del lxc_data['profile']
                    lxc_data.setdefault(
                        'profile',
                        __salt__['mc_saltcloud.gen_id'](
                            'ms-{0}-{1}-lxc'.format(target, profile)))
                lxc_data.setdefault('name', container)
                lxc_data.setdefault('size', None)
                lxc_data.setdefault('from_container', None)
                lxc_data.setdefault('snapshot', None)
                for i in ["from_container",
                          'size', 'image', 'bridge', 'netmask', 'gateway',
                          'dnsservers', 'backing', 'vgname', 'lvname',
                          'vgname', 'ssh_username', 'users', 'sudo',
                          'lxc_conf_unset', 'lxc_conf']:
                    lxc_data.setdefault(
                        i,
                        lxcSettings['defaults'].get(i,
                                                    lxcSettings.get(i, None)))
        return lxcSettings
    return _settings()


def find_mac_for_container(target, container, lxc_data=None):
    if not lxc_data:
        lxc_data = {}
    gid = 'makina-states.services.virt.lxc.containerssettings.{1}.{1}.mac'.format(
        target, container)
    mac = lxc_data.get('mac', __salt__['mc_utils.get'](gid, None))
    if not mac:
        __salt__['grains.setval'](gid, gen_mac())
        __salt__['saltutil.sync_grains']()
        mac = __salt__['mc_utils.get'](gid)
        if not mac:
            raise Exception(
                'Error while setting grainmac for {0}/{1}'.format(target,
                                                                  container))
    return mac


def find_ip_for_container(target, container, lxc_data=None):
    '''Search for:
        - an ip in lxc.conf
        - an ip already allocated
        - an random available ip in the range
    '''
    raise Exception('Not implemented')
    if not lxc_data:
        lxc_data = {}
    ip4 = lxc_data.get('ip4', None)
    gid = 'makina-states.services.virt.lxc.containers.{0}.{1}.ip4'.format(
        target, container)
    if not ip4:
        __salt__['grains.setval'](gid, gen_ip4())
        __salt__['saltuitil.sync_grains']()
        ip4 = __salt__['mc_utils.get'](gid)
        if not ip4:
            raise Exception(
                'Error while setting grainip4 for {0}/{1}'.format(target,
                                                              container))
    return ip4


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
