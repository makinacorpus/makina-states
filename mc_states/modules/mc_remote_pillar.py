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


six = mc_states.api.six

log = logging.getLogger(__name__)
__name = 'mc_remote_pillar'


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
        mopts = config.master_config(__opts__['config_dir']+'/master')
    except Exception:
        # may not have master config in masterless setups
        mopts = copy.deepcopy(__opts__)
    id_, grains, _ = salt.utils.minions.get_minion_data(minion, mopts)
    if not grains:
        grains = {}
    grains = copy.deepcopy(grains)
    grains = {}
    did = {'fqdn': minion, 'id': minion}
    grains.update(did)
    mopts.update(did)
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


def generate_masterless_pillar(id_,
                               fileid='makinastates-masterless.sls',
                               match='*',
                               errors=None,
                               dump=True):
    _s = __salt__
    pillars = {}
    pid = None
    if errors is None:
        errors = []
    try:
        data = get_pillar(id_)
        pillar = pillars.setdefault((fileid, match), OrderedDict())
        pillars[(fileid, match)] = _s['mc_utils.dictupdate'](pillar, data)
    except Exception:
        trace = traceback.format_exc()
        errors.append(trace)
        log.error('MASTERLESS PILLAR FOR {0} failed'
                  ' to render'.format(id_))
        log.error(trace)
    if dump:
        target_dir = os.path.join(
            __opts__['pillar_roots']['base'][0], 'masterless_pillars')
        client_dir = os.path.join(target_dir, id_)
        pclient_dir = os.path.join(client_dir, 'pillar')
        if not os.path.isdir(pclient_dir):
            os.makedirs(pclient_dir)
        for pfi, fdata in pillars.items():
            fid, target = pfi
            pid = os.path.join(client_dir, pclient_dir, fid)
            with open(os.path.join(pid), 'w') as fic:
                log.info('Writing pillar {0}'.format(pid))
                fic.write(_s['mc_dumper.yaml_dump'](fdata))
    return pillars, errors, pid


def is_online_for_pillar_transfer(id_):
    status = True
    log.error('implement is_online_for_pillar_transfer')
    return status


def backup_remote_masterless_pillar(id_):
    log.error('implement backup_remote_masterless_pillar')


def sync_masterless_pillar(id_):
    log.error('implement sync_masterless_pillar')


def remote_wire_masterless_pillar(id_):
    log.error('implement remote_wire_masterless_pillar')


def get_remote_masterless_pillar(id_):
    log.error('implement get_remote_masterless_pillar')
    return get_pillar(id_)


def restore_remote_masterless_pillar(id_):
    log.error('implement restore_remote_masterless_pillar')


def generate_ssh_config(id_):
    log.error('implement restore_remote_masterless_pillar')


def synchronize_remote_pillar(id_):
    if not is_online_for_pillar_transfer(id_):
        raise Exception(
            '{0} is not online, skipping synchronization'
            ''.format(id_))
    ret = None
    backup_remote_masterless_pillar(id_)
    sync_masterless_pillar(id_)
    remote_wire_masterless_pillar(id_)
    try:
        ret = get_remote_masterless_pillar(id_)
    except Exception:
        restore_remote_masterless_pillar(id_)
        raise
    return ret


def generate_local_files(id_):
    generate_masterless_pillar(id_)
    generate_ssh_config(id_)


def replicate_masterless_pillar(id_, sync=None):
    # XXX: implement per-id local pillar locking
    # for two executions to lock themselves up
    # until one finishes
    # no need for lock as we write on a separate directory
    # for each minion
    if sync is None:
        sync = True
    lock = None
    try:
        if lock:
            lock.acquire()
        try:
            data = {}
            generate_local_files(id_)
            if sync:
                synchronize_remote_pillar(id_)
            ret = (id_, 'success', data)
        finally:
            if lock:
                lock.release()
    except Exception:
        trace = traceback.format_exc()
        ret = (id_, 'error', trace)
    return ret


def handle_result(results, item):
    # the salt payload may not be full if something low leve
    # is not in place
    if not item['salt_out']:
        if item['retcode'] == saltcaller.TIMEOUT_RETCODE:
            err = saltcaller.format_output_and_error(item)
        else:
            err = saltcaller.format_output(item)
        item = (item['salt_args'][0], 'error', err)
    results.append(item)
    return results


def wait_processes_pool(workers, output_queue, results=None):
    if results is None:
        results = []
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
        results = []
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



def generate_ansible_roster(ids_=None):
    hosts = {}
    for i, idata in six.iteritems(get_hosts(ids_)):
        hosts[i] = {
            'name': '',
            'host': '',
            'port': '',
            'gateway': '',
        }
    return hosts


def replicate_masterless_pillars(ids_=None,
                                 skip=None,
                                 processes=4,
                                 threads=None,
                                 debug=False,
                                 local=None,
                                 timeout=None,
                                 loglevel=None,
                                 config_dir=None,
                                 env=None,
                                 sync=None,
                                 *args,
                                 **kwargs):
    _s = __salt__
    _o = __opts__
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
    input_queue = Queue.Queue()
    output_queue = Queue.Queue()
    threads = int(threads)
    for ix, id_ in enumerate(ids_):
        if id_ in skip:
            log.info('Skipping pillar generation for {0}'.format(id_))
            continue
        input_queue.put(id_)
        if ix >= 2:
            break
    workers = {}
    results = []
    executable = None
    if config_dir and ('mastersalt' in config_dir):
        executable = 'mastersalt-call'
    try:
        fargs = [id_]
        if sync is not None:
            fargs.append('sync={0}'.format(sync))
        pargs = {'executable': executable,
                 'func': 'mc_remote_pillar.replicate_masterless_pillar',
                 'args': fargs,
                 'env': env,
                 'out': 'json',
                 'timeout': timeout,
                 'local': local,
                 'config_dir': config_dir,
                 'loglevel': loglevel,
                 'output_queue': output_queue}
        while not input_queue.empty():
            id_ = input_queue.get()
            log.info('Handling pillar for {0}'.format(id_))
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
# vim:set et sts=4 ts=4 tw=80:
