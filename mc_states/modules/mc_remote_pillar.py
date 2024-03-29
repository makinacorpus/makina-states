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

import pstats
import cProfile
import datetime
import os
import sys
import copy
import time
import logging
try:
    import queue
except ImportError:
    import Queue as queue
from multiprocessing import Queue as mQueue
import multiprocessing
import threading
import traceback
import salt.loader

import salt.utils.minions
import salt.config as config

import mc_states.api
from mc_states import saltcaller
from mc_states import saltapi


Queue = queue
six = mc_states.api.six

log = logging.getLogger(__name__)
__name = 'mc_remote_pillar'
_marker = object()


class AnsibleInventoryIncomplete(ValueError):
    '''.'''


def get_hosts(ids_=None):
    data = set()
    if isinstance(ids_, six.string_types):
        ids_ = ids_.split(',')
    for f in __salt__:
        if f.endswith('.get_masterless_makinastates_hosts'):
            [data.add(a) for a in __salt__[f]()]
    data = list(data)
    if ids_:
        for i in data[:]:
            if i not in ids_:
                data.pop(data.index(i))
    return data


def get_host(host):
    return get_hosts(host).get(host, None)


def get_pillar(minion='*', skipped=None, saltenv='base', **kwargs):
    '''
    Returns the compiled pillar either of a specific minion
    or just the global available pillars. This function assumes
    that no minion has the id ``*``.
    '''
    _o = __opts__
    try:
        fic = _o['config_dir'] + '/master'
        os.stat(fic)  # may raise OSError
        mopts = config.master_config(fic)
    except (KeyError, OSError):
        # may not have master config in masterless setups
        mopts = copy.deepcopy(_o)
    id_, grains, _ = salt.utils.minions.get_minion_data(minion, mopts)
    if not grains:
        grains = {}
    grains = copy.deepcopy(grains)
    did = {'fqdn': minion, 'id': minion}
    # for d in [grains, mopts]:
    for d in [grains]:
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


def get_groups_pillar(host, pillar=None):
    if pillar is None:
        pillar = __salt__['mc_remote_pillar.get_pillar'](host)
    return pillar


def get_groups(host, pillar=None, groups=None):
    _s = __salt__
    if pillar is None:
        pillar = get_pillar(host)
    if groups is None:
        groups = {}
    data = set()
    for f in _s:
        if f.endswith('.get_masterless_makinastates_groups'):
            data.add(f)
    for i in data:
        res = _s[i](host, pillar)
        if res:
            if isinstance(res, dict):
                _s['mc_utils.dictupdate'](groups, res)
            else:
                [groups.setdefault(g, {}) for g in res]
    return groups


def generate_masterless_pillar(id_,
                               set_retcode=False,
                               profile_enabled=False,
                               reset_local_cache=True,
                               restart_memcached=True):
    _s = __salt__
    if profile_enabled:
        if reset_local_cache:
            _s['mc_pillar.invalidate_mc_pillar']()
        if restart_memcached:
            _s['cmd.run']('service memcached restart')
            time.sleep(2)
    pid = None
    errors = []
    if profile_enabled:
        pr = cProfile.Profile()
        pr.enable()
    try:
        pillar = get_pillar(id_)
    except Exception:
        pillar = {}
        error = traceback.format_exc()
        errors.append(error)
        log.error('MASTERLESS PILLAR FOR {0} failed'
                  ' to render'.format(id_))
        log.error(error)
    pillar['ansible_groups'] = get_groups(id_, pillar)
    if isinstance(pillar.get('_errors', None), list):
        errors.extend(pillar['_errors'])
    result = {'id': id_, 'pillar': pillar, 'errors': errors, 'pid': pid}
    if profile_enabled:
        pr.disable()
        if not os.path.isdir('/tmp/stats'):
            os.makedirs('/tmp/stats')
        date = datetime.datetime.now().isoformat()
        ficp = '/tmp/stats/{0}.{1}.pstats'.format(id_, date)
        fico = '/tmp/stats/{0}.{1}.dot'.format(id_, date)
        ficn = '/tmp/stats/{0}.{1}.stats'.format(id_, date)
        if not os.path.exists(ficp):
            pr.dump_stats(ficp)
            with open(ficn, 'w') as fic:
                pstats.Stats(pr, stream=fic).sort_stats('cumulative')
        msr = _s['mc_locations.msr']()
        _s['cmd.run'](
            '{2}/venv/bin/pyprof2calltree '
            '-i "{0}" -o "{1}"'.format(ficp, fico, msr), python_shell=True)
    return result


def handle_result(results, item):
    # the salt payload may not be full if something low level
    # is not in place
    results[item['salt_args'][0]] = item
    return results


def push_queue_to_results(output_queue, results):
    try:
        item = output_queue.get(False, 0.1)
        if item is not None:
            handle_result(results, item)
    except Queue.Empty:
        item = None
    return item


def wait_processes_pool(workers, output_queue, results):
    if results is None:
        results = {}
    msgs = []
    while len(workers):
        item = push_queue_to_results(output_queue, results)
        if item is not None:
            id_ = item['salt_args'][0]
            th = workers.pop(id_, None)
            if th is not None:
                th.join(1)
                th.terminate()
        else:
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
    while push_queue_to_results(output_queue, results):
        pass
    return results


def wait_pool(workers, output_queue, results):
    if results is None:
        results = {}
    msgs = []
    while len(workers):
        try:
            item = output_queue.get(False, 0.1)
            if item is not None:
                id_ = item[0]
                th = workers.pop(id_, None)
                if th is not None and th.is_alive() and th.ident:
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
    while push_queue_to_results(output_queue, results):
        pass
    return results


def generate_masterless_pillars(ids_=None,
                                skip=None,
                                processes=None,
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
    if processes is None:
        try:
            grains = salt.loader.grains(_o)
            processes = int(grains['num_cpus'])
        except ValueError:
            processes = 0
        if processes < 2:
            processes = 2
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
    if processes:
        output_queue = mQueue()
    else:
        output_queue = Queue.Queue()
    threads = int(threads)
    for ix, id_ in enumerate(ids_):
        if id_ in skip:
            log.info('Skipping pillar generation for {0}'.format(id_))
            continue
        input_queue.put(id_)
        # for debug
        # if ix >= 2: break
    workers = {}
    results = {}
    try:
        size = input_queue.qsize()
        i = 0
        while not input_queue.empty():
            i += 1
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
            log.info('ETA: {0}/{1}'.format(i, size))
            if threads:
                if len(workers) >= threads:
                    wait_pool(workers, output_queue, results)
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
            wait_pool(workers, output_queue, results)
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
    for host, idata in six.iteritems(masterless_hosts):
        try:
            pillar = idata.get('salt_out', {}).get('pillar', {})
        except Exception:
            trace = traceback.format_exc()
            if idata.get('stderr'):
                sys.stderr.write(idata['stderr'])
            else:
                sys.stderr.write(trace)
            raise
        if '_errors' in pillar:
            raise AnsibleInventoryIncomplete(
                'Pillar for {0} has errors\n{1}'.format(
                    host,
                    '\n'.join(pillar['_errors'])))
        # ssh connecttion infos must have been exposed in
        # extpillars in the "saltapi.SSH_CON_PREFIX" subdict
        oinfos = pillar.get(saltapi.SSH_CON_PREFIX, {})
        pillar['makinastates_from_ansible'] = True
        hosts[host] = {
            'name': host,
            'ansible_host': host,
            'ansible_port': 22,
            'makinastates_from_ansible': True,
            'salt_pillar': pillar}
        # we can expose custom ansible host vars
        # by defining the "ansible_vars" inside the pillar
        hosts[host].update(
            copy.deepcopy(pillar.get('ansible_vars', {})))
        if hosts[host]['name'] and not hosts[host]['ansible_host']:
            hosts[host]['ansible_host'] = hosts[host]['name']
        hosts[host].update(oinfos)
        for i, aliases in six.iteritems({
            'ssh_name': ['name'],
            'ssh_host': ['ansible_host'],
            'ssh_sudo': ['ansible_become'],
            'ssh_port': ['ansible_port'],
            'ssh_password': ['ansible_password'],
            'ssh_key': ['ansible_ssh_private_key_file'],
            'ssh_username': ['ansible_user'],
            'ssh_gateway': [],
            'ssh_gateway_port': [],
            'ssh_gateway_user': [],
            'ssh_gateway_key': [],
            'ssh_gateway_password': []
        }):
            val = oinfos.get(i, None)
            if val is None:
                continue
            for alias in aliases:
                hosts[host][alias] = oinfos[i]
        hosts[host]['control_path'] = (
            '~/.assh'
            '-{ssh_username}'
            '@{ssh_host}'
            '.{ssh_port}'
        ).format(**hosts[host])
        c_a = 'ansible_ssh_common_args'
        c_av = hosts[host].setdefault(c_a, '')
        if not isinstance(c_av, six.string_types):
            hosts[host][c_a] = ''
        if hosts[host]['ssh_gateway']:
            hosts[host]['control_path'] += (
                '-via'
                '-{ssh_gateway_user}'
                '@{ssh_gateway}'
                '.{ssh_gateway_port}'
            ).format(**hosts[host])
            hosts[host][c_a] += ' -o ProxyCommand="ssh -W %h:%p -q'
            if hosts[host]['ssh_gateway_key']:
                hosts[host][c_a] += ' -i {0}'.format(
                    hosts[host]['ssh_gateway_key'])
            if hosts[host]['ssh_gateway_port']:
                hosts[host][c_a] += ' -p {0}'.format(
                    hosts[host]['ssh_gateway_port'])
            if hosts[host]['ssh_gateway_user']:
                hosts[host][c_a] += ' -l {0}'.format(
                    hosts[host]['ssh_gateway_user'])
            hosts[host][c_a] += ' {0}"'.format(
                hosts[host]['ssh_gateway'])
        if 'controlpath' not in c_a.lower():
            hosts[host][c_a] += ' -o ControlPath="{control_path}"'.format(**hosts[host])
    return hosts
# vim:set et sts=4 ts=4 tw=80:
