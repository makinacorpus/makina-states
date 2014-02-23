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

from salt.utils.odict import OrderedDict

__name = 'lxc'

log = logging.getLogger(__name__)


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
            'makina-states.services.http.lxc', {
                'is_lxc': is_lxc(),
            }
        )
        lxcSettings['containers'] = OrderedDict()
        # server-def is retro compat
        sufs = ['-lxc-server-def', '-lxc-container-def']

        for suf in sufs:
            for k, lxc_data in pillar.items():
                if k.endswith(suf):
                    lxc_data = lxc_data.copy()
                    lxc_name = lxc_data.get('name', k.split(suf)[0])
                    lxcSettings['containers'][lxc_name] = lxc_data
                    lxc_data.setdefault('template', 'ubuntu')
                    lxc_data.setdefault('netmask', '255.255.255.0')
                    lxc_data.setdefault('gateway', '10.0.3.1')
                    lxc_data.setdefault('dnsservers', '10.0.3.1')
                    lxc_root = lxc_data.setdefault(
                        'root',
                        locations['var_lib_dir'] + '/lxc/' + lxc_name)
                    lxc_data.setdefault('rootfs', lxc_root + '/rootfs')
                    lxc_data.setdefault('config', lxc_root + '/config')
                     # raise key error if undefined
                    lxc_data.setdefault('mac', lxc_data['mac'])
                    lxc_data.setdefault('ip4', lxc_data['ip4'])
        return lxcSettings
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
