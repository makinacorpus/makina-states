#!/usr/bin/env python
from __future__ import absolute_import, print_function
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
from mc_states.modules.mc_utils import dictupdate
from salt.utils import check_state_result
import salt.output
import salt.minion
from salt.utils.odict import OrderedDict
from mc_states.utils import memoize_cache

from mc_states import api
from mc_states.saltapi import (
    ComputeNodeProvisionError,
    salt_output,
    result,
    green, red, yellow,
    check_point,
    client,
    FailedStepError,
    result,
    merge_results,
    MessageError,
)


log = logging.getLogger(__name__)
_GPREF = 'makina-states.cloud.generic.compute_node'



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
    '''
    Difference with cloud controller bare one is that here
    we have the target argument mandatory
    '''
    func_name = 'mc_compute_node.run_vt_hook {0} {1}'.format(
        target, hook_name)
    __salt__['mc_api.time_log']('start', func_name)
    ret = __salt__['mc_cloud_controller.run_vt_hook'](hook_name,
                                                      target=target,
                                                      ret=ret,
                                                      vts=vts,
                                                      output=output,
                                                      *args, **kwargs)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def upgrade_vts(target, ret=None, output=True):
    '''
    upgrade all virtual types to be ready to host vms
    '''
    func_name = 'mc_compute_node.install_vts {0}'.format(target)
    __salt__['mc_api.time_log']('start', func_name)
    if ret is None:
        ret = result()
    ret = run_vt_hook('upgrade_vt', ret=ret, target=target, output=output)
    if ret['result']:
        ret['comment'] += yellow(
            '{0} is now upgraded to host vms\n'.format(target))
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def install_vts(target, ret=None, output=True):
    '''
    install all virtual types to be ready to host vms
    '''
    func_name = 'mc_compute_node.install_vts {0}'.format(target)
    __salt__['mc_api.time_log']('start', func_name)
    if ret is None:
        ret = result()
    ret = run_vt_hook('install_vt',
                      ret=ret, target=target, output=output)
    if ret['result']:
        ret['comment'] += yellow(
            '{0} is now ready to host vms\n'.format(target))
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def _configure(what, target, ret, output):
    #__salt__['mc_cloud_compute_node.lazy_register_configuration'](target)
    func_name = 'mc_compute_node._configure {0} {1}'.format(what, target)
    __salt__['mc_api.time_log']('start', func_name)
    if ret is None:
        ret = result()
    ret['comment'] += yellow('Installing {1} on {0}\n'.format(target, what))
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(_GPREF, what), **{
            'salt_target': target, 'ret': ret})
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def configure_sshkeys(target, ret=None, output=True):
    '''
    drop the compute node ssh key
    '''
    return _configure('sshkeys', target, ret, output)


def configure_sslcerts(target, ret=None, output=True):
    '''
    deploy SSL certificates on compute node
    '''
    return _configure('sslcerts', target, ret, output)


def configure_host(target, ret=None, output=True):
    '''
    shorewall configuration
    '''
    return _configure('host', target, ret, output)


def configure_firewall(target, ret=None, output=True):
    '''
    shorewall configuration
    '''
    return _configure('firewall', target, ret, output)


def configure_reverse_proxy(target, ret=None, output=True):
    '''
    haproxy configuration
    '''
    return _configure('reverse_proxy', target, ret, output)


def configure_hostsfile(target, ret=None, output=True):
    '''
    local dns configuration
    '''
    return _configure('hostsfile', target, ret, output)


def configure_network(target, ret=None, output=True):
    '''
    install network configuration
    '''
    return _configure('network', target, ret, output)


def configure_prevt(target, ret=None, output=True):
    '''
    install all prevt steps
    '''
    return _configure('prevt', target, ret, output)


def reconfigure_front(target, ret=None, output=True):
    '''
    Small hook to reconfigure the reverse proxy part of
    a compute node, meaned to be used via the CLI
    '''
    for step in [
        configure_host
    ]:
        step(target, ret=ret, output=False)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    return ret


def deploy(target, output=True, ret=None, hooks=True, pre=True, post=True):
    '''
    Prepare cloud controller configuration
    can also apply per virtualization type configuration
    '''
    #__salt__['mc_cloud_compute_node.lazy_register_configuration'](target)
    func_name = 'mc_compute_node.deploy {0}'.format(target)
    __salt__['mc_api.time_log']('start', func_name)
    if ret is None:
        ret = result()
    ret['comment'] += green('Installing compute node configuration\n')
    if hooks and pre:
        run_vt_hook('pre_deploy_compute_node',
                    ret=ret, target=target, output=output)
    for step in [
        configure_prevt,
        install_vts,
        configure_network,
        reconfigure_front
    ]:
        step(target, ret=ret, output=False)
        check_point(ret, __opts__, output=output)
    if hooks and post:
        run_vt_hook('post_deploy_compute_node',
                    ret=ret, target=target, output=output)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def post_deploy(target, ret=None, output=True):
    '''
    Prepare cloud controller configuration
    can also apply per virtualization type configuration
    '''
    func_name = 'mc_compute_node.post_deploy {0}'.format(target)
    __salt__['mc_api.time_log']('start', func_name)
    if ret is None:
        ret = result()
    hook = 'pre_post_deploy_compute_node'
    run_vt_hook(hook, ret=ret, target=target, output=output)
    for step in []:
        step(target, ret=ret, output=False)
        check_point(ret, __opts__, output=output)
    hook = 'post_post_deploy_compute_node'
    run_vt_hook(hook, ret=ret, target=target, output=output)
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def filter_compute_nodes(nodes, skip, only):
    '''filter compute nodes to run on'''
    func_name = 'mc_compute_node.filter_compute_nodes'
    __salt__['mc_api.time_log']('start', func_name)
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
    __salt__['mc_api.time_log']('end', func_name, targets=targets)
    return targets


def provision_compute_nodes(skip=None, only=None,
                            no_compute_nodes=False,
                            output=True,
                            refresh=True,
                            ret=None):
    '''provision compute nodes

        skip
            list or comma separated string of compute node
            to skip (will skip contained vms too)
        only
            list or comma separated string of compute node
            If set, it will only provision those compute nodes
            and contained vms

    '''
    func_name = 'mc_compute_node.provision_compute_nodes'
    __salt__['mc_api.time_log']('start', func_name)
    only, _, skip, __ = (
        __salt__['mc_cloud_controller.gather_only_skip'](
            only=only, skip=skip))
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
        if no_compute_nodes:
            cret['comment'] = yellow(
                'Compute node configuration skipped for {0}\n'
            ).format(compute_node)
        else:
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
        if ret['result']:
            ret['trace'] = ''
            ret['comment'] += green('All computes nodes were provisionned\n')
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def post_provision_compute_nodes(skip=None, only=None,
                                 output=True, refresh=False, ret=None):
    '''post provision all compute nodes

    '''
    func_name = 'mc_compute_node.post_provision_compute_nodes'
    __salt__['mc_api.time_log']('start', func_name)
    only, _, skip, __ = (
        __salt__['mc_cloud_controller.gather_only_skip'](
            only=only, skip=skip))
    if ret is None:
        ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    settings = cli('mc_cloud_compute_node.settings')
    provision = ret['changes'].setdefault('postp_cns_provisionned', [])
    provision_error = ret['changes'].setdefault('postp_cns_in_error', [])
    targets = [a for a in settings['targets']]
    #targets += ['foo', 'bar']
    targets = filter_compute_nodes(targets, skip, only)
    for idx, compute_node in enumerate(targets):
        cret = result()
        try:
            post_deploy(compute_node, ret=cret, output=False)
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
        ret['comment'] += red('There were errors while postprovisionning '
                              'computes nodes {0}\n'.format(provision_error))
    else:
        if ret['result']:
            ret['trace'] = ''
            ret['comment'] += green(
                'All computes nodes were postprovisionned\n')
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def orchestrate(skip=None,
                skip_vms=None,
                only=None,
                only_vms=None,
                no_compute_nodes=False,
                no_provision=False,
                no_post_provision=False,
                no_vms_post_provision=False,
                no_vms=False,
                output=True,
                refresh=True,
                ret=None):
    '''Orchestrate the whole cloud deployment.
    In this order:

        - provision compute nodes minus the skipped one
          and limiting to the 'only' if any
        - provision vms minus the skipped one
          and limiting to the 'only_compute_vm' if any.
          If the vms are to be hosted on a failed host, they
          will be skipped
        - post provision compute nodes
        - post provision vms


        skip
            list or comma separated string of compute node
            to skip (will skip contained vms too)
        only
            list or comma separated string of compute node
            If set, it will only provision those compute nodes
            and contained vms
        no_provision
            do not run the compute nodes provision
        no_post_provision
            do not run the compute nodes post provision
        no_compute_nodes
            skip configuration of compute nodes
        skip_vms
            list or comma separated string of vms
            to skip
        only_vms
            list or comma separated string of vms.
            If set, it will only provision those vms
        no_vms
            do not run the vm provision
        no_vms_post_provision
            do not run the vms post provision
    '''
    func_name = 'mc_compute_node.orchestrate'
    __salt__['mc_api.time_log']('start', func_name)
    if refresh:
        cli('saltutil.refresh_pillar')
    if ret is None:
        ret = result()
    chg = ret['changes']
    lresult = True
    only, only_vms, skip, skip_vms = (
        __salt__['mc_cloud_controller.gather_only_skip'](
            only=only, only_vms=only_vms,
            skip=skip, skip_vms=skip_vms))
    if not no_provision:
        provision_compute_nodes(
            skip=skip, only=only,
            no_compute_nodes=no_compute_nodes,
            output=False, refresh=False, ret=ret)
        for a in ret.setdefault('cns_in_error', []):
            if a not in skip:
                lresult = False
                skip.append(a)
        if not no_vms:
            for compute_node in chg.setdefault('cns_provisionned', []):
                __salt__['mc_cloud_vm.orchestrate'](
                    compute_node, output=False,
                    skip=skip_vms, only=only_vms,
                    refresh=False, ret=ret)
            vms_in_error = chg.setdefault('vms_in_error', {})
            for node in vms_in_error:
                for vm in vms_in_error[node]:
                    if vm not in skip_vms:
                        lresult = False
                        skip_vms.append(vm)

    if not no_post_provision:
        post_provision_compute_nodes(skip=skip, only=only,
                                     output=False,
                                     refresh=False,
                                     ret=ret)
        for a in chg.setdefault('postp_cns_in_error', []):
            if a not in skip:
                lresult = False
                skip.append(a)

        if not no_vms and not no_vms_post_provision:
            for compute_node in chg['cns_provisionned']:
                __salt__['mc_cloud_vm.post_provision_vms'](
                    compute_node, output=False,
                    skip=skip_vms, only=only_vms,
                    refresh=False, ret=ret)
            vms_in_error = chg.setdefault('postp_vms_in_errors', {})
            for node in vms_in_error:
                for vm in vms_in_error[node]:
                    if vm not in skip_vms:
                        skip_vms.append(vm)
                        lresult = False
    ret['result'] = lresult
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret


def report(targets, ret=None, refresh=False, output=True):
    '''Parse all reachable compute nodes and vms
    and regenerate the local configuration registries concerning
    cloud deployment'''
    func_name = 'mc_compute_node.report'
    __salt__['mc_api.time_log']('start', func_name)
    settings = cli('mc_cloud_compute_node.ext_pillar', prefixed=False)
    if ret is None:
        ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    sret = ''
    if not isinstance(targets, list):
        targets = targets.split(',')
    for target in targets:
        if target in settings['targets']:
            for vm in settings['targets'][target]['vms']:
                if vm not in targets:
                    targets.append(vm)
    for idx, target in enumerate(targets):
        try:
            if not cli('test.ping', salt_target=target):
                continue
        except Exception:
            continue
        sret += '{0}'.format(
            cli('mc_project.report', salt_target=target)
        )
    ret['result'] = sret
    __salt__['mc_api.out'](ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end', func_name, ret=ret)
    return ret
#    return _configure('grains', target, ret, output)
