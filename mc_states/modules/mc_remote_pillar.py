#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''

.. _module_mc_remote_pillar:

mc_remote_pillar / masterless pillar management
===============================================


The idea is to have masterless managed tenants, where the pillar is
remotely generated on a central box and replicated onto final destinations
via ssh+rsync.


From this central box:

    - We autodiscover the ids of the boxes to manage by calling
      all discovered ``*.get_masterless_makinastates_hosts`` functions
      and execute them. Those functions should return minions ids to act
      on. Remember not to rely on pillar, as the pillar may not
      be fully populated here !
    - From then, we execute in parrallel for each host:

      - We locally generate all pillars and dump them to a file
      - We then replicate the pillars to all the online boxes

        - We may rollback the previous pillar in case of errors


To customize the pillar configuration, you can

    - add static pillar
    - add an ext_pillar that generates pillar entries depending on
      the minion id

But you won't have access to remote box grains as we won't use either
classical MQ salt or salt+ssh, so don't use pillar grains matching !

'''

import os
import sys
import copy
import time
import logging
import Queue
import multiprocessing
import threading
import traceback

import salt.utils.minions
import salt.config as config
from salt.utils.odict import OrderedDict

import mc_states.api
from mc_states import saltcaller
from mc_states import saltapi


six = mc_states.api.six

log = logging.getLogger(__name__)
__name = 'mc_remote_pillar'



class AnsibleInventoryIncomplete(ValueError):
    '''.'''


def get_hosts(ids_=None):
    data = OrderedDict()
    if isinstance(ids_, basestring):
        ids_ = ids_.split(',')
    for f in __salt__:
        if f.endswith('.get_masterless_makinastates_hosts'):
            data.update(__salt__[f]())
    if ids_:
        for i in [a for a in data]:
            if i not in ids_:
                data.pop(i, None)
    return data


def get_host(host):
    return get_hosts(host).get(host, None)


def get_pillar(minion='*', skipped=None, saltenv='base', **kwargs):
    '''
    Returns the compiled pillar either of a specific minion
    or just the global available pillars. This function assumes
    that no minion has the id ``*``.
    '''
    try:
        fic = __opts__['config_dir'] + '/master'
        os.stat(fic)  # may raise OSError
        mopts = config.master_config(fic)
    except (KeyError, OSError):
        # may not have master config in masterless setups
        mopts = copy.deepcopy(__opts__)
    id_, grains, _ = salt.utils.minions.get_minion_data(minion, mopts)
    if not grains:
        grains = {}
    grains = copy.deepcopy(grains)
    did = {'fqdn': minion, 'id': minion}
    for d in [grains, mopts]:
        d.update(did)
    pillar = salt.pillar.Pillar(mopts, grains, id_, saltenv)
    if not skipped:
        skipped = ['master']
    compiled_pillar = pillar.compile_pillar()
    for k in skipped:
        compiled_pillar.pop(k, None)
    return compiled_pillar


def get_generate_hooks():
    hooks = []
    _s = __salt__
    for func in _s:
        if func.endswith('load_makinastates_masterless_pillar'):
            hooks.append(func)
    return _s['mc_utils.uniquify'](hooks)


def generate_masterless_pillar(id_, set_retcode=False, dump=False):
    _s = __salt__
    pid = None
    errors = []
    try:
        pillar = get_pillar(id_)
    except Exception:
        pillar = {}
        error = traceback.format_exc()
        errors.append(error)
        log.error('MASTERLESS PILLAR FOR {0} failed'
                  ' to render'.format(id_))
        log.error(error)
    if isinstance(pillar.get('_errors', None), list):
        errors.extend(pillar['_errors'])
    if dump and not errors:
        target_dir = os.path.join(
            os.path.dirname(__opts__['config_dir']), 'masterless_pillars')
        client_dir = os.path.join(target_dir, id_)
        pclient_dir = os.path.join(client_dir, 'pillar')
        if not os.path.isdir(pclient_dir):
            os.makedirs(pclient_dir)
        pfi = 'makinastates-masterless.sls'
        pid = os.path.join(client_dir, pclient_dir, pfi)
        with open(os.path.join(pid), 'w') as fic:
            log.info('Writing pillar {0}'.format(pid))
            fic.write(_s['mc_dumper.yaml_dump'](pillar))
    return {'id': id_, 'pillar': pillar, 'errors': errors, 'pid': pid}


def handle_result(results, item):
    # the salt payload may not be full if something low level
    # is not in place
    results[item['salt_args'][0]] = item
    return results


def wait_processes_pool(workers, output_queue, results=None):
    if results is None:
        results = {}
    msgs = []
    while len(workers):
        try:
            item = output_queue.get(False, 0.1)
            if item is not None:
                id_ = item[0]
                th = workers.pop(id_, None)
                th.join(1)
                th.terminate()
                handle_result(results, item)
        except Queue.Empty:
            msg = ('Waiting for pillars pool(process) to finish {0}'
                   ''.format(' '.join([a for a in workers])))
            if msg not in msgs:
                log.info(msg)
                msgs.append(msg)
        for id_ in [a for a in workers]:
            th = workers[id_]
            if not th.is_alive():
                th.join(1)
                th.terminate()
                workers.pop(id_, None)
        time.sleep(0.1)
    return results


def wait_pool(workers, output_queue, results=None):
    if results is None:
        results = {}
    msgs = []
    while len(workers):
        try:
            item = output_queue.get(False, 0.1)
            if item is not None:
                id_ = item[0]
                th = workers.pop(id_, None)
                if th.is_alive() and th.ident:
                    th.join(0.1)
                handle_result(results, item)
        except Queue.Empty:
            msg = ('Waiting for pillars pool(thread) to finish {0}'
                   ''.format(' '.join([a for a in workers])))
            if msg not in msgs:
                log.info(msg)
                msgs.append(msg)
        for id_ in [a for a in workers]:
            th = workers[id_]
            if not th.is_alive():
                th.join(0.1)
                workers.pop(id_, None)
    return results


def generate_masterless_pillars(ids_=None,
                                skip=None,
                                processes=4,
                                executable=None,
                                threads=None,
                                debug=False,
                                local=None,
                                timeout=None,
                                loglevel=None,
                                config_dir=None,
                                env=None,
                                *args,
                                **kwargs):
    _s = __salt__
    _o = __opts__
    locs = _s['mc_locations.settings']()
    if not executable:
        executable = os.path.join(locs['msr'], 'bin/salt-call')
    if not config_dir:
        config_dir = _o['config_dir']
    if not loglevel:
        loglevel = _o['log_level']
    if local is None:
        local = _o['file_client'] == 'local'
    ids_ = get_hosts(ids_)
    if isinstance(ids_, six.string_types):
        ids_ = ids_.split(',')
    if not threads:
        threads = 0
    if not skip:
        skip = []
    if not env:
        env = {}
    env = _s['mc_utils.dictupdate'](copy.deepcopy(dict(os.environ)), env)
    input_queue = Queue.Queue()
    output_queue = Queue.Queue()
    threads = int(threads)
    for ix, id_ in enumerate(ids_):
        if id_ in skip:
            log.info('Skipping pillar generation for {0}'.format(id_))
            continue
        input_queue.put(id_)
        # for debug
        # if ix >= 2:
        #     break
    workers = {}
    results = {}
    try:
        while not input_queue.empty():
            id_ = input_queue.get()
            fargs = [id_, 'set_retcode=True']
            pargs = {'executable': executable,
                     'func': 'mc_remote_pillar.generate_masterless_pillar',
                     'args': fargs,
                     'out': 'json',
                     'timeout': timeout,
                     'no_display_ret': True,
                     'local': local,
                     'config_dir': config_dir,
                     'loglevel': loglevel}
            log.info('Getting pillar through saltcaller.call'
                     ' for {0}'.format(id_))
            log.debug('Arguments: {0}'.format(pargs))
            pargs.update({'env': env,
                          'output_queue': output_queue})
            if threads:
                if len(workers) >= threads:
                    wait_pool(workers, results)
                workers[id_] = (
                    threading.Thread(
                        target=saltcaller.call, kwargs=pargs))
                workers[id_].start()
            elif processes:
                if len(workers) >= processes:
                    wait_processes_pool(workers, output_queue, results)
                workers[id_] = (
                    multiprocessing.Process(
                        target=saltcaller.call, kwargs=pargs))
                workers[id_].start()
            else:
                saltcaller.call(**pargs)
                while not output_queue.empty():
                    item = output_queue.get()
                    handle_result(results, item)
        if threads:
            wait_pool(workers, results)
        elif processes:
            wait_processes_pool(workers, output_queue, results)
    except (KeyboardInterrupt, Exception):
        if threads:
            for id_ in [a for a in workers]:
                th = workers.pop(id_, None)
                if th.is_alive() and th.ident:
                    th.join(0.01)
        elif processes:
            for id_ in [a for a in workers]:
                th = workers.pop(id_, None)
                if th.is_alive() and th.ident:
                    th.terminate()
        raise
    return results


def generate_ansible_roster(ids_=None, **kwargs):
    hosts = {}
    masterless_hosts = generate_masterless_pillars(
        ids_=ids_, **kwargs)
    for i, idata in six.iteritems(masterless_hosts):
        pillar = idata.get('salt_out', {}).get('pillar', {})
        if '_errors' in pillar:
            raise AnsibleInventoryIncomplete(
                'Pillar for {0} has errors\n{1}'.format(
                    i,
                    '\n'.join(pillar['_errors'])
                )
            )
        oinfos = pillar.get(saltapi.SSH_CON_PREFIX, {})
        hosts[i] = {
            'name': i,
            'host': i,
            'port': 22,
            'gateway': None,
            'salt_pillar': pillar}
        hosts[i].update(oinfos)
    return hosts
# vim:set et sts=4 ts=4 tw=80:
