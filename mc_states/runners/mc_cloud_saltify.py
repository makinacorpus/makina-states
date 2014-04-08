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
from pprint import pformat
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
    salt_output,
    green, red, yellow,
    check_point,
    client,
    FailedStepError,
    SaltyficationError,
    MessageError,
    process_cloud_return,
)


log = logging.getLogger(__name__)


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def saltify(name, output=True):
    '''Saltify a specific target'''
    try:
        ret = result()
        already_exists = __salt__['mc_cloud_controller.exists'](name)
        if already_exists:
            success = green('{0} is already saltified'.format(name))
        else:
            try:
                data = cli('mc_cloud_saltify.settings_for_target', name)
                if not isinstance(data, dict):
                    raise SaltyficationError(red('{0}'.format(data)))
            except KeyError:
                data = None
            if data is None:
                raise SaltyficationError(
                    red('Saltify target {0} is not configured'.format(name)))

            else:
                success = green('{0} is saltified')
                kwargs = {'minion': {'master': data['master'],
                                     'master_port': data['master_port']}}
                for var in [
                    "ssh_username", "ssh_keyfile", "keep_tmp", "gateway", "sudo",
                    "password", "script_args", "ssh_host", "sudo_password",
                ]:
                    if data.get(var):
                        kwargs[var] = data[var]
                try:
                    info = __salt__['cloud.profile'](data['profile'],
                                                     [name],
                                                     vm_overrides=kwargs)
                except Exception, exc:
                    trace = traceback.format_exc()
                    ret['trace'] = trace
                    raise FailedStepError(red('{0}'.format(exc)))
                ret = process_cloud_return(name, info, driver='saltify', ret=ret)
            if ret['result']:
                ret['comment'] = success
            if not output:
                ret['changes'] = {}
            check_point(ret, __opts__)
    except FailedStepError:
        ret['result'] = False
        salt_output(ret, __opts__, output=output)
    salt_output(ret, __opts__, output=output)
    return ret


def filter_compute_nodes(nodes, skip, only):
    '''filter compute nodes to run on'''
    targets = []
    for a in nodes:
        if a not in skip and a not in targets:
            targets.append(a)
    if only:
        if isinstance(only, basestring):
            if ',' not in only:
                only = [only]
            else:
                only = [a for a in only.split(',') if a.strip()]
        targets = [a for a in targets if a in only]
    targets.sort()
    return targets


def orchestrate(output=True, only=None, skip=None, refresh=False):
    '''Parse saltify settings to saltify all targets'''
    if skip is None:
        skip = []
    if only is None:
        only = []
    ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    comment = ''
    settings = cli('mc_cloud_saltify.settings')
    saltified = ret['changes'].setdefault('saltified', [])
    saltified_error = ret['changes'].setdefault('saltified_errors', [])
    targets = [a for a in settings['targets']]
    targets = filter_compute_nodes(targets, skip, only)
    targets.sort()
    for idx, compute_node in enumerate(targets):
        try:
            cret = saltify(compute_node, output=False)
            if cret['result']:
                saltified.append(compute_node)
            else:
                raise SaltyficationError(
                    'Target {0} failed to saltify:\n{1}'.format(
                        compute_node, cret['comment']))
        except Exception, exc:
            trace = traceback.format_exc()
            comment += yellow(
                '\nSaltyfication failed for {0}: {1}'.format(compute_node,
                                                              exc))
            if not isinstance(exc, SaltyficationError):
                ret['trace'] += '\n'.format(trace)
            log.error(trace)
            saltified_error.append(compute_node)
    if not comment:
        comment = green('All targets were successfuly saltified.')
    ret['comment'] += '\n{0}'.format(comment)
    salt_output(ret, __opts__, output=output)
    return ret

#
