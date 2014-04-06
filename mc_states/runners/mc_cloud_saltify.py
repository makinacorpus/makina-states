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
    SaltyfificationError,
    MessageError,
    process_cloud_return,
)


log = logging.getLogger(__name__)


def cli(*args, **kwargs):
    if not kwargs:
        kwargs = {}
    kwargs.update({
        'salt_cfgdir': __opts__.get('config_dir', None),
        '__opts__': __opts__,
        'salt_cfg': __opts__.get('conf_file', None),
    })
    return client(*args, **kwargs)


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
                    raise SaltyfificationError(red('{0}'.format(data)))
            except KeyError:
                data = None
            if data is None:
                raise SaltyfificationError(
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


def orchestrate(output=True, refresh=False):
    '''Parse saltify settings to saltify all targets'''
    ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    comment = ''
    settings = cli('mc_cloud_saltify.settings')
    saltified = ret['changes'].setdefault('saltified', [])
    saltified_error = ret['changes'].setdefault('saltified_errors', [])
    targets = [a for a in settings['targets']]
    targets.sort()
    for idx, compute_node in enumerate(targets):
        try:
            cret = saltify(compute_node, output=False)
            if cret['result']:
                saltified.append(compute_node)
            else:
                raise SaltyfificationError(
                    'Target {0} failed to saltify:\n{1}'.format(
                        compute_node, cret['comment']))
        except Exception, exc:
            trace = traceback.format_exc()
            comment += yellow(
                '\nSaltificatioon failed for {0}: {1}'.format(compute_node,
                                                              exc))
            if not isinstance(exc, SaltyfificationError):
                ret['trace'] += '\n'.format(trace)
            log.error(trace)
            saltified_error.append(compute_node)
    if not comment:
        comment = green('All targets were successfuly saltifified.')
    ret['comment'] += '\n{0}'.format(comment)
    salt_output(ret, __opts__, output=output)
    return ret

#
