# -*- coding: utf-8 -*-
'''
.. _module_mc_project:

mc_project / project
============================================



Corpus PaaS project management: state part
'''

# Import python libs
import logging
import traceback

# Import salt libs

log = logging.getLogger(__name__)

def deployed(name, api_ver='2', **kwargs):
    '''
    Ensures that apache is deployed, once, with given version and main settings

    name
        The state name, not used internally

    version
        The apache version

    '''
    ret = {'name': name, 'changes': {}, 'result': True, 'comment': ''}
    kwargs['name'] = name
    try:
        cret = __salt__['init_project'](api_ver=api_ver, **kwargs)
        ret.update(cret)
    except Exception, ex:
        trace = traceback.format_exc()
        ret['comment'] =(
            'Error while creating project {0}\n{1}'.format(
                ex, trace))
        ret['result'] = False
    return ret

#
