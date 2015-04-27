# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
'''
.. _module_mc_dns:

mc_dns / dns settings
=======================


The main settings in there is "default_dnses" which are the dns for resolution
As soon as you install a dns service on the behalf of makina-states

'''

import logging
from mc_states import api
six = api.six


log = logging.getLogger(__name__)


def settings(ttl=15*60):

    def _do():
        settings = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.dns', {
                'no_default_dnses': False,
                'default_dnses': []})
        if not settings['no_default_dnses']:
            for i in [
                '127.0.0.1',
                '127.0.1.1',
                '8.8.8.8',
                '4.4.4.4'
            ]:
                if i not in settings['default_dnses']:
                    settings['default_dnses'].append(i)
        settings['default_dnses'] = __salt__['mc_utils.uniquify'](
            settings['default_dnses'])
        return settings
    cache_key = 'mc_dns.settings'
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)
