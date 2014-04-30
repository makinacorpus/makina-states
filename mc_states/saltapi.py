#!/usr/bin/env python
'''

.. _mc_saltapi:

Convenient functions to use a salt infra as an api
==================================================
'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import salt.config as config
import os
import json
from pprint import pformat
import salt.syspaths
from mc_states.modules.mc_utils import dictupdate
import copy
import traceback
from salt.utils import check_state_result
import time

import salt.utils
from salt.client import LocalClient
from salt.exceptions import (
    SaltException,
    SaltRunnerError
)
from salt.runner import RunnerClient
from mc_states import api


class SaltExit(SaltException):
    pass


class SaltRudeError(SystemExit):
    pass


class SaltExecutionError(SaltExit):
    pass


class FailedStepError(SaltRudeError):
    pass


class ProvisionError(SaltRudeError):
    pass


class SaltInvalidReturnError(SaltExit):
    pass


class SaltEmptyDictError(SaltInvalidReturnError):
    pass


class SaltyficationError(ProvisionError):
    pass


class ComputeNodeProvisionError(ProvisionError):
    pass


class VMProvisionError(ProvisionError):
    pass


class SaltCopyError(SaltRudeError):
    pass


class MessageError(SaltException):
    pass


__RESULT = {'comment': '',
            'changes': {},
            'output': '',
            'trace': '',
            'result': True}


def result(**kwargs):
    try:
        ret = kwargs.pop('ret', {})
    except IndexError:
        ret = {}
    ret = copy.deepcopy(__RESULT)
    ret.update(kwargs)
    return ret


__FUN_TIMEOUT = {
    'mc_cloud_lxc.get_settings_for_vm': 120,
    'mc_cloud_compute_node.get_settings_for_target': 300,
    'mc_cloud_compute_node.get_reverse_proxies_for_target': 300,
    'mc_cloud_compute_node.settings': 300,
    'mc_cloud_controller.settings': 300,
    'mc_cloud_images.settings': 120,
    'mc_cloud.settings': 120,
    'mc_cloud_lxc.settings': 120,
    'cmd.run': 60 * 60,
    'test.ping': 10,
    'lxc.info': 40,
    'lxc.list': 300,
    'lxc.templates': 100,
    'grains.items': 100,
    'state.sls': 60*60*5,
}
__CACHED_CALLS = {}
__CACHED_FUNS = {
    'test.ping': 3 * 60,  # cache ping for 3 minutes
    'lxc.list':  2,  # cache lxc.list for 2 seconds,
    'grains.items': 100,

    'mc_cloud_lxc.get_settings_for_vm': 900,
    'mc_cloud_compute_node.get_settings_for_target': 900,
    'mc_cloud_compute_node.get_reverse_proxies_for_target': 900,
    'mc_cloud_compute_node.settings': 600,
    'mc_cloud_controller.settings': 600,
    'mc_cloud_images.settings': 900,
    'mc_cloud_lxc.settings': 900,

    'mc_nodetypes.registry': 900,
    'mc_cloud.registry': 900,
    'mc_services.registry': 900,
    'mc_controllers.registry': 900,
    'mc_localsettings.registry': 900,

    'mc_cloud.settings': 900,
    'mc_nodetypes.settings': 900,
    'mc_controllers.settings': 900,
    'mc_services.settings': 600,
    'mc_localsettings.settings': 600,
}


def invalidate(laps=None,
               target=None,
               fun=None,
               sargs=None,
               skw=None,
               skwargs=None):
    '''Invalidate something in the api cached calls
    by matching on any of the parameters'''
    if (
        laps is None
        and target is None
        and fun is None
        and sargs is None
        and skw is None
        and skwargs is None
    ):
        return
    args = [laps, target, fun, sargs, skw, skwargs]
    popping = []
    for key in __CACHED_CALLS:
        match = None
        for j, arg in enumerate(args):
            if arg is None:
                continue
            if match is not False:
                if arg == key[j]:
                    match = True
                else:
                    match = False
        if match:
            popping.append(key)
    for pop in popping:
        __CACHED_CALLS.pop(pop)


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



def master_opts(*args, **kwargs):
    if not kwargs:
        kwargs = {}
    kwargs.update({
        'cfgdir': __opts__.get('config_dir', None),
        'cfg': __opts__.get('conf_file', None),
    })
    return _master_opts(*args, **kwargs)


def _runner(cfgdir=None, cfg=None):
    # opts = _master_opts()
    # opts['output'] = 'quiet'
    return RunnerClient(_master_opts(cfgdir=cfgdir, cfg=cfg))


def get_local_target(cfgdir=None):
    target = _minion_opts(cfgdir=cfgdir).get('id', None)
    return target


def _client(cfgdir=None, cfg=None):
    return LocalClient(mopts=_master_opts(cfgdir=cfgdir, cfg=cfg))


def client(fun, *args, **kw):
    '''Execute a salt function on a specific minion using the salt api.
    This will set automatic timeouts for well known functions.
    This will also call well known api calls for a specific time.

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
        poll = 0.4
    try:
        cfgdir = kw.pop('salt_cfgdir')
    except KeyError:
        cfgdir = None
    try:
        __opts__ = kw.pop('salt___opts__')
    except KeyError:
        __opts__ = {}
    try:
        cfg = kw.pop('salt_cfg')
    except KeyError:
        cfg = None
    try:
        target = kw.pop('salt_target')
    except KeyError:
        target = None
    if not target:
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
        rkwargs = kwargs.copy()
        rkwargs['timeout'] = timeout
        jid = conn.cmd_async(tgt=target,
                             fun=fun,
                             arg=args,
                             kwarg=kw,
                             **rkwargs)
        cret = conn.cmd(tgt=target,
                        fun='saltutil.find_job',
                        arg=[jid],
                        timeout=10,
                        **kwargs)
        try:
            if 'spawn' in args[0]:
                import pdb;pdb.set_trace()  ## Breakpoint ##
        except:
            pass

        running = bool(cret.get(target, False))
        endto = time.time() + timeout
        while running:
            rkwargs = {'tgt': target,
                       'fun': 'saltutil.find_job',
                       'arg': [jid],
                       'timeout': 10}
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
        wendto = time.time() + wait_for_res
        while True:
            cret = runner.cmd('jobs.lookup_jid',
                              [jid, {'__kwarg__': True, 'output': False}])
            if target in cret:
                ret = cret[target]
                break
            # special case, some answers may be crafted
            # to handle the unresponsivness of a specific command
            # which is also meaningfull, eg a minion not yet provisionned
            if fun in ['test.ping'] and not wait_for_res:
                ret = {'test.ping': False}.get(fun, False)
            if time.time() > wendto:
                try:
                    msg = (
                        'Timeout {0}s for job/fun/kw {1}/{3}/{4} '
                        'running on {3} is elapsed, '
                        'return will unlikely retun results now'
                    ).format(wait_for_res, jid, fun, target, kw)
                except:
                    msg = (
                        'Timeout {0}s for job/fun {1}/{2}'
                        ' running on {3} is elapsed,'
                        ' return will unlikely return results now'
                    ).format(wait_for_res, jid, fun, target, kw)
                raise SaltExit(msg)
            time.sleep(poll)
        try:
            if 'The minion function caused an exception:' in ret:
                raise SaltExecutionError(
                    'module/function {0} failed:\n {1}'.format(fun, ret))
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


def _errmsg(ret, msg):
    err = '\n{0}\n'.format(msg)
    for k in ['comment', 'trace']:
        if ret[k]:
            err += '\n{0}:\n{1}\n'.format(k, ret[k])
    raise SaltExit(err)


def errmsg(msg):
    raise MessageError(msg)


def salt_output(ret, __opts__, output=True):
    if output:
        api.msplitstrip(ret)
        # copy the result to zresult key for bare out to really
        # display the summary at the end of the console stream
        ret['z_500_output'] = ret['output']
        ret['z_700_comment'] = ret['comment']
        ret['z_900_result'] = ret['result']
        salt.output.display_output(ret, '', __opts__)
        del ret['z_500_output']
        del ret['z_700_comment']
        del ret['z_900_result']

def complete_gateway(target_data, default_data):
    if 'ssh_gateway' in target_data:
        gwk = target_data
    else:
        target_data.setdefault('gateway', {})
        gwk = target_data['gateway']
    if gwk:
        gw = target_data.get('ssh_gateway',
                             default_data.get('ssh_gateway', None))
        if gw:
            for k in [
                'ssh_gateway', 'ssh_gateway_user', "ssh_gateway_password",
                'ssh_gateway_key', 'ssh_gateway_port',
            ]:

                if 'defaults' in default_data:
                    default = default_data['defaults'].get(
                        k, default_data.get(k, None))
                else:
                    default = default_data.get(k, None)
                gwk.setdefault(k,
                               target_data.get(k, default))
            if gwk['ssh_gateway_password'] and ('ssh_gateway_key' in gwk):
                del gwk['ssh_gateway_key']
    return target_data


def check_point(ret, __opts__, output=True):
    api.msplitstrip(ret)
    if not ret['result']:
        salt_output(ret, __opts__, output=output)
        raise FailedStepError(
            red('Execution of the runner has been stopped due to'
                ' error'))


def _colors(color=None, colorize=True):
    colors = salt.utils.get_colors(colorize)
    if color:
        return colors[color]
    return colors


def yellow(string):
    return '{0}{2}{1}'.format(_colors('YELLOW'), _colors('ENDC'), string)


def green(string):
    return '{0}{2}{1}'.format(_colors('GREEN'), _colors('ENDC'), string)


def red(string):
    return '{0}{2}{1}'.format(_colors('RED'), _colors('ENDC'), string)


def blue(string):
    return '{0}{2}{1}'.format(_colors('LIGHT_CYAN'), _colors('ENDC'), string)


def blue_line(string):
    return "\n{0}\n".format(blue(string))


def yellow_line(string):
    return "\n{0}\n".format(yellow(string))


def green_line(string):
    return "\n{0}\n".format(green(string))


def red_line(string):
    return "\n{0}\n".format(red(string))


def process_cloud_return(name, info, driver='saltify', ret=None):
    if ret is None:
        ret = result()
    # get either {Error: ''} or {namestring: {Error: ''}}
    # which is what we can get from providers returns
    main_error = info.get('Error', '')
    name_error = ''
    if isinstance(info, dict):
        subinfo = info.get(name, {})
        if isinstance(subinfo, dict):
            name_error = subinfo.get('Error', None)
    error = main_error or name_error
    if info and not error:
        node_info = info.get(name)
        default_msg = '\nSaltified {0}'.format(name)
        # some providers support changes
        if 'changes' in node_info:
            ret['changes'] = node_info['changes']
            cmt = node_info.get('comment', default_msg)
            ret['comment'] = '\n{0}'.format(cmt)
        else:
            ret['changes'] = info
            ret['comment'] = default_msg
    elif error:
        ret['result'] = False
        ret['comment'] += ('\nFailed to install with {2} {0}: {1}').format(
            name,
            '{0}\n{1}\n'.format(main_error, name_error).strip(), driver)
    else:
        ret['result'] = False
        ret['comment'] += '\nFailed to saltify {0}'.format(name)
    return ret


def merge_results(ret, cret):
    # sometime we delete some stuff from the to be merged  results
    # dict to only keep some infos
    if 'result' in cret:
        if not cret['result']:
            ret['result'] = False
    for k in ['output', 'comment', 'trace']:
        if k not in ret:
            ret[k] = ''
        if cret.get(k, None) is not None:
            ret[k] += "\n{0}".format(cret[k])
    for k in ['changes']:
        if k in cret and k in ret:
            ret[k] = dictupdate(ret[k], cret[k])
    return ret

# vim:set et sts=4 ts=4 tw=80:
