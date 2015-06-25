# -*- coding: utf-8 -*-
'''

.. _module_mc_ntp:

mc_ntp / ntp registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_ntp

'''
# Import python libs
import logging
import mc_states.api

__name = 'ntp'

log = logging.getLogger(__name__)


def settings():
    '''
    ntp

        servers
           server entries without the fudge headers
        fudge
            fudge entries without the fudge headers

        default_all
            allow query from ext (firewalled in ms)
        block_ext
            block all outbound queryies
        default restrict
            set to false to generate a no<flag>

            ignore
                False
            limited
                False
            lowpriotrap
                False
            kod
                False
            peer
                True
            trap
                False
            serve
                True
            trust
                True
            modify
                False
            query
                False
            restrict
                list of restrict entries without the leading restrict

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.base.ntp', {
                'servers': [
                    '0.ubuntu.pool.ntp.org',
                    '1.ubuntu.pool.ntp.org',
                    '2.ubuntu.pool.ntp.org',
                    '3.ubuntu.pool.ntp.org',
                    'ntp.ubuntu.com',
                    '127.127.1.0',
                ],
                'fudge': [
                    '127.127.1.0 stratum 11',
                ],
                'restrict': [
                ],
                'default_all': True,
                'activated': None,
                'block_ext': False,
                'ignore': False,
                'kod': True,
                'limited': False,
                'lowpriotrap': False,
                'peer': False,
                'trap': False,
                'serve': True,
                'trust': True,
                'modify': False,
                'query': False,
                'defaults': {
                    'NTPSERVERS': '"ntp.ubuntu.com"',
                    'NTPDATE_USE_NTP_CONF': '"yes"',
                    'NTPOPTIONS': '""',
                },
                'upstream': 'ntp.org',
                'default_flags': None,
                'configs': {
                    '/etc/cron.d/ntpsync': {
                        'mode': '700',
                    },
                    '/etc/default/ntpdate': {
                    },
                    '/etc/ntp.conf': {
                    },
                    '/sbin/ntp-kill.sh': {
                        'mode': '755',
                    },
                    '/sbin/ntp-sync.sh': {
                        'mode': '755',
                    }
                }
            }
        )
        for g in ['makina.lxc', 'makina.docker']:
            if __grains__.get(g, False):
                data['activated'] = False
        if data['activated'] is None:
            data['activated'] = True
        data['defaults']['NTPSYNC'] = '"yes"'
        if not data['activated']:
            data['defaults']['NTPSYNC'] = '"no"'
        if data['default_flags'] is None:
            data['default_flags'] = ''
            for item in ['kod', 'limited', 'lowpriotrap']:
                if data[item]:
                    data['default_flags'] += ' {0}'.format(item)
            for item in ['trap', 'modify', 'peer', 'query']:
                if not data[item]:
                    data['default_flags'] += ' no{0}'.format(item)
        return data
    return _settings()
