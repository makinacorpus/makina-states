# -*- coding: utf-8 -*-
'''
.. _module_mc_salt:

mc_salt / salt related helpers
================================



'''
# Import salt libs
import mc_states.api
import random
import copy
import os
import logging
from mc_states.grains import makina_grains


__name = 'salt'

J = os.path.join
loglevelfmt = (
    "'%(asctime)s,%(msecs)03.0f "
    "[%(name)-17s][%(levelname)-8s] %(message)s'")
log = logging.getLogger(__name__)


def get_local_param(param):
    param = makina_grains._get_msconf(param, _o=__opts__)
    return param


def get_ms_url():
    val = get_local_param('ms_url')
    if not val:
        val = 'https://github.com/makinacorpus/makina-states.git'
    return val


def get_salt_url():
    val = get_local_param('salt_url')
    if not val:
        val = 'https://github.com/makinacorpus/salt.git'
    return val


def get_ansible_url():
    val = get_local_param('ansible_url')
    if not val:
        val = 'https://github.com/makinacorpus/ansible.git'
    return val


def get_salt_branch():
    val = get_local_param('salt_branch')
    if not val:
        val = '2015.8'
    return val


def get_ansible_branch():
    val = get_local_param('ansible_branch')
    if not val:
        val = 'stable-2.0.0.1'
    return val


def settings():
    '''Registry of settings decriving salt installation

    Please read the code to be sure to understand it before changing parameters
    as it can brick your installation.
    That's why most of this stuff will be underdocumented at first sight.
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        _o = __opts__
        local_conf = _s['mc_macros.get_local_registry'](
            'salt', registry_format='pack')
        locs = _s['mc_locations.settings']()
        crons = True
        env = _s['mc_env.settings']()['env']
        if (
            _s['mc_nodetypes.is_devhost']() or
            env in ['dev']
        ):
            crons = False
        tcrond = random.randint(2, 5)
        tcron = random.randint(0, 9)
        tcron2 = tcron + 5
        if tcron2 >= 10:
            tcron2 -= 10
        tcron3 = tcron2 + 3
        if tcron3 >= 10:
            tcron3 -= 10
        cron_minion_checkalive = '{0}{1} 0,6,12,20 * * *'.format(tcrond, tcron)
        cron_sync_minute = '0{0},1{0},2{0},3{0},4{0},5{0}'.format(tcron2)
        cron_minion_checkalive = local_conf.setdefault(
            'cron_minion_checkalive', cron_minion_checkalive)
        cron_sync_minute = local_conf.setdefault('cron_sync_minute',
                                                 cron_sync_minute)
        tcrond = local_conf.setdefault('tcrond', tcrond)
        tcron = local_conf.setdefault('tcron', tcron)
        tcron2 = local_conf.setdefault('tcron_2', tcron2)
        tcron3 = local_conf.setdefault('tcron_3', tcron3)
        # factorisation with bootsalt.sh
        data = {
            'id': _s['config.option'](
                'makina-states.minion_id',
                _s['config.option']('id', None)),
            'cron_auto_sync': crons,
            'cron_sync_minute': cron_sync_minute,
            'cron_sync_hour': '*',
            'cron_master_restart_minute': 0,
            'cron_master_restart_hour': 0,
            'cron_minion_restart_minute': 3,
            'cron_minion_restart_hour': 0,
            'rotate': _s['mc_logrotate.settings']()['days'],
            'log_prefix': '{msr}/var/log',
            'name': 'salt',
            'pillar_root': '{prefix}/pillar'}
        for k in _o:
            if k not in data:
                data[k] = copy.deepcopy(_o[k])
        #  default daemon overrides
        data = _s['mc_utils.defaults'](
            'makina-states.controllers.salt', data)
        # retrocompat access
        for i in {
            'venv_path',
            'msr',
            'salt_root',
            'pillar_root',
            'makina_states',
            'venv',
            'prefix',
        }:
            data[i] = locs[i]
        data = _s['mc_utils.format_resolve'](data)
        return data
    return _settings()
# vim:set et sts=4 ts=4 tw=80:
