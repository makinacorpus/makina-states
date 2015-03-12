# -*- coding: utf-8 -*-
'''
.. _module_mc_registry:

mc_registry / local registries
============================================



Makina-States local registries management
'''

# Import python libs
import logging
import traceback

# Import salt libs

log = logging.getLogger(__name__)


def update(name, params, **kw):
    '''
    Active or deactive a param in the named makina-states
    loccalregistry
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': '{1} in registry {0} up to date'.format(name, params)}
    _default = object()
    reg_obj = __salt__['mc_{0}.registry'.format(name)]()
    reg = __salt__['mc_macros.get_local_registry'](name)
    sync = False
    if params is None:
        ret['result'] = False
        ret['changes'] = {}
        ret['comment'] = 'Params missing for {0}'.format(name)
        return ret
    for param, value in params.items():
        gparam = '{0}.{1}'.format(reg_obj['grains_pref'], param)
        if reg.get(gparam, _default) != value:
            sync = True
    if sync:
        try:
            cret = __salt__['mc_macros.update_registry_params'](name, params)
            ret['changes'] = cret
            ret['comment'] = 'Params updated for {0}'.format(name)
        except Exception, ex:
            trace = traceback.format_exc()
            ret['comment'] =(
                'Error while creating project {0}\n{1}'.format(
                    ex, trace))
            ret['result'] = False
    return ret


def toggle(name, sls=None, slss=None, status=True):
    if (not sls) and (not slss):
        return {'name': name,
                'changes': {},
                'result': False,
                'comment': 'no sls'}
    if slss is None:
        slss = []
    if sls and (not sls in slss):
        slss.append(sls)
    return update(name, dict([(a, status) for a in slss]))


def present(name, sls=None, slss=None, **kw):
    return toggle(name, sls=sls, slss=slss, status=True)


def absent(name, sls=None, slss=None, **kw):
    return toggle(name, sls=sls, slss=slss, status=False)

#
