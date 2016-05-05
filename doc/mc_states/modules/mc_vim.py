#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_vim:

mc_vim / vim registry
============================================



If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_vim

'''
# Import python libs
import logging
import mc_states.api

__name = 'vim'

log = logging.getLogger(__name__)


def settings():
    '''
    vim registry

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        kiorky_config = True
        full = True
        if __salt__['mc_nodetypes.is_docker']():
            kiorky_config = False
            full = False
        data = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.vim', {
                'kiorky_config': kiorky_config,
                'full': full,
                'package': 'vim-nox',
                'editor': '/usr/bin/vim.nox',
                'packages': []
            })
        if data['package']:
            data['packages'].append(data['package'])
            if data['full']:
                data['packages'].append('exuberant-ctags')
        return data
    return _settings()
# vim:set et sts=4 ts=4 tw=80:
