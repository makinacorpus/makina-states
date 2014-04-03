#!/usr/bin/env python
'''

.. _runner_mc_cloud_vm:

mc_cloud_vm runner
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
import salt.output
from salt.utils import check_state_result
import salt.minion
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states.saltapi import (
    result,
    check_point,
    green, red, yellow,
    client,
    FailedStepError,
    MessageError,
)

log = logging.getLogger(__name__)


def postdeploy(target, vm):
    ret = __salt__['mc_cloud_vm.install_highstate'](vm)
    checkpoint(rets, ret)


def orchestrate_vm(target, vt, vm, rets=None):
    if rets is None:
        rets = []
    return rets
    settings = cli('mc_cloud_lxc.settings')
    vm_settings = cli(
        'mc_cloud_compute_{0}.get_settings_for_vm'.format(vt),
        target, vm)
    try:
        for step in [
            'configure',
            'deploy',
            'postdeploy',
        ]:
            cret = __salt__['mc_cloud_{1}.{0}'.format](target, vm, vt)
            checkpoint(rets, ret)

            cret = __salt__['mc_cloud_vm.{0}'.format](target, vm)
            checkpoint(rets, ret)
            cret = __salt__['mc_cloud_{1}.{0}'.format](target, vm, vt)
    except:
        pass
    checkpoint(rets, ret)
    ret = __salt__['mc_cloud_vm.spawn'](vm)
    checkpoint(rets, ret)
    ret = __salt__['mc_cloud_vm.post_configure'](vm, salt_target=vm)
    checkpoint(rets, ret)
    return rets


# vim:set et sts=4 ts=4 tw=80:
