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
import logging
import json
import re
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
    EauthAuthenticationError,
    SaltClientError,
    SaltRunnerError
)
from salt.runner import RunnerClient
from mc_states import api
from mc_states.api import memoize_cache
from mc_states.api import six
import salt.utils.vt


log = logging.getLogger(__name__)
_CLIENTS = {}
_marker = object()
_RUNNERS = {}
LXC_IMPLEMENTATION = 'mc_lxc_fork'
LXC_IMPLEMENTATION = 'lxc'
DEFAULT_POLL = 0.4
STRIP_FLAGS = re.M | re.U | re.S
STRIPPED_RES = [
    re.compile(r"\x1b\[[0-9;]*[mG]", STRIP_FLAGS),
    re.compile(r"\x1b.*?[mGKH]", STRIP_FLAGS),
]


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
__CACHED_FUNS = {
    'test.ping': 3 * 60,  # cache ping for 3 minutes
    'lxc.list':  2,  # cache lxc.list for 2 seconds,
    'grains.items': 100,

    'mc_cloud_compute_node.settings': 600,
    'mc_cloud_images.settings': 900,
    'mc_cloud_controller.settings': 600,
    'mc_cloud_vm.settings': 900,
    'mc_cloud.settings': 900,

    'mc_cloud_compute_node.ext_pillar': 600,
    'mc_cloud_controller.ext_pillar': 600,
    'mc_cloud_vm.ext_pillar': 600,
    'mc_cloud_images.ext_pillar': 900,
    'mc_cloud.ext_pillar': 900,

    'mc_cloud_compute_node.extpillar_settings': 600,
    'mc_cloud_controller.extpillar_settings': 600,
    'mc_cloud_vm.extpillar_settings': 600,
    'mc_cloud.extpillar_settings': 900,
    'mc_cloud_images.extpillar_settings': 900,

    'mc_cloud_compute_node.ext_pillar': 600,
    'mc_cloud_vm.vt_extpillar': 600,
    'mc_cloud_vm.vm_extpillar': 600,

    'mc_cloud_vm.vt_settings': 600,
    'mc_cloud_vm.vm_settings': 600,
    'mc_cloud_vm.vts_settings': 600,
    'mc_cloud_vm.vms_settings': 600,

    'mc_nodetypes.registry': 900,
    'mc_cloud.registry': 900,
    'mc_services.registry': 900,
    'mc_controllers.registry': 900,
    'mc_localsettings.registry': 900,

    'mc_nodetypes.settings': 900,
    'mc_controllers.settings': 900,
    'mc_services.settings': 600,
    'mc_localsettings.settings': 600,
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


def master_opts(*args, **kwargs):
    if not kwargs:
        kwargs = {}
    kwargs.update({
        'cfgdir': __opts__.get('config_dir', None),
        'cfg': __opts__.get('conf_file', None),
    })
    return _master_opts(*args, **kwargs)


def get_local_client(cfgdir=None, cfg=None, conn=None, **kwargs):
    '''
    Get a local client

    cfgdir/cfg
        args given to localclient

    '''
    if isinstance(conn, LocalClient):
        return conn
    kw = {}
    if cfgdir:
        kw['cfgdir'] = cfgdir
    if cfg:
        kw['cfg'] = cfg
    key = '{0}_{1}'.format(cfgdir, cfg)
    if key not in _CLIENTS:
        _CLIENTS[key] = LocalClient(mopts=_master_opts(**kw))
    return _CLIENTS[key]


def get_local_runner(cfgdir=None, cfg=None, runner=None, **kwargs):
    conn = kwargs.get('runner', None)
    if isinstance(conn, RunnerClient):
        return conn
    kw = {}
    if cfgdir:
        kw['cfgdir'] = cfgdir
    if cfg:
        kw['cfgdir'] = cfg
    key = '{0}_{1}'.format(cfgdir, cfg)
    if key not in _RUNNERS:
        _RUNNERS[key] = RunnerClient(_master_opts(cfgdir=cfgdir, cfg=cfg))
    return _RUNNERS[key]


def _runner(*a, **kw):
    return get_local_runner(*a, **kw)


def get_local_target(cfgdir=None):
    target = _minion_opts(cfgdir=cfgdir).get('id', None)
    return target


def _client(*a, **kw):
    '''
    Retocompat alias
    '''
    return get_local_client(*a, **kw)


def get_failure_error(jid, target, fun, args, kw):
    try:
        jidt = ''
        if jid:
            jidt = '{0}'.format(jid)
        to_errmsg = (
            'Failure for [job/]fun[/args/kw'
            ' {1}{2}/{4}/{5}'
        ).format(None, jidt, fun, target, args, kw)
        raise
    except:
        jidt = ''
        if jid:
            jidt = '{0}'.format(jid)
        to_errmsg = (
            'Failure for [job/]fun'
            ' {1}{2}'
        ).format(None, jidt, fun, target)
    return to_errmsg



def get_timeout_error(wait_for_res,
                      jid,
                      target,
                      fun,
                      args,
                      kw):
    try:
        jidt = ''
        if jid:
            jidt = '{0}'.format(jid)
        to_errmsg = (
            'Timeout {0}s for [job/]fun[/args/kw'
            ' {1}{2}/{4}/{5}'
            ' launched on {3} is elapsed,'
            ' return will unlikely return results now'
        ).format(wait_for_res, jidt, fun, target, args, kw)
        raise
    except:
        jidt = ''
        if jid:
            jidt = '{0}'.format(jid)
        to_errmsg = (
            'Timeout {0}s for [job/]fun'
            ' {1}{2}'
            ' launched on {3} is elapsed,'
            ' return will unlikely return results now'
        ).format(wait_for_res, jidt, fun, target)
    return to_errmsg


def wait_running_job(target,
                     jid,
                     timeout=0,
                     running=True,
                     poll=DEFAULT_POLL,
                     conn=None,
                     **run_kw):
    if conn is None:
        conn = get_local_client(**run_kw)
    endto = time.time() + timeout
    while running:
        # Again, do not fall too quick on findjob which is quite
        # spamming the master and give too early of a false positive
        findtries, thistry = 10, 0
        rkwargs = {'tgt': target,
                   'fun': 'saltutil.find_job',
                   'arg': [jid],
                   'timeout': 10}
        while thistry < findtries:
            thistry += 1
            try:
                cret = conn.cmd(**rkwargs)
                break
            except (SaltClientError, EauthAuthenticationError) as exc:
                if thistry > findtries:
                    raise exc
                time.sleep(poll)
        running = bool(cret.get(target, False))
        if not running:
            break
        if running and (time.time() > endto):
            raise SaltExit(
                'Timeout {0}s for {1} is elapsed'.format(timeout, jid))
        time.sleep(poll)


def submit_async_job(target,
                     fun,
                     args,
                     kw,
                     timeout=10,
                     conn=None,
                     rkwargs=None,
                     **run_kw):
    if rkwargs is None:
        rkwargs = {}
    if conn is None:
        conn = get_local_client(**run_kw)
    cret = None
    arkwargs = copy.deepcopy(rkwargs)
    arkwargs['timeout'] = timeout
    findtries, thistry = 10, 0
    poll = rkwargs.get('poll', DEFAULT_POLL)
    jid = _marker
    while thistry < findtries:
        thistry += 1
        try:
            jid = conn.cmd_async(tgt=target,
                                 fun=fun,
                                 arg=args,
                                 kwarg=kw,
                                 **arkwargs)
            break
        except (SaltClientError, EauthAuthenticationError) as exc:
            if thistry > findtries:
                raise exc
            time.sleep(poll)
        # do not fall too quick on findjob which is quite spamming the
    _check_ret(jid, '', target, run, args, kw)
    # master and give too early of a false positive
    findtries, thistry = 10, 0
    while thistry < findtries:
        thistry += 1
        try:
            cret = conn.cmd(tgt=target, fun='saltutil.find_job',
                            arg=[jid], **rkwargs)
            break
        except (SaltClientError, EauthAuthenticationError) as exc:
            if thistry > findtries:
                raise exc
            time.sleep(poll)
    return jid, cret


def run_and_poll(target,
                 fun,
                 args,
                 kw,
                 conn=None,
                 runner=None,
                 rkwargs=None,
                 **run_kw):
    if runner is None:
        runner = get_local_runner(**run_kw)
    if conn is None:
        conn = get_local_client(**run_kw)
    if rkwargs is None:
        rkwargs = {}
    ret = _marker
    poll = rkwargs.get('poll', DEFAULT_POLL)
    wait_for_res = float({'test.ping': '5', }.get(fun, '120'))
    jid, cret = submit_async_job(target, fun, args, kw,
                                 conn=conn, rkwargs=rkwargs)
    running = bool(cret.get(target, False))
    wait_running_job(target, jid, running=running, conn=conn, poll=poll)
    wendto = time.time() + wait_for_res
    while True:
        cret = runner.cmd('jobs.lookup_jid', [jid, {'__kwarg__': True}])
        if target in cret:
            ret = cret[target]
            break
        # special case, some answers may be crafted
        # to handle the unresponsivness of a specific command
        # which is also meaningfull, eg a minion not yet provisionned
        if fun in ['test.ping'] and not wait_for_res:
            ret = {'test.ping': False}.get(fun, False)
        if time.time() > wendto:
            raise SaltExit(get_timeout_error(10, jid, target, fun, args, kw))
        time.sleep(poll)
    return _check_ret(ret, jid, fun, args, kw)


def _check_ret(ret, jid, target, fun, args, kw):
    if ret is _marker:
        raise SaltExit(get_failure_error( jid, target, fun, args, kw))
    return ret


def run(target, fun, args, kw, rkwargs=None, conn=None, **run_kw):
    if rkwargs is None:
        rkwargs = {}
    if conn is None:
        conn = get_local_client(**run_kw)
    # do not fall too quick on findjob which is quite spamming the
    # master and give too early of a false positive
    findtries, thistry = 10, 0
    ret = _marker
    while thistry < findtries:
        thistry += 1
        try:
            ret = conn.cmd(target, fun, args, kwarg=kw, **rkwargs)[target]
            break
        except (SaltClientError, EauthAuthenticationError) as exc:
            if thistry > findtries:
                raise exc
            time.sleep(0.4)
    return _check_ret(ret, '', target, fun, args, kw)


def assert_pinguable(target, max_retries=10, conn=None, **run_kw):
    if conn is None:
        conn = get_local_client(**run_kw)
    # be sure that the executors are alive
    ping_retries = 0
    while ping_retries <= max_retries:
        try:
            if ping_retries > 0:
                time.sleep(1)
            pings = conn.cmd(tgt=target,
                             timeout=10,
                             fun='test.ping')
            values = pings.values()
            ping = True
            if not values:
                ping = False
            for v in values:
                if v is not True:
                    ping = False
            if not ping:
                raise ValueError('Unreachable')
            break
        except Exception:
            ping = False
            ping_retries += 1
            log.error(get_timeout_error(
                10, '', target, 'test.ping', '', ''))
    if not ping:
        raise SaltExit('Target {0} unreachable'.format(target))


def client(fun, *args, **kw):
    '''
    Execute a salt function on a specific minion using the salt api.
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
            salt_ttl
                cache ttl
                either 2 seconds or see __CACHED_FUNS preselector
    '''
    ttl = kw.pop('salt_ttl',
                 __CACHED_FUNS.get(fun, None))
    # if we did not select a ttl, be sure not to cache
    force_run = ttl is None
    run_kw = {}
    try:
        run_kw['poll'] = kw.pop('salt_job_poll')
    except KeyError:
        run_kw['poll'] = 0.4
    try:
        run_kw['cfgdir'] = kw.pop('salt_cfgdir')
    except KeyError:
        run_kw['cfgdir'] = None
    try:
        __opts__ = kw.pop('salt___opts__')
    except KeyError:
        __opts__ = {}
    try:
        run_kw['cfg'] = kw.pop('salt_cfg')
    except KeyError:
        run_kw['cfg'] = None
    try:
        target = run_kw['target'] = kw.pop('salt_target')
    except KeyError:
        target = run_kw['target'] = None
    if not target:
        target = run_kw['target'] = get_local_target(cfgdir=run_kw['cfgdir'])
        if not target:
            raise SaltExit('no target')
    try:
        run_kw['polling'] = bool((kw.pop('salt_polling')))
    except (KeyError, ValueError):
        # try to has some low timeouts for very basic commands
        # wait up to 15 minutes for the default timeout
        run_kw['polling'] = False
    try:
        run_kw['timeout'] = int(kw.pop('salt_timeout'))
    except (KeyError, ValueError):
        # try to has some low timeouts for very basic commands
        # wait up to 15 minutes for the default timeout
        run_kw['timeout'] = __FUN_TIMEOUT.get(fun, 900)
    try:
        run_kw['kwargs'] = kw.pop('kwargs')
    except KeyError:
        run_kw['kwargs'] = {}
    try:
        sargs = json.dumps(args)
    except TypeError:
        sargs = ''
    try:
        skw = json.dumps(kw)
    except TypeError:
        skw = ''
    try:
        skwargs = json.dumps(run_kw['kwargs'])
    except TypeError:
        skwargs = ''

    def _do(target, fun, args, kw, run_kw):
        conn = get_local_client(**run_kw)
        runner = get_local_runner(**run_kw)
        # do not check ping... if we are pinguing
        if not fun == 'test.ping':
            assert_pinguable(target, max_retries=6, conn=conn)
        # throw the real job command
        findtries, thistry = 10, 0
        ret = _marker
        rkwargs = run_kw['kwargs']
        while thistry < findtries:
            thistry += 1
            if not run_kw['polling']:
                ret = run(target, fun, args, kw, conn=conn, rkwargs=rkwargs)
            else:
                ret = run_and_poll(target, fun, args, kw,
                                   rkwargs=rkwargs, runner=runner, conn=conn)
            if ret is not _marker:
                break
            if thistry > findtries:
                raise SaltExecutionError(
                    'module/function {0} failed:\n too many retries without'
                    ' return')
        if isinstance(ret, six.string_types):
            if 'The minion function caused an exception:' in ret:
                raise SaltExecutionError(
                    'module/function {0} failed:\n {1}'.format(fun, ret))
            elif 'is not available.' in ret:
                raise SaltExit(
                    'module/function {0} is not available'.format(fun))
        return ret
    cache_key = 'mcapi_' + '_'.join([target, fun, sargs, skw, skwargs])
    return memoize_cache(_do, [target, fun, args, kw, run_kw], {},
                         cache_key, ttl, force_run=force_run)


def _errmsg(ret, msg):
    err = '\n{0}\n'.format(msg)
    for k in ['comment', 'trace']:
        if ret[k]:
            err += '\n{0}:\n{1}\n'.format(k, ret[k])
    raise SaltExit(err)


def errmsg(msg):
    raise MessageError(msg)


def salt_output(ret,
                __opts__,
                output=True,
                onlyret=False,
                __jid_event__=None):
    if output:
        api.msplitstrip(ret)
        # copy the result to zresult key for bare out to really
        # display the summary at the end of the console stream
        ret['z_500_output'] = ret['output']
        ret['z_700_comment'] = ret['comment']
        ret['z_900_result'] = ret['result']
        dret = ret
        if onlyret:
            dret = dret['z_900_result']
        if __jid_event__ is None:
            salt.output.display_output(dret, '', __opts__)
        else:
            __jid_event__.fire_event(
                {'data': dret, 'outputter': 'nested'},
                'print')
        del ret['z_500_output']
        del ret['z_700_comment']
        del ret['z_900_result']


def complete_gateway(target_data, default_data=None):
    if default_data is None:
        default_data = {}
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
    if colors and isinstance(colors, dict):
        # compat to old themes
        colors.update({'PURPLE':  colors.get('MAGENTA', ''),
                       'LIGHT_PURPLE': colors.get('LIGHT_MAGENTA', ''),
                       'PURPLE_BOLD': colors.get('LIGHT_MAGENTA', ''),
                       'RED_BOLD': colors.get('LIGHT_RED', ''),
                       'BROWN': colors.get('YELLOW', '')})
    if color:
        if color not in colors:
            log.error('No such color {0}'.format(color))
            ret = ''
        else:
            ret = colors[color]
        return ret
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


def strip_colors(line):
    stripped_line = line
    for stripped_re in STRIPPED_RES:
        stripped_line = stripped_re.sub('', stripped_line)
    stripped_line = salt.output.strip_esc_sequence(line)
    return stripped_line


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


def _get_ssh_ret(**kw):
    return salt.utils.dictupdate.update({'retcode': 1255,
                                         'pid': -1,
                                         'stdout': '',
                                         'stderr': '',
                                         'trace': ''},
                                        kw)

class _SSHExecError(salt.utils.vt.TerminalException):
    """."""

    def __init__(self, message, exec_ret=_marker):
        super(_SSHExecError, self).__init__(message)
        if exec_ret is _marker:
            exec_ret = _get_ssh_ret()
        self.exec_ret = exec_ret


class _SSHLoginError(_SSHExecError):
    """."""


class _SSHTimeoutError(_SSHLoginError):
    '''.'''


class _SSHVtError(_SSHExecError):
    """."""


class _SSHInterruptError(_SSHExecError):
    """."""


class _SSHCommandFinished(_SSHExecError):
    """."""


class _SSHCommandFailed(_SSHCommandFinished):
    """."""


class _SSHCommandTimeout(_SSHCommandFailed):
    """."""


class _SSHTransferFailed(_SSHCommandFailed):
    """."""


class _SaltCallFailure(_SSHExecError):
    """."""


def asbool(item):
    if isinstance(item, six.string_types):
        item = item.lower()
    if item in [None, False, 0, '0', 'no', 'n', 'n', 'non']:
        item = False
    if item in [True, 1, '1', 'yes', 'y', 'o', 'oui']:
        item = True
    return bool(item)
# vim:set et sts=4 ts=4 tw=80:
