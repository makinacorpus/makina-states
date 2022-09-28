#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import copy
import traceback
import time

import salt.utils
try:
    from salt.utils import fopen
except ImportError:
    from salt.utils.files import fopen

try:
    from salt.utils import traverse_dict
except ImportError:
    from salt.utils.data import traverse_dict

try:
    from salt.utils import check_state_result
    check_result = check_state_result
except ImportError:
    from salt.utils.state import check_result
    check_state_result = check_result

try:
    from salt.utils import clean_kwargs
except ImportError:
    from salt.utils.args import clean_kwargs

try:
    from salt.utils import get_colors
except ImportError:
    from salt.utils.color import get_colors

try:
    from salt.utils import DEFAULT_TARGET_DELIM
except ImportError:
    from salt.defaults import DEFAULT_TARGET_DELIM

from salt.utils.odict import OrderedDict
import salt.utils.vt
from salt.client import LocalClient
import salt.exceptions
from salt.runner import RunnerClient
from mc_states import api

# let do some alias imports for api consumers to let them
# import also from saltapi to limit the imports todo
from mc_states.api import memoize_cache
from mc_states.api import get_cache_key
from mc_states.api import six
from mc_states.api import asbool
from mc_states.api import STRIPPED_RES
from mc_states.api import strip_colors
from mc_states.api import magicstring
from mc_states.api import get_ssh_username
from mc_states.api import no_more_mastersalt
from mc_states.modules.mc_utils import dictupdate


log = logging.getLogger(__name__)
SSH_CON_PREFIX = 'makina-states.ssh_connection'
_CLIENTS = {}
_marker = object()
_RUNNERS = {}
# LXC_IMPLEMENTATION = 'mc_lxc_fork'
LXC_IMPLEMENTATION = 'lxc'
DEFAULT_POLL = 0.4
__RESULT = {'comment': '',
            'changes': {},
            'output': '',
            'trace': '',
            'result': True}
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
    'state.sls': 60*60*5}
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
    'mc_localsettings.settings': 600}


class PortConflictError(ValueError):
    '''.'''


class ImgError(salt.exceptions.SaltException):
    pass


class ImgStepError(ImgError):
    '''.'''


class MastersaltNotInstalled(salt.exceptions.SaltException, ValueError):
    pass


class MastersaltNotRunning(salt.exceptions.SaltException, ValueError):
    pass


class SaltExit(salt.exceptions.SaltException):
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


class MessageError(salt.exceptions.SaltException):
    pass


class SSHExecError(salt.utils.vt.TerminalException):
    """."""

    def __init__(self, message, exec_ret=_marker):
        super(SSHExecError, self).__init__(message)
        if exec_ret is _marker:
            exec_ret = _get_ssh_ret()
        self.exec_ret = exec_ret


SSHExecError = SSHExecError  # retrocompat


class SSHLoginError(SSHExecError):
    """."""


class SSHTimeoutError(SSHLoginError):
    '''.'''


class SSHVtError(SSHExecError):
    """."""


class SSHInterruptError(SSHExecError):
    """."""


class SSHCommandFinished(SSHExecError):
    """."""


class SSHCommandFailed(SSHCommandFinished):
    """."""


class SSHCommandTimeout(SSHCommandFailed):
    """."""


class SSHTransferFailed(SSHCommandFailed):
    """."""


class SaltCallFailure(SSHExecError):
    """."""


_SaltCallFailure = SaltCallFailure  # retrocompat


class NoRegistryLoaderFound(salt.exceptions.SaltException):
    """."""


class RemoteResultProcessError(salt.exceptions.SaltException):
    def __init__(self, msg, original=None, ret=None, *args, **kwargs):
        super(RemoteResultProcessError, self).__init__(msg, *args, **kwargs)
        self.original = original
        self.ret = ret


class RenderError(RemoteResultProcessError):
    '''.'''


class TransformError(RemoteResultProcessError):
    '''.'''


class IPRetrievalError(KeyError):
    ''''''


class RRError(ValueError):
    """."""


class NoResultError(KeyError):
    ''''''


class PillarError(Exception):
    ''''''


def result(**kwargs):
    try:
        ret = kwargs.pop('ret', {})
    except IndexError:
        ret = {}
    ret = copy.deepcopy(__RESULT)
    ret.update(kwargs)
    return ret


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
            except (
                salt.exceptions.SaltClientError,
                salt.exceptions.EauthAuthenticationError
            ) as exc:
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
        except (
            salt.exceptions.SaltClientError,
            salt.exceptions.EauthAuthenticationError
        ) as exc:
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
        except (
            salt.exceptions.SaltClientError,
            salt.exceptions.EauthAuthenticationError
        ) as exc:
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
        # recent changes
        elif 'data' in cret and 'outputter' in cret:
            ret = cret['data']
            break
        # special case, some answers may be crafted
        # to handle the unresponsivness of a specific command
        # which is also meaningfull, eg a minion not yet provisionned
        if fun in ['test.ping'] and not wait_for_res:
            ret = {'test.ping': False}.get(fun, False)
        if time.time() > wendto:
            raise SaltExit(get_timeout_error(10, jid, target, fun, args, kw))
        time.sleep(poll)
    return _check_ret(ret, jid, target, fun, args, kw)


def _check_ret(ret, jid, target, fun, args, kw):
    if ret is _marker:
        raise SaltExit(get_failure_error(jid, target, fun, args, kw))
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
        except (
            salt.exceptions.SaltClientError,
            salt.exceptions.EauthAuthenticationError
        ) as exc:
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


def concat_res_or_rets(ret,
                       cret=None,
                       result_keys=None,
                       output_keys=None,
                       dict_keys=None,
                       omit=None):
    '''
    Convenient and magical way to merge 2 structures
    or strings for usage in salt functions.

    concatenate string with string
        join them (separated with a newline)
    concatenate string with dict:
        append all output keys from dict in the
        string separated by a new line and prefixed
        by the output key identfier
    concatenate dict with string:
        concatenate (with newlineà)
        the string in all output keys
    concatenate dict with dict:
        merge corresponding keys in an intelligent way:

        - result from ret is setted to false
          if cret's one is setted to False
        - merge output keys (separate with newline)
        - merge dict keys by updating or creating
          the corresponding key in ret from cret

    .. doctest:: example

    >>> from collections import OrderedDict
    >>> from mc_states.saltapi import concat_res_or_rets
    >>> concat_res_or_rets({}, {'result': False})
    {'result': False}
    >>> concat_res_or_rets({'result': True}, {'result': False})
    {'result': False}
    >>> concat_res_or_rets('oo', {'stdout': 'a', 'stderr': 'b'})
    'oo\\nSTDOUT: a\\nSTDERR: b'
    >>> concat_res_or_rets('a', 'b')
    'a\\nb'
    >>> concat_res_or_rets(OrderedDict([('stdout', 'a'), ('stderr', 'b')]),
    ...                    'de')
    OrderedDict([('stdout', 'a\\nde'), ('stderr', 'b'), ('output', 'de')])
    >>> concat_res_or_rets(OrderedDict([('stdout', 'a'), ('stderr', 'b')]),
    ...                    {'stdout': 'c', 'stderr': 'd'})
    OrderedDict([('stdout', 'a\\nc'), ('stderr', 'b\\nd')])
    >>> concat_res_or_rets({'changes': {1: 2, 3: 4, 5: 6}},
    ...                    {'changes': {1: 3, 3: 4}})
    {'changes': {1: 3, 3: 4, 5: 6}}

    '''
    if not result_keys:
        result_keys = ['result']
    if not output_keys:
        output_keys = ['stdout', 'stderr',
                       'comment' 'trace', 'output']
    if not dict_keys:
        dict_keys = ['changes']
    if not omit:
        omit = []
    if not isinstance(ret, (six.string_types, dict)):
        ret = api.asstring(ret)
    if not isinstance(cret, (six.string_types, dict)):
        cret = api.asstring(cret)
    if isinstance(cret, six.string_types) and isinstance(ret, dict):
        cret = {'stdout': cret, 'comment': cret,
                'trace': cret, 'output': cret}
    if isinstance(ret, six.string_types):
        ret = api.magicstring(ret)
    elif isinstance(ret, dict):
        for k in output_keys:
            if k in omit:
                continue
            val = ret.get(k, None)
            if isinstance(val, six.string_types):
                ret[k] = api.magicstring(val)
    for k in result_keys:
        if (
            isinstance(cret, dict) and
            isinstance(ret, dict) and
            (k in cret)
        ):
            if not cret.get(k):
                ret[k] = False
    if isinstance(ret, dict):
        for k in output_keys:
            if not cret:
                break
            elif k in omit:
                continue
            val = api.asstring(ret.get(k, None))
            oval = api.asstring(cret.get(k, None))
            if oval:
                formatting = "{0}\n{1}"
                if not val:
                    formatting = "{1}"
                if val != oval:
                    ret[k] = formatting.format(
                        api.magicstring(val),
                        api.magicstring(oval))
    if isinstance(ret, six.string_types) and cret:
        if isinstance(cret, dict):
            for k in output_keys:
                if k not in cret:
                    continue
                if k in omit:
                    continue
                val = cret[k]
                if not val:
                    continue
                sval = api.magicstring(val)
                ret = '{0}\n{1}: {2}'.format(
                    ret, k.upper(), sval)
        elif isinstance(cret, six.string_types) and cret:
            ret = '{0}\n{1}'.format(
                api.magicstring(ret),
                api.magicstring(cret))
    if isinstance(ret, dict) and isinstance(cret, dict):
        for k in dict_keys:
            if k in omit:
                continue
            if k in cret or k in ret:
                d1 = ret.get(k, OrderedDict())
                d2 = cret.get(k, OrderedDict())
                if isinstance(d1, dict) and isinstance(d2, dict):
                    ret[k] = dictupdate(d1, d2)
    return ret


def merge_results(ret, cret):
    # sometime we delete some stuff from the to be merged  results
    # dict to only keep some infos
    return concat_res_or_rets(ret, cret)


def rich_error(klass=salt.exceptions.SaltException,
               msg='error',
               cret=None):
    msg = concat_res_or_rets(msg, cret)
    return klass(msg)


def _errmsg(ret, msg):
    raise rich_error(SaltExit, msg, ret)


def errmsg(msg, ret=None):
    raise rich_error(MessageError, msg, ret)


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
    colors = get_colors(colorize)
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


def _get_ssh_ret(**kw):
    return salt.utils.dictupdate.update({'retcode': 1255,
                                         'pid': -1,
                                         'stdout': '',
                                         'stderr': '',
                                         'trace': ''},
                                        kw)


def sanitize_kw(kw, omit=None, default=True):
    ckw = copy.deepcopy(kw)
    if not omit:
        omit = []
    if isinstance(omit, six.string_types):
        omit = omit.split(',')
    if default:
        omit.append('^__pub')
    for k in [a for a in ckw]:
        if not isinstance(k, six.string_types):
            continue
        else:
            for pattern in omit:
                if re.search(pattern,  k):
                    ckw.pop(k, None)
    return ckw
# vim:set et sts=4 ts=4 tw=80:
