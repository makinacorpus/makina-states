#!/usr/bin/env python

'''
.. _runner_mc_lxc:

Jobs for lxc managment
==========================
'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import python libs
import os
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
    result,
    green, red, yellow,
    check_point,
    client,
    FailedStepError,
    MessageError,
)

import salt.output


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


def configure(output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    ret = result()
    try:
        id_ = cli('config.get', 'id')
        cret = cli('state.sls',
                   'makina-states.cloud.generic.controller.pre-deploy')
        ret['result'] = check_state_result(cret)
        ret['output'] = salt.output.get_printout(
            'highstate', __opts__)({id_: cret})
        import pdb;pdb.set_trace()  ## Breakpoint ##
        if ret['result']:
            ret['comment'] += green(
                'Global cloud controller configuration is applied')
        else:
            ret['comment'] += red(
                'Cloud controller failed to configure:\n')
        settings = cli('mc_cloud_controller.settings')
        check_point(ret)
        for vt in settings['vts']:
            vid_ = 'mc_cloud_{0}.configure_controller'.format(vt)
            if id_ in __salt__:
                import pdb;pdb.set_trace()  ## Breakpoint ##
                cret = __salt__(vid_, output=False)
                cret['result'] = False
                if cret[' output']:
                    ret['output'] += cret['output']
                if cret['result']:
                    ret['comment'] += ret['comment']
                else:
                    ret['comment'] += red(
                        'Cloud controller failed to configure:\n')
                check_point(ret)
    except FailedStepError:
        if output:
            salt.output.display_output(ret, '', __opts__)
        raise
    if output:
        salt.output.display_output(ret, '', __opts__)
    return ret


def postconfigure():
    ret = result()
    return ret


def orchestrate(output=True):
    ret = result()
    rets = []
    settings = cli('mc_cloud_controller.settings')
    computes_nodes = {}
    try:
        ret = configure()
        check_point(ret)
        ret['comment'] += cret['comment']
        #for compute node in compute_nodes():
        #    __salt__['mc_cloud_controller.saltify'](compute_nodes)
        #for compute node in compute_nodes():
        #    try:
        #       ret =  orchestrate(compute_node)
        #       checkpoint(rets, ret, failhard=True)
        #    except:
        #        continue
        #    checkpoint(rets, ret)
        cret = post_configure()
        checkpointcret)
        ret['comment'] += cret['comment']
    except FailedStepError:
        if output:
            salt.output.display_output(ret, '', __opts__)
        raise
    if output:
        salt.output.display_output(ret, '', __opts__)
    return ret

#
