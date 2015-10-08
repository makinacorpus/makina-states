# -*- coding: utf-8 -*-
'''

.. _state_mc_apache:

mc_apache / apache states
============================================



If you alter this module and want to test it, do not forget to deploy it on
minion using::

  salt '*' saltutil.sync_states

If you use this state as a template for a new custom state
do not forget to use to get this module included in salt modules.

To comment

.. code-block:: yaml

    apache-main-conf:
      makina-states.apache.deployed:
        - version: 2.2
        - log_level: debug

Or using the "names:" directive, you can put several names for the same IP.
(Do not try one name with space-separated values).

.. code-block:: yaml

    server1:
      host.present:
        - ip: 192.168.0.42
        - names:
          - server1
          - florida


'''

# Import python libs
from mc_states.api import six
import logging

# Import salt libs

log = logging.getLogger(__name__)

# Modules explicitly required by states
# Module explicitly excluded by states

_DEFAULT_MPM = 'worker'


def deployed(name, *args, **kwargs):
    '''
    DEPRECATED
    '''
    comment = 'apache.deployed is deprecated and unactivated'
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': comment}
    log.error(comment)
    # DEPRECATED !!!
    return ret


def _toggle_mods(modules, action, name='name'):
    mods = {}
    ret = {'changes': mods, 'name': name, 
           'result': None, 'comment': ''}
    if not modules:
        modules = []
    else:
        ret['result'] = True
    if isinstance(modules, six.string_types):
        modules = modules.split(',')
    for module in modules:
        if not __opts__['test']:
            result = __salt__[
                'mc_apache.{0}'.format(action)](module)
        else:
            result= {'changed': True, 'result': True}
        comment = '{1} {0}\n'.format(module, action)
        if not result['result']:
            comment = 'FAILURE {1} {0}\n'.format(
                module, action)
            comment += result['return']['stdout'] + '\n'
            comment += result['return']['stderr'] + '\n'
            ret['result'] = False
        if result.get('changed', False):
            mods[module] = action
        ret['comment'] += comment
    return ret
 


def include_module(name, modules):
    '''
    Soft enable one or mode apache modules

        name
            ignored
        modules
            list or comma separated list of modules
    '''
    return _toggle_mods(modules, action='a2enmod', name=name)


def exclude_module(name, modules):
    '''
    Soft disable one or mode apache modules

        name
            ignored
        modules
            list or comma separated list of modules
    '''
    return _toggle_mods(modules, action='a2dismod', name=name)
