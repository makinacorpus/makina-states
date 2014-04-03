#!/usr/bin/env python
'''

.. _runner_mc_cloud_controller:

mc_cloud_controller runner
==========================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import python libs
import os
import logging
import traceback

from pprint import pformat

# Import salt libs
from salt.utils import check_state_result
import salt.client
import salt.payload
import salt.utils
import salt.output
import salt.minion
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states.saltapi import (
    salt_output,
    result,
    green, red, yellow,
    check_point,
    client,
    FailedStepError,
    MessageError,
)

import salt.output

log = logging.getLogger(__name__)


def cli(*args, **kwargs):
    if not kwargs:
        kwargs = {}
    kwargs.update({
        'salt_cfgdir': __opts__.get('config_dir', None),
        'salt_cfg': __opts__.get('conf_file', None),
    })
    return client(*args, **kwargs)


def post_configure(output=True):
    return result()


def run_vt_hook(ret, hook_name):
    settings = cli('mc_cloud_controller.settings')
    for vt in settings['vts']:
        vid_ = 'mc_cloud_{0}.{1}'.format(vt, hook_name)
        if vid_ in __salt__:
            cret = __salt__[vid_](output=False)
            if not cret['result']:
                ret['result'] = False
            if cret['output']:
                ret['output'] += cret['output']
            if cret['result']:
                ret['comment'] += ret['comment']
            else:
                ret['comment'] += red(
                    'Cloud controller failed to configure:\n')
            check_point(ret)


def _sls_exec(sls,
              success='Sucess',
              error='Error',
              id_='local',
              ret=None):
    if ret is None:
        ret = result()
    cret = cli('state.sls', sls)
    ret['result'] = check_state_result(cret)
    ret['output'] = salt.output.get_printout(
        'highstate', __opts__)({id_: cret})
    if ret['result']:
        ret['comment'] += green(success)
    else:
        ret['comment'] += red(error)
    return ret


def pre_deploy(output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    ret = result()
    try:
        run_vt_hook(ret, 'pre_configure_controller')
        id_ = cli('config.get', 'id')
        _sls_exec(
            'makina-states.cloud.generic.controller.pre-deploy',
            success='Global cloud controller configuration is applied',
            error='Cloud controller failed to configure',
            id_=id_,
            ret=ret)
        _sls_exec(
            'makina-states.cloud.saltify',
            success='Cloud controller saltify configuration is applied',
            error='Cloud controller saltify configuration failed to configure',
            id_=id_,
            ret=ret)
        check_point(ret)
        run_vt_hook(ret, 'post_configure_controller')
    except FailedStepError:
        salt_output(ret, __opts__, output=output)
        raise
    salt_output(ret, __opts__, output=output)
    return ret


def deploy():
    ret = result()
    run_vt_hook(ret, 'pre_deploy_controller')
    run_vt_hook(ret, 'post_deploy_controller')
    return ret


def post_deploy():
    ret = result()
    run_vt_hook(ret, 'pre_post_deploy_controller')
    run_vt_hook(ret, 'post_post_deploy_controller')
    return ret


def orchestrate(output=True, refresh=True):
    ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    rets = []
    try:
        ret = pre_deploy()
        check_point(ret)
        ret = deploy()
        check_point(ret)
        cret = __salt__['mc_cloud_saltify.orchestrate'](output=False,
                                                        refresh=False)
        if cret['result']:
            ret['comment'] += cret['comment']
        check_point(rets, ret)
        saltified_errors = cret['changes'].get('saltified_errors', [])
        cret = __salt__['mc_cloud_compute_node.orchestrate'](skip=saltified_errors)
        # check_point(rets, ret)
        ret = post_deploy()
        check_point(cret)
        ret['comment'] += cret['comment']
    except FailedStepError:
        salt_output(ret, __opts__, output=output)
        raise
    salt_output(ret, __opts__, output=output)
    return ret


def exists(name):
    cloudSettings = cli('mc_cloud.settings')
    key = '{prefix}/pki/master/minions/{name}'.format(
        prefix=cloudSettings['prefix'], name=name)
    already_exists = os.path.exists(key)
    if not already_exists:
        try:
            instance = __salt__['cloud.action'](
                fun='show_instance', names=[name])
            prov = str(instance.keys()[0])
            if instance and 'Not Actioned' not in prov:
                already_exists = True
        except:
            trace = traceback.format_exc()
            log.warn(trace)
    return already_exists


#
