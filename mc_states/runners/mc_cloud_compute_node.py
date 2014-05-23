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
    result,
    merge_results,
    MessageError,
)


log = logging.getLogger(__name__)
_GPREF = 'makina-states.cloud.generic.compute_node'


def cn_sls_pillar(target):
    '''limited cloud pillar to expose to a compute node'''
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
    cloudSettingsData['prefix'] = cloudSettings['prefix']
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
    '''install all virtual types to be ready to host vms'''
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
    '''drop the compute node ssh key'''
    return _configure('sshkeys', target, ret, output)


def configure_sslcerts(target, ret=None, output=True):
    '''shorewall configuration'''
    return _configure('sslcerts', target, ret, output)


def configure_firewall(target, ret=None, output=True):
    '''shorewall configuration'''
    return _configure('firewall', target, ret, output)


def configure_reverse_proxy(target, ret=None, output=True):
    '''haproxy configuration'''
    return _configure('reverse_proxy', target, ret, output)


def configure_hostsfile(target, ret=None, output=True):
    '''local dns configuration'''
    return _configure('hostsfile', target, ret, output)


def configure_network(target, ret=None, output=True):
    '''install marker grains'''
    return _configure('network', target, ret, output)


def configure_grains(target, ret=None, output=True):
    '''install marker grains'''
    return _configure('grains', target, ret, output)


def deploy(target, output=True, ret=None, hooks=True, pre=True, post=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    if ret is None:
        ret = result()
    ret['comment'] += green('Installing compute node configuration\n')
    if hooks and pre:
        run_vt_hook('pre_deploy_compute_node',
                    ret=ret, target=target, output=output)
    for step in [configure_sshkeys,
                 configure_grains,
                 install_vts,
                 configure_network,
                 configure_hostsfile,
                 configure_firewall,
                 configure_sslcerts,
                 configure_reverse_proxy]:
        step(target, ret=ret, output=False)
        check_point(ret, __opts__, output=output)
    if hooks and post:
        run_vt_hook('post_deploy_compute_node',
                    ret=ret, target=target, output=output)
    salt_output(ret, __opts__, output=output)
    return ret


def post_deploy(target, ret=None, output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    if ret is None:
        ret = result()
    hook = 'pre_post_deploy_compute_node'
    run_vt_hook(hook, ret=ret, target=target, output=output)
    for step in []:
        step(target, ret=ret, output=False)
        check_point(ret, __opts__, output=output)
    hook = 'post_post_deploy_compute_node'
    run_vt_hook(hook, ret=ret, target=target, output=output)
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


def provision_compute_nodes(skip=None, only=None,
                            no_compute_node_provision=False,
                            output=True,
                            refresh=False,
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
    if isinstance(only, basestring):
        only = only.split(',')
    if isinstance(skip, basestring):
        skip = skip.split(',')
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
        if no_compute_node_provision:
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
    salt_output(ret, __opts__, output=output)
    return ret


def post_provision_compute_nodes(skip=None, only=None,
                                 output=True, refresh=False, ret=None):
    '''post provision all compute nodes

    '''
    if isinstance(only, basestring):
        only = only.split(',')
    if isinstance(skip, basestring):
        skip = skip.split(',')
    if only is None:
        only = []
    if skip is None:
        skip = []
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
    salt_output(ret, __opts__, output=output)
    return ret


def orchestrate(skip=None,
                skip_vms=None,
                only=None,
                only_vms=None,
                no_compute_node_provision=False,
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
        no_compute_node_provision
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
    if refresh:
        cli('saltutil.refresh_pillar')
    if only is None:
        only = []
    if skip is None:
        skip = []
    if only_vms is None:
        only_vms = []
    if skip_vms is None:
        skip_vms = []
    if isinstance(only, basestring):
        only = only.split(',')
    if isinstance(skip, basestring):
        skip = skip.split(',')
    if isinstance(only_vms, basestring):
        only_vms = only_vms.split(',')
    if isinstance(skip_vms, basestring):
        skip_vms = skip_vms.split(',')
    if ret is None:
        ret = result()
    chg = ret['changes']
    lresult = True
    if not no_provision:
        provision_compute_nodes(
            skip=skip, only=only,
            no_compute_node_provision=no_compute_node_provision,
            output=False, refresh=refresh, ret=ret)
        for a in ret.setdefault('cns_in_error', []):
            if a not in skip:
                lresult = False
                skip.append(a)
        if not no_vms:
            for compute_node in chg.setdefault('cns_provisionned', []):
                __salt__['mc_cloud_vm.orchestrate'](
                    compute_node, output=False,
                    skip=skip_vms, only=only_vms,
                    refresh=refresh, ret=ret)
            vms_in_error = chg.setdefault('vms_in_error', {})
            for node in vms_in_error:
                for vm in vms_in_error[node]:
                    if vm not in skip_vms:
                        lresult = False
                        skip_vms.append(vm)

    if not no_post_provision:
        post_provision_compute_nodes(skip=skip, only=only,
                                     output=False, refresh=refresh, ret=ret)
        for a in chg.setdefault('postp_cns_in_error', []):
            if a not in skip:
                lresult = False
                skip.append(a)

        if not no_vms and not no_vms_post_provision:
            for compute_node in chg['cns_provisionned']:
                __salt__['mc_cloud_vm.post_provision_vms'](
                    compute_node, output=False,
                    skip=skip_vms, only=only_vms,
                    refresh=refresh, ret=ret)
            vms_in_error = chg.setdefault('postp_vms_in_errors', {})
            for node in vms_in_error:
                for vm in vms_in_error[node]:
                    if vm not in skip_vms:
                        skip_vms.append(vm)
                        lresult = False
    ret['result'] = lresult
    salt_output(ret, __opts__, output=output)
    return ret
#
