#!/usr/bin/python python
# -*- coding: utf-8 -*-
'''

.. _module_mc_python:

mc_python / python registry
============================================



If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_python

'''
# Import python libs
import logging
import mc_states.api

__name = 'python'

log = logging.getLogger(__name__)


def settings():
    '''
    python registry

    versions
        python versions
    alt_versions
        different versions from system(internal var)
    version
        current version
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        pillar = __pillar__
        data = {}
        cur_pyver = grains['pythonversion']
        if isinstance(cur_pyver, list):
            cur_pyver = '.'.join(['{0}'.format(s) for s in cur_pyver])
        cur_pyver = cur_pyver[:3]
        data['cur_pyver'] = cur_pyver
        data = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.python', {
                'versions': [cur_pyver],
                'alt_versions': [cur_pyver],
                'version': cur_pyver,
            })
        data['alt_versions'] = filter(lambda x: x != cur_pyver,
                                      data['alt_versions'])
        return data
    return _settings()



#
# -*- coding: utf-8 -*-

# vim:set et sts=4 ts=4 tw=80:
