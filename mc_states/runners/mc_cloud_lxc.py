#!/usr/bin/env python
'''

.. _runner_mc_cloud_lxc:

mc_cloud_lxc runner
==========================

'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# Import python libs
import os
import logging
from pprint import pformat
import traceback

# Import salt libs
import salt.client
import salt.payload
import salt.utils
import salt.output
import salt.minion
from salt.utils import check_state_result
from salt.utils.odict import OrderedDict

from mc_states import api
from mc_states.saltapi import (
    merge_results,
    result,
    salt_output,
    check_point,
    SaltExit,
    green, red, yellow,
    SaltCopyError,
    FailedStepError,
    MessageError,
)

log = logging.getLogger(__name__)


def cli(*args, **kwargs):
    return __salt__['mc_api.cli'](*args, **kwargs)


def cn_sls_pillar(target):
    '''limited cloud pillar to expose to a compute node'''
    pillar = __salt__['mc_cloud_compute_node.cn_sls_pillar'](target)
    imgSettings = cli('mc_cloud_images.settings')
    lxcSettings = cli('mc_cloud_lxc.settings')
    imgSettingsData = {}
    lxcSettingsData = {}
    for name, imageData in imgSettings['lxc']['images'].items():
        imgSettingsData[name] = {
            'lxc_tarball': imageData['lxc_tarball'],
            'lxc_tarball_md5': imageData['lxc_tarball_md5'],
            'lxc_tarball_name': imageData['lxc_tarball_name'],
            'lxc_tarball_ver': imageData['lxc_tarball_ver']}
    for v in ['use_bridge', 'bridge',
              'gateway', 'netmask_full',
              'network', 'netmask']:
        lxcSettingsData[v] = lxcSettings['defaults'][v]
    imgSettingsData = api.json_dump(imgSettingsData)
    lxcSettingsData = api.json_dump(lxcSettingsData)
    pillar.update(
        {'slxcSettings': lxcSettingsData,
         'simgSettings': imgSettingsData})
    return pillar


def vm_sls_pillar(compute_node, vm):
    '''limited cloud pillar to expose to a vm'''
    pillar = __salt__['mc_cloud_vm.vm_sls_pillar'](compute_node, vm)
    lxcVmData = cli('mc_cloud_lxc.get_settings_for_vm',
                    compute_node, vm, full=False)
    lxcVmData = api.json_dump(lxcVmData)
    pillar['slxcVmData'] = lxcVmData
    return pillar


def post_deploy_controller(output=True):
    '''Prepare cloud controller LXC configuration'''
    ret = result()
    ret['comment'] = yellow('Installing controller lxc configuration\n')
    pref = 'makina-states.cloud.lxc.controller'
    ret = __salt__['mc_api.apply_sls'](
        ['{0}.layout'.format(pref), '{0}.crons'.format(pref)],
        **{'ret': ret})
    salt_output(ret, __opts__, output=output)
    return ret


def _cn_configure(what, target, ret, output):
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'LXC: Installing {1} on compute node {0}\n'.format(target, what))
    pref = 'makina-states.cloud.lxc.compute_node'
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(pref, what), **{
            'salt_target': target,
            'ret': ret,
            'sls_kw': {'pillar': cn_sls_pillar(target)}})
    salt_output(ret, __opts__, output=output)
    return ret


def configure_grains(target, ret=None, output=True):
    '''install compute node grain markers'''
    return _cn_configure('grains', target, ret, output)


def configure_install_lxc(target, ret=None, output=True):
    '''install lxc'''
    return _cn_configure('install_lxc', target, ret, output)


def configure_images(target, ret=None, output=True):
    '''configure all images templates'''
    return _cn_configure('images', target, ret, output)


def install_vt(target, output=True):
    '''install & configure lxc'''
    ret = result()
    ret['comment'] += yellow('Installing lxc on {0}\n'.format(target))
    for step in [configure_grains,
                 configure_install_lxc,
                 configure_images]:
        try:
            step(target, ret=ret, output=False)
        except FailedStepError:
            pass
    iret = __salt__['mc_lxc.sync_images'](only=[target])
    if iret['result']:
        ret['comment'] += yellow(
            'LXC: images synchronnised on {0}\n'.format(target))
    else:
        merge_results(ret, iret)
        ret['comment'] += yellow(
            'LXC: images failed to synchronnise on {0}\n'.format(target))
    salt_output(ret, __opts__, output=output)
    return ret


def post_post_deploy_compute_node(target, output=True):
    '''post deployment hook for controller'''
    ret = result()
    nodetypes_reg = cli('mc_nodetypes.registry')
    slss, pref = [], 'makina-states.cloud.lxc.compute_node'
    if nodetypes_reg['is']['devhost']:
        slss.append('{0}.devhost'.format(pref))
    if slss:
        ret =  __salt__['mc_api.apply_sls'](
            slss, **{'salt_target': target,
                     'ret': ret,
                     'sls_kw': {'pillar': cn_sls_pillar(target)}})
    msg = 'Post installation: {0}\n'
    if ret['result']:
        clr = green
        status = 'sucess'
    else:
        clr = red
        status = 'failure'
    ret['comment'] += clr(msg.format(status))
    salt_output(ret, __opts__, output=output)
    return ret


def _vm_configure(what, target, compute_node, vm, ret, output):
    if ret is None:
        ret = result()
    ret['comment'] += yellow(
        'LXC: Installing {2} on vm '
        '{0}/{1}\n'.format(compute_node, vm, what))
    pref = 'makina-states.cloud.lxc.vm'
    ret =  __salt__['mc_api.apply_sls'](
        '{0}.{1}'.format(pref, what), **{
            'salt_target': target,
            'ret': ret,
            'sls_kw': {'pillar': vm_sls_pillar(compute_node, vm)}})
    salt_output(ret, __opts__, output=output)
    return ret


def vm_spawn(vm, compute_node=None, vt='lxc', ret=None, output=True):
    '''spawn the vm

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_spawn foo.domain.tld

    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('spawn', None, compute_node, vm, ret, output)


def vm_grains(vm, compute_node=None, vt='lxc', ret=None, output=True):
    '''install marker grains

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_grains foo.domain.tld

    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('grains', vm, compute_node, vm, ret, output)


def vm_initial_setup(vm, compute_node=None, vt='lxc', ret=None, output=True):
    '''set initial password at least

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_initial_setup foo.domain.tld


    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('initial_setup', vm, compute_node, vm, ret, output)


def vm_hostsfile(vm, compute_node=None, vt='lxc', ret=None, output=True):
    '''manage vm /etc/hosts to add link to host

    ::

        mastersalt-run -lall mc_cloud_lxc.vm_hostsfile foo.domain.tld

    '''
    compute_node = __salt__['mc_cloud_vm.get_compute_node'](vm, compute_node)
    return _vm_configure('hostsfile', vm, compute_node, vm, ret, output)

# vim:set et sts=4 ts=4 tw=80:
