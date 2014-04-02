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


def _checkpoint(ret):
    if not ret['result']:
        raise FailedStepError('stop')


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
        continue


def orchestrate(target, rets=None):
    if rets is None:
        rets = []
    return rets
    settings = cli('mc_cloud_compute_node.settings')
    t_settings = cli('mc_cloud_compute_node.get_settings_for_target', target)

    ret = result()
    rets = []
    ret = configure_cloud()
    return ret
    checkpoint(rets, ret)
    vms = {}
    configure()
    for vm in vms:
        try:
            ret = __salt__[
                'mc_cloud_{0}.orchestrate'.format(
                    vt)]()
            configure_vm(target, vm)
            ret = __salt__['mc_cloud_controller.post_configure'](compute_nodes)
        except:
            continue
    post_configure()
    checkpoint(rets, ret)
    return rets

#
