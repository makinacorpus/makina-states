#!/usr/bin/env python
'''
.. _runner_mc_cloud_compute_node:

mc_cloud_compute_node runner
============================
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
    ComputeNodeProvisionError,
    salt_output,
    result,
    green, red, yellow,
    check_point,
    client,
    FailedStepError,
    merge_results,
    MessageError,
)


log = logging.getLogger(__name__)
_GPREF = 'makina-states.cloud.generic.compute_node'



def cn_sls_pillar(target):
    cloudSettings = cli('mc_cloud.settings')
    cloudSettingsData = {}
    cnSettingsData = {}
    cnSettingsData['cn'] = cli(
        'mc_cloud_compute_node.get_settings_for_target', target)
    cnSettingsData['rp'] = cli(
        'mc_cloud_compute_node.get_reverse_proxies_for_target', target)
    cloudSettingsData['all_sls_dir'] = cloudSettings['all_sls_dir']
    cloudSettingsData[
        'compute_node_sls_dir'] = cloudSettings['compute_node_sls_dir']
    cloudSettingsData[
        'prefix'] = cloudSettings['prefix']
    cloudSettingsData = api.json_dump(cloudSettingsData)
    cnSettingsData = api.json_dump(cnSettingsData)
    pillar = {'scloudSettings': cloudSettingsData,
              'scnSettings': cnSettingsData}
    return pillar


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def _checkpoint(ret):
    if not ret['result']:
        raise FailedStepError('stop')


def run_vt_hook(hook_name,
                target,
                ret=None,
                vts=None,
                output=True,
                *args, **kwargs):
    '''Difference with cloud controller bare one is that here
    we have the target argument mandatory'''
    return  __salt__['mc_cloud_controller.run_vt_hook'](hook_name,
                                                        target=target,
                                                        ret=ret,
                                                        vts=vts,
                                                        output=output,
                                                        *args, **kwargs)


def install_vts(target, ret=None, output=True):
    if ret is None:
        ret = result()
    ret = run_vt_hook('install_vt',
                      ret=ret, target=target, output=output)
    if ret['result']:
        ret['comment'] += yellow(
            '{0} is now ready to host vms\n'.format(target))
    salt_output(ret, __opts__, output=output)
    return ret


def _configure(what, target, ret, output):
    if ret is None:
        ret = result()
    ret['comment'] += yellow('Installing {1} on {0}\n'.format(target, what))
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(_GPREF, what), **{
            'salt_target': target,
            'ret': ret,
            'sls_kw': {'pillar': cn_sls_pillar(target)}})
    salt_output(ret, __opts__, output=output)
    return ret


def configure_sshkeys(target, ret=None, output=True):
    return _configure('sshkeys', target, ret, output)


def configure_firewall(target, ret=None, output=True):
    return _configure('firewall', target, ret, output)


def configure_reverse_proxy(target, ret=None, output=True):
    return _configure('reverse_proxy', target, ret, output)


def configure_hostsfile(target, ret=None, output=True):
    return _configure('hostsfile', target, ret, output)


def configure_grains(target, ret=None, output=True):
    return _configure('grains', target, ret, output)


def deploy(target, output=True, ret=None):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    if ret is None:
        ret = result()
    ret['comment'] += green('Installing compute node configuration\n')
    run_vt_hook('pre_deploy_compute_node',
                ret=ret, target=target, output=output)
    for step in [configure_sshkeys,
                 configure_grains,
                 install_vts,
                 configure_firewall,
                 configure_reverse_proxy]:
        step(target, ret=ret, output=False)
        check_point(ret, __opts__, output=output)
    run_vt_hook('post_deploy_compute_node',
                ret=ret, target=target, output=output)
    salt_output(ret, __opts__, output=output)
    return ret


def post_deploy(target, ret=None, output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    if ret is None:
        ret = result()
    hook = 'post_post_deploy_compute_node'
    ret['comment'] += green('Installing post compute node configuration\n')
    run_vt_hook(hook, ret=ret, target=target, output=output)
    for step in [configure_hostsfile]:
        step(target, ret=ret, output=False)
        check_point(ret, __opts__, output=output)
    run_vt_hook(hook, ret=ret, target=target, output=output)
    salt_output(ret, __opts__, output=output)
    return ret


def filter_compute_nodes(nodes, skip, only):
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


def provision_compute_nodes(skip=None, only=None,
                            output=True,
                            refresh=False,
                            ret=None):
    if only is None:
        only = []
    if skip is None:
        skip = []
    if ret is None:
        ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    settings = cli('mc_cloud_compute_node.settings')
    provision = ret['changes'].setdefault('cns_provisionned', [])
    provision_error = ret['changes'].setdefault('cns_in_error', [])
    targets = [a for a in settings['targets']]
    #targets += ['foo', 'bar']
    targets = filter_compute_nodes(targets, skip, only)
    for idx, compute_node in enumerate(targets):
        cret = result()
        try:
            deploy(compute_node, ret=cret, output=False)
            #if idx == 1:
            #    raise FailedStepError('foo')
            #elif idx > 0:
            #    raise Exception('bar')
        except FailedStepError:
            cret['result'] = False
        except Exception, exc:
            trace = traceback.format_exc()
            cret = {'result': False,
                    'output': 'unknown error on {0}\n{1}'.format(compute_node,
                                                                 exc),
                    'comment': 'unknown error on {0}\n'.format(compute_node),
                    'trace': trace}
        if cret['result']:
            if compute_node not in provision:
                provision.append(compute_node)
            # if everything is well, wipe the unseful output
            cret['output'] = ''
            cret['trace'] = ''
        else:
            ret['result'] = False
            if compute_node not in provision_error:
                provision_error.append(compute_node)
        cret.pop('result', False)
        merge_results(ret, cret)
    if len(provision_error):
        ret['comment'] += red('There were errors while provisionning '
                              'computes nodes {0}\n'.format(provision_error))
    else:
        del ret['trace']
        ret['comment'] += green('All computes nodes were provisionned\n')
    salt_output(ret, __opts__, output=output)
    return ret


def post_provision(skip=None, skip_vms=None,
                   only_compute_nodes=None, only_vms=None,
                   output=True, refresh=False, ret=None):
    if only_compute_nodes is None:
        only_compute_nodes = []
    if only_vms is None:
        only_vms = {}
    if skip is None:
        skip = []
    if skip_vms is None:
        skip_vms = {}
    if ret is None:
        ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    settings = cli('mc_cloud_compute_node.settings')
    provision = ret['changes'].setdefault('post_provisionned', [])
    provision_error = ret['changes'].setdefault('post_in_error', [])
    targets = []
    for a in settings['targets']:
        if a not in skip and a not in targets:
            targets.append(a)
        else:
            ret['comment'] += yellow(
                'compute node {0} post-provision skipped\n'.format(a))
    targets.sort()
    targets += ['foo', 'bar']
    for idx, compute_node in enumerate(targets):
        cret = result()
        try:
            post_deploy(compute_node, ret=cret, output=False)
            if idx  == 1:
                raise FailedStepError('foo')
            elif idx > 0:
                raise Exception('bar')
        except FailedStepError:
            cret['result'] = False
        except Exception, exc:
            trace = traceback.format_exc()
            cret = {'result': False,
                    'comment': 'unknown error {0}'.format(exc),
                    'trace': trace}
        if cret['result']:
            if compute_node not in provision:
                provision.append(compute_node)
            # if everything is well, wipe the unseful output
            cret['output'] = ''
            cret['trace'] = ''
        else:
            ret['result'] = False
            if compute_node not in provision_error:
                provision_error.append(compute_node)
        cret.pop('result', False)
        merge_results(ret, cret)
    if len(provision_error):
        ret['comment'] += red('There were errors while post provisionning '
                              'nodes {0}\n'.format(provision_error))
    else:
        del ret['trace']
        ret['comment'] += green('All nodes were post provisionned\n')
    salt_output(ret, __opts__, output=output)
    return ret


def orchestrate(skip=None,
                skip_vms=None,
                only_compute_nodes=None,
                only_vms=None,
                output=True,
                refresh=False,
                ret=None):
    if skip is None:
        skip = []
    if skip_vms is None:
        skip_vms = {}
    if only_compute_nodes is None:
        only_compute_nodes = []
    if only_vms is None:
        only_vms = []
    if ret is None:
        ret = result()
    provision_compute_nodes(skip=skip, only=only_compute_nodes,
                            output=False, refresh=refresh, ret=ret)
    skip = [a for a in skip + ret['cns_in_error']]

    vcret = result()
    for compute_node in ret['cns_provisionned']:
        __salt__['mc_cloud.vm.orchestrate'](compute_node, output=False,
                                            skip=skip_vms, only=only_vms,
                                            refresh=refresh, ret=vcret)
    vms_in_error = ret['changes']['vms_in_errors'] = vcret[
        'changes'].get('in_error', [])
    ret['comment'] += vcret['comment']
    if len(vms_in_error):
        ret['trace'] += vcret['trace']
        ret['comment'] += red('There where errors while provisionning vms\n')
    else:
        ret['comment'] += green('All vms were provisionned\n')
    skip_vms.update(vms_in_error)

    pcret = result()
    post_provision(skip=skip, skip_vms=skip_vms,
                   output=output, refresh=refresh, ret=pcret)
    pcn_in_error = ret['changes']['cn_in_post_provisionerrors'] = pcret[
        'changes'].get('in_error', [])
    ret['comment'] += pcret['comment']
    if len(pcn_in_error):
        ret['comment'] += red(
            'There were error with post procedures controller/vm\n')
        ret['trace'] += cret['trace']
    else:
        ret['comment'] += green(
            'All post procedures controller/vm were done\n')
    return ret
#
