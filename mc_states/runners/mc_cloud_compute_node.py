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


def cn_sls_pillar(target, ttl=api.RUNNER_CACHE_TIME):
    '''limited cloud pillar to expose to a compute node
    This will be stored locally inside a local registry'''
    func_name = 'mc_cloud_compute_node.cn_sls_pillar {0}'.format(
        target)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))

    def _do(target):
        cloudSettings = cli('mc_cloud.settings')
        cloudSettingsData = {}
        imgSettingsData = {}
        cnSettingsData = {}
        cnSettingsData['cn'] = cli(
            'mc_cloud_compute_node.get_settings_for_target', target)
        vt_data = cnSettingsData['cn'].get('virt_types', {})
        vts = []
        for vt, enabled in vt_data.items():
            if enabled:
                vts.append(vt)
        cnSettingsData['rp'] = cli(
            'mc_cloud_compute_node.get_reverse_proxies_for_target', target)
        cloudSettingsData['all_sls_dir'] = cloudSettings['all_sls_dir']
        cloudSettingsData[
            'compute_node_sls_dir'] = cloudSettings['compute_node_sls_dir']
        cloudSettingsData['prefix'] = cloudSettings['prefix']
        cloudSettingsData = cloudSettingsData
        cnSettingsData = cnSettingsData
        vmSettings = {}
        imgSettings = cli('mc_cloud_images.settings')
        for name, imageData in imgSettings.get('kvm', {}).get('images', {}).items():
            imgSettingsData[name] = {
                'kvm_tarball': imageData['kvm_tarball'],
                'kvm_tarball_md5': imageData['kvm_tarball_md5'],
                'kvm_tarball_name': imageData['kvm_tarball_name'],
                'kvm_tarball_ver': imageData['kvm_tarball_ver']}
        pillar = {'cloudSettings': cloudSettingsData,
                  'vmSettings': vmSettings,
                  'imgSettings': imgSettingsData,
                  'cnSettings': cnSettingsData}
        # add to the compute node pillar all the VT specific pillars
        for vt in vts:
            cid = 'mc_cloud_{0}.cn_sls_pillar'.format(vt)
            vid = 'mc_cloud_{0}.vm_sls_pillar'.format(vt)
            for vm, vdata in  cnSettingsData['cn']['vms'].items():
                if vt == vdata.get('virt_type', ''):
                    vmSettings[vm] = __salt__[vid](target, vm)
            if cid in __salt__:
                pillar = dictupdate(pillar, __salt__[cid](target))
        # add to the compute node pillar all the VM pillars
        return pillar
    cache_key = 'mc_cloud_compute_node.cn_sls_pillar_{0}'.format(target)
    ret = memoize_cache(_do, [target], {}, cache_key, ttl)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


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
    func_name = 'mc_compute_node.run_vt_hook {0} {1}'.format(
        target, hook_name)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    ret = __salt__['mc_cloud_controller.run_vt_hook'](hook_name,
                                                      target=target,
                                                      ret=ret,
                                                      vts=vts,
                                                      output=output,
                                                      *args, **kwargs)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def upgrade_vts(target, ret=None, output=True):
    '''upgrade all virtual types to be ready to host vms'''
    func_name = 'mc_compute_node.install_vts {0}'.format(target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    ret = run_vt_hook('upgrade_vt',
                      ret=ret, target=target, output=output)
    if ret['result']:
        ret['comment'] += yellow(
            '{0} is now upgraded to host vms\n'.format(target))
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def install_vts(target, ret=None, output=True):
    '''install all virtual types to be ready to host vms'''
    func_name = 'mc_compute_node.install_vts {0}'.format(target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    ret = run_vt_hook('install_vt',
                      ret=ret, target=target, output=output)
    if ret['result']:
        ret['comment'] += yellow(
            '{0} is now ready to host vms\n'.format(target))
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def _configure(what, target, ret, output):
    __salt__['mc_cloud_compute_node.lazy_register_configuration'](target)
    func_name = 'mc_compute_node._configure {0} {1}'.format(what, target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    ret['comment'] += yellow('Installing {1} on {0}\n'.format(target, what))
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(_GPREF, what), **{
            'salt_target': target, 'ret': ret})
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def register_configuration(target, ret=None, output=True):
    '''
    drop the compute node configuration
    '''
    func_name = 'mc_compute_node.register_configuration {0}'.format(target)
    if ret is None:
        ret = result()
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    settings = __salt__['mc_cloud_compute_node.cn_sls_pillar'](target)
    cret = cli(
        'mc_macros.update_local_registry',
        'cloud_compute_node_settings', settings, registry_format='pack',
        salt_target=target)
    if (
        isinstance(cret, dict)
        and(
            'makina-states.local.'
            'cloud_compute_node_settings.cnSettings' in cret
        )
    ):
        ret['result'] = True
        ret['comment'] += yellow('Configuration stored'
                                 ' on {0}\n'.format(target))
    else:
        ret['result'] = False
        ret['comment'] += red('Configuration failed to store'
                              ' on {0}\n'.format(target))
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def lazy_register_configuration(cn, ttl=5*60, *args, **kwargs):
    '''
    Wrapper to register_configuration at the exception
    that only one shared call can de done in a five minutes row.

    This can be used as a decorator in orchestrations functions
    to ensure configuration has been dropped on target tenants.
    '''
    cache_key = ('mc_cloud_compute_node.lazy_'
                 'register_configuration_{0}').format(cn)

    def _do(cn, *args, **kwargs):
        return __salt__['mc_cloud_compute_node.register_configuration'](
            cn, *args, **kwargs)
    ret = memoize_cache(_do, [cn] + list(args), kwargs, cache_key, ttl)
    return ret


def register_configurations(only=None, only_vms=None,
                            skip=None, skip_vms=None,
                            refresh=False, ret=None, output=True):
    '''Parse all reachable compute nodes and vms
    and regenerate the local configuration registries concerning
    cloud deployment'''
    func_name = 'mc_compute_node.register_configurations'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    only, _, skip, __ = (
        __salt__['mc_cloud_controller.gather_only_skip'](
            only=only, skip=skip))
    if ret is None:
        ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    settings = cli('mc_cloud_compute_node.settings')
    configuration = ret['changes'].setdefault('cns_configured', [])
    configuration_error = ret['changes'].setdefault('cns_in_error', [])
    targets = [a for a in settings['targets']]
    # targets += ['foo', 'bar']
    targets = filter_compute_nodes(targets, skip, only)
    hosts_to_configure_vms = []
    for idx, compute_node in enumerate(targets):
        cret = result()
        try:
            if not cli('test.ping', salt_target=compute_node):
                raise FailedStepError('not reachable')
            register_configuration(compute_node, ret=cret, output=False)
            check_point(cret, __opts__, output=output)
            if compute_node not in hosts_to_configure_vms:
                hosts_to_configure_vms.append(compute_node)
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
            if compute_node not in configuration:
                configuration.append(compute_node)
            # if everything is well, wipe the unseful output
            cret['output'] = ''
            cret['trace'] = ''
        else:
            ret['result'] = False
            if compute_node not in configuration_error:
                configuration_error.append(compute_node)
        cret.pop('result', False)
        merge_results(ret, cret)
    if len(configuration_error):
        ret['comment'] += red('There were errors while configuring '
                              'computes nodes {0}\n'.format(
                                  configuration_error))
    else:
        if ret['result']:
            ret['trace'] = ''
            ret['comment'] += green('All computes nodes were preconfigured\n')
    # now for each reachable vm, also preconfigure it
    for idx, compute_node in enumerate(hosts_to_configure_vms):
        cret = result()
        try:
            __salt__['mc_cloud_vm.register_configurations'](
                compute_node, skip=skip_vms, only=only_vms,
                ret=cret, output=False)
            check_point(cret, __opts__, output=output)
        except FailedStepError:
            cret['result'] = False
        except Exception, exc:
            trace = traceback.format_exc()
            cret = {'result': False,
                    'output': (
                        'unknown error on '
                        'configuring vms {0}\n{1}'
                    ).format(compute_node),
                    'comment': (
                        'unknown error on configuring vms'
                        '{0}\n'
                    ).format(compute_node),
                    'trace': trace}
        if cret['result']:
            if compute_node not in configuration:
                configuration.append(compute_node)
            # if everything is well, wipe the unseful output
            cret['output'] = ''
            cret['trace'] = ''
        else:
            ret['result'] = False
            if compute_node not in configuration_error:
                configuration_error.append(compute_node)
        cret.pop('result', False)
        merge_results(ret, cret)
    if len(configuration_error):
        ret['comment'] += red('There were errors while configuring '
                              'computes nodes vms {0}\n'.format(
                                  configuration_error))
    else:
        if ret['result']:
            ret['trace'] = ''
            ret['comment'] += green('All computes nodes vms '
                                    'were preconfigured\n')
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def configure_sshkeys(target, ret=None, output=True):
    '''drop the compute node ssh key'''
    return _configure('sshkeys', target, ret, output)


def configure_sslcerts(target, ret=None, output=True):
    '''deploy SSL certificates on compute node'''
    return _configure('sslcerts', target, ret, output)


def configure_host(target, ret=None, output=True):
    '''shorewall configuration'''
    return _configure('host', target, ret, output)


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
    '''install network configuration'''
    return _configure('network', target, ret, output)


def configure_prevt(target, ret=None, output=True):
    '''install all prevt steps'''
    return _configure('prevt', target, ret, output)


def configure_grains(target, ret=None, output=True):
    '''install marker grains'''
    return _configure('grains', target, ret, output)


def deploy(target, output=True, ret=None, hooks=True, pre=True, post=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    __salt__['mc_cloud_compute_node.lazy_register_configuration'](target)
    func_name = 'mc_compute_node.deploy {0}'.format(target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    if ret is None:
        ret = result()
    ret['comment'] += green('Installing compute node configuration\n')
    if hooks and pre:
        run_vt_hook('pre_deploy_compute_node',
                    ret=ret, target=target, output=output)
        for step in [
            register_configuration,
            configure_prevt,
            # merged in configure_prevt for perf reason
            # configure_sshkeys,
            # configure_grains,
            install_vts,
            configure_network,
            configure_host,
            # merged in configure_host for perf reason
            # configure_hostsfile,
            # configure_firewall,
            # configure_sslcerts,
            # configure_reverse_proxy
        ]:
            step(target, ret=ret, output=False)
            check_point(ret, __opts__, output=output)
    if hooks and post:
        run_vt_hook('post_deploy_compute_node',
                    ret=ret, target=target, output=output)
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def post_deploy(target, ret=None, output=True):
    '''Prepare cloud controller configuration
    can also apply per virtualization type configuration'''
    func_name = 'mc_compute_node.post_deploy {0}'.format(target)
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def filter_compute_nodes(nodes, skip, only):
    '''filter compute nodes to run on'''
    func_name = 'mc_compute_node.filter_compute_nodes'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return targets


def provision_compute_nodes(skip=None, only=None,
                            no_compute_node_provision=False,
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
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
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
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def post_provision_compute_nodes(skip=None, only=None,
                                 output=True, refresh=False, ret=None):
    '''post provision all compute nodes

    '''
    func_name = 'mc_compute_node.post_provision_compute_nodes'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
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
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
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
    func_name = 'mc_compute_node.orchestrate'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
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
            no_compute_node_provision=no_compute_node_provision,
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
    salt_output(ret, __opts__, output=output)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret


def report(targets, ret=None, refresh=False, output=True):
    '''Parse all reachable compute nodes and vms
    and regenerate the local configuration registries concerning
    cloud deployment'''
    func_name = 'mc_compute_node.register_configurations'
    __salt__['mc_api.time_log']('start {0}'.format(func_name))
    settings = cli('mc_cloud_compute_node.settings')
    if ret is None:
        ret = result()
    if refresh:
        cli('saltutil.refresh_pillar')
    sret = ''
    if not isinstance(targets, list):
        targets = targets.split(',')
    for target in targets:
        # if compute_node
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
    salt_output(ret, __opts__, output=output, onlyret=True)
    __salt__['mc_api.time_log']('end {0}'.format(func_name))
    return ret



#
