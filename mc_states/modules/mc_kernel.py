# -*- coding: utf-8 -*-
'''
.. _module_mc_kernel:

mc_kernel / kernel registry
============================================



If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_kernel


'''
# Import python libs
import logging
import mc_states.api

__name = 'kernel'

log = logging.getLogger(__name__)


def settings():
    '''
    kernel registry

    Systcl values for
        tcp_wmem
             4096 65536 16777216
        tcp_rmem
             4096 87380 16777216
        rwmemmax
             16716777216 77216
        ip_local_port_range
             1025 65535
        tcp_max_sync_backlog
             20480
        tcp_fin_timeout
             15
        net_core_somaxconn
             4096
        netdev_max_backlog
             4096
        no_metrics_save
             1
        ulimit
             64000
        tcp_congestion_control
             cubic
        tcp_max_tw_buckets
             2000000
        tcp_tw_recycle
             0
        vm_min_free_kbytes
             int(((grains['mem_total']/64)*1024*1024)/1000)
        tcp_syn_retries
             2
        tcp_tw_reuse
             1
        tcp_timestamps
             0
        vm_swappiness
            1

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        nbcpus = __grains__.get('num_cpus', '1')

        #
        # KERNEL OPTIMIZATIONS
        #
        max_user_instances = '128'
        max_user_watches = '8192'
        try:
            # try to get an uppper value for hight memory servers
            vmfree = int(((grains['mem_total']/64)*1024*1024)/1000)
            if vmfree < 30000:
                raise Exception('too low, use default')
            max_user_instances = '512'
            max_user_watches = '100000'
        except:
            # sane default for at least 1gb hardware
            vmfree = '65536'
        data = _s['mc_utils.defaults'](
            'makina-states.localsettings.kernel', {
                'tcp_wmem': '4096 65536 16777216',
                'tcp_rmem': '4096 87380 16777216',
                'rwmemmax': '16777216',
                'ip_local_port_range': '1025 65535',
                'tcp_max_syn_backlog': '20480',
                'tcp_fin_timeout': '15',
                'net_core_somaxconn': '4096',
                'netdev_max_backlog': '4096',
                'no_metrics_save': '1',
                'ulimit': '64000',
                'tcp_congestion_control': 'cubic',
                'tcp_max_tw_buckets': '2000000',
                'tcp_tw_recycle': '0',
                'fs.inotify.max_user_instances': max_user_instances,
                'fs.inotify.max_user_watches': max_user_watches,
                'vm_min_free_kbytes': vmfree,
                'tcp_syn_retries': '2',
                'tcp_tw_reuse': '1',
                'tcp_timestamps': '0',
                'vm_swappiness': '1',
            }
        )
        return data
    return _settings()



#
