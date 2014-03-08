#!/usr/bin/env python
'''
Convenient functions to use a salt infra as an api
==================================================
'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import salt.config as config
import json
from pprint import pformat
import salt.syspaths
import os
import copy
import time
from salt.client import LocalClient
from salt.exceptions import SaltException
from salt.runner import RunnerClient


class SaltExit(SaltException):
    '''.'''


class MessageError(SaltException):
    '''.'''


__RESULT = {'comment': '',
            'changes': {},
            'trace': '',
            'result': True}


def result(**kwargs):
    ret = copy.deepcopy(__RESULT)
    ret.update(kwargs)
    return ret


__FUN_TIMEOUT = {
    'cmd.run': 60 * 60,
    'test.ping': 10,
    'lxc.info': 40,
    'lxc.list': 300,
    'lxc.templates': 100,
    'grains.items': 100,
}
__CACHED_CALLS = {}
__CACHED_FUNS = {
    'test.ping': 3 * 60,  # cache ping for 3 minutes
    'lxc.list':  2  # cache lxc.list for 2 seconds
}


def _minion_opts(cfgdir=None, cfg=None):
    if not cfgdir:
        cfgdir = salt.syspaths.CONFIG_DIR
    if not cfg:
        cfg = os.environ.get('SALT_MINION_CONFIG', 'minion')
        cfg = os.path.join(cfgdir, cfg)
    opts = config.minion_config(cfg)
    return opts


def _master_opts(cfgdir=None, cfg=None):
    if not cfgdir:
        cfgdir = salt.syspaths.CONFIG_DIR
    if not cfg:
        cfg = os.environ.get('SALT_MASTER_CONFIG', 'master')
        cfg = os.path.join(cfgdir, cfg)
    opts = config.master_config(cfg)
    return opts


def _client(cfgdir=None, cfg=None):
    return LocalClient(mopts=_master_opts(cfgdir=cfgdir, cfg=cfg))


def _runner(cfgdir=None, cfg=None):
    # opts = _master_opts()
    # opts['output'] = 'quiet'
    return RunnerClient(_master_opts(cfgdir=cfgdir, cfg=cfg))


def get_local_target(cfgdir=None):
    target = _minion_opts(cfgdir=cfgdir).get('id', None)
    return target


def client(fun, *args, **kw):
    '''Execute a salt function on a specific minion

    Special kwargs:

            salt_cfgdir
                alternative configuration file directory
            salt_cfg
                alternative configuration file
            salt_target
                target to exec things on
            salt_timeout
                timeout for jobs
            salt_job_poll
                poll interval to wait for job finish result
    '''
    try:
        poll = kw.pop('salt_job_poll')
    except KeyError:
        poll = 0.1
    try:
        cfgdir = kw.pop('salt_cfgdir')
    except KeyError:
        cfgdir = None
    try:
        cfg = kw.pop('salt_cfg')
    except KeyError:
        cfg = None
    try:
        target = kw.pop('salt_target')
    except KeyError:
        target = get_local_target(cfgdir=cfgdir)
        if not target:
            raise SaltExit('no target')
    try:
        timeout = int(kw.pop('salt_timeout'))
    except (KeyError, ValueError):
        # try to has some low timeouts for very basic commands
        timeout = __FUN_TIMEOUT.get(
            fun,
            900  # wait up to 15 minutes for the default timeout
        )
    try:
        kwargs = kw.pop('kwargs')
    except KeyError:
        kwargs = {}
    laps = time.time()
    cache = False
    if fun in __CACHED_FUNS:
        cache = True
        laps = laps // __CACHED_FUNS[fun]
    try:
        sargs = json.dumps(args)
    except TypeError:
        sargs = ''
    try:
        skw = json.dumps(kw)
    except TypeError:
        skw = ''
    try:
        skwargs = json.dumps(kwargs)
    except TypeError:
        skwargs = ''
    cache_key = (laps, target, fun, sargs, skw, skwargs)
    if not cache or (cache and (not cache_key in __CACHED_CALLS)):
        conn = _client(cfgdir=cfgdir, cfg=cfg)
        runner = _runner(cfgdir=cfgdir, cfg=cfg)
        kwargs['timeout'] = timeout
        jid = conn.cmd_async(tgt=target,
                             fun=fun,
                             arg=args,
                             kwarg=kw,
                             timeout=timeout,
                             **kwargs)
        cret = conn.cmd(tgt=target,
                        fun='saltutil.find_job',
                        arg=[jid],
                        timeout=10,
                        **kwargs)
        running = bool(cret.get(target, False))
        endto = time.time() + timeout
        while running:
            rkwargs = {
                'tgt': target,
                'fun': 'saltutil.find_job',
                'arg': [jid],
                'timeout': 10
            }
            cret = conn.cmd(**rkwargs)
            running = bool(cret.get(target, False))
            if not running:
                break
            if running and (time.time() > endto):
                raise SaltExit('Timeout {0}s for {1} is elapsed'.format(
                    timeout, pformat(kwargs)))
            time.sleep(poll)
        # timeout for the master to return data about a specific job
        wait_for_res = float({
            'test.ping': '5',
        }.get(fun, '120'))
        while wait_for_res:
            wait_for_res -= poll
            cret = runner.cmd(
                'jobs.lookup_jid',
                [jid, {'__kwarg__': True, 'output': False}])
            if target in cret:
                ret = cret[target]
                break
            # special case, some answers may be crafted
            # to handle the unresponsivness of a specific command
            # which is also meaningfull, eg a minion not yet provisionned
            if fun in ['test.ping'] and not wait_for_res:
                ret = {
                    'test.ping': False,
                }.get(fun, False)
            time.sleep(poll)
        try:
            if 'is not available.' in ret:
                raise SaltExit(
                    'module/function {0} is not available'.format(fun))
        except SaltExit:
            raise
        except TypeError:
            pass
        if cache:
            __CACHED_CALLS[cache_key] = ret
    elif cache and cache_key in __CACHED_CALLS:
        ret = __CACHED_CALLS[cache_key]
    return ret

def splitstrip(string):
    return '\n'.join(
        [a for a in string.splitlines() if a.strip()])


def msplitstrip(mapping):
    for k in ['trace', 'comment']:
        if k in mapping:
            mapping[k] = splitstrip(mapping[k])


def _errmsg(ret, msg):
    err = '\n{0}\n'.format(msg)
    for k in ['comment', 'trace']:
        if ret[k]:
            err += '\n{0}:\n{1}\n'.format(k, ret[k])
    raise SaltExit(err)

# vim:set et sts=4 ts=4 tw=80:
