#!/usr/bin/env python
'''

.. _runner_mc_cloud_vm:

mc_cloud_lxc runner
==========================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import python libs
import os
import traceback
import logging

# Import salt libs
import salt.client
import salt.payload
import salt.utils
from salt.utils import check_state_result
import salt.output
import salt.minion
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states.saltapi import (
    result,
    green, red, yellow,
    check_point,
    client,
    FailedStepError,
    MessageError,
)


log = logging.getLogger(__name__)


def _checkpoint(ret):
    if not ret['result']:
        raise FailedStepError('stop')


def pre_deploy(output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    ret = result()
    try:
        run_vt_hook(ret, 'pre_configure_controller')
        id_ = cli('config.get', 'id')
        cret = cli('state.sls',
                   'makina-states.cloud.generic.controller.pre-deploy')
        ret['result'] = check_state_result(cret)
        ret['output'] = salt.output.get_printout(
            'highstate', __opts__)({id_: cret})
        if ret['result']:
            ret['comment'] += green(
                'Global cloud controller configuration is applied')
        else:
            ret['comment'] += red(
                'Cloud controller failed to configure:\n')
        check_point(ret)
        run_vt_hook(ret, 'post_configure_controller')
    except FailedStepError:
        if output:
            salt.output.display_output(ret, '', __opts__)
        raise
    if output:
        salt.output.display_output(ret, '', __opts__)
    return ret


def configure():
    ret = result()
    return ret


def postconfigure():
    ret = result()
    return ret


def configure_firewall(target):
    ret = result()
    return ret


def configure(target, vm):
    ret = result()
    return ret
    try:
        pass
    except:
        pass


def saltify(name, data):
    ret = result()
    cloudSettings = salt['mc_cloud.settings']()
    settings = salt['mc_cloud_saltify.settings']()
    key = '{prefix}/pki/master/minions/{name}'.format(
        prefix=cloudSettings.prefix, name=name)
    if os.path.exists(key):
        success = '{0} is already saltified'
    else:
        success = '{0} is saltified'
        kwargs = {'minion': {
            'master': data['master'],
            'master_port': data['master_port']}}
        for var in [
            "ssh_username", "ssh_keyfile", "keep_tmp", "gateway", "sudo",
            "password", "script_args", "ssh_host", "sudo_password",
        ]:
            if data.get(var):
                kwargs[var] = data[var]
        cret = __salt__['cloud.profile'](data['profile'], [name], **kwargs)
    return ret


def orchestrate(target, rets=None):
    ret = result()
    t_settings = cli('mc_cloud_compute_node.get_settings_for_target', target)
    settings = salt['mc_cloud_saltify.settings']()
    saltified = ret.setdefault('saltified', [])
    for compute_node, data in settings['targets'].items():
        try:
            cret = saltify(target, data)
            if cret['result']:
            saltified.append(compute_node)
        except Exception:
            trace = traceback.format_exc()
            log.error(trace)
            continue
    checkpoint(ret)
    return ret

#
