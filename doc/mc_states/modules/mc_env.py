#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_env:

mc_env / env registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_env

'''
# Import python libs
import logging
import mc_states.api
from mc_states.modules.mc_pillar import PILLAR_TTL

__name = 'env'

log = logging.getLogger(__name__)
RVM_URL = (
    'https://raw.github.com/wayneeseguin/env/master/binscripts/env-installer')


def is_reverse_proxied():
    return __salt__['mc_cloud.is_vm']()


def settings():
    '''
    env registry

    default_env
        Environment defaults (one of: dev/prod/preprod)
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        env = _s['mc_utils.get']('default_env', 'dev')
        data = _s['mc_utils.defaults'](
            'makina-states.localsettings.env', {
                'env': env})
        # retro compat
        data['default_env'] = data['env']
        return data
    return _settings()


def ext_pillar(id_, ttl=PILLAR_TTL, *args, **kw):
    def _do(id_, args, kw):
        rdata = {}
        conf = __salt__['mc_pillar.get_configuration'](id_)
        rdata['default_env'] = rdata['env'] = conf['default_env']
        return rdata
    cache_key = '{0}.{1}.{2}'.format(__name, 'ext_pillar', id_)
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, args, kw], {}, cache_key, ttl)
# vim:set et sts=4 ts=4 tw=80:
