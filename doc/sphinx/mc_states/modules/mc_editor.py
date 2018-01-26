#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_editor:

mc_editor / editor registry
============================================


'''
# Import python libs
import logging
import mc_states.api

__name = 'editor'

log = logging.getLogger(__name__)


def settings():
    '''
    editor registry

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.editor', {
                'editor': '/usr/bin/vim.nox',
            })
        return data
    return _settings()
# editor:set et sts=4 ts=4 tw=80:
