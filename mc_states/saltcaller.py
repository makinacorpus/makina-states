#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
'''

.. _mc_states_saltcaller

wrappers to salt shell commands
=================================

This is not included in a salt module and isolated to be
picklable and used thorough python multiprocessing as a target

'''

import argparse
import copy
import cStringIO
import os
import pipes
import subprocess
import sys
import time
import traceback
import logging
import fcntl

from salt.utils import vt

from mc_states import api
from mc_states.modules import mc_dumper


NO_RETURN = '__CALLER_NO_RETURN__'
TIMEOUT_RETCODE = -666
VT_ERROR_RETCODE = -667
NO_RETCODE = -668
log = logging.getLogger(__name__)


def terminate(process):
    if isinstance(process, vt.Terminal):
        process.close(terminate=True, kill=True)
    else:
        for i in ['terminate', 'kill']:
            try:
                getattr(process, i)()
            except Exception:
                pass


def validate_states(data):
    if not data:
        return 1
    if not isinstance(data, dict):
        return 1
    for i, rdata in data.items():
        if not isinstance(rdata, dict):
            return 1
        for j, statedata in rdata.items():
            if statedata.get('result', None) is False:
                return 1


def failed(ret, error=None):
    ret['status'] = ret['retcode'] == 0
    if error is not None and not ret['status']:
        ret['error'] = error
    if ret['error']:
        ret['error'] = api.magicstring(ret['error'])
    return ret


def non_block_read(output):
    try:
        fd = output.fileno()
    except ValueError:
        return ""
    else:
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        try:
            return output.read()
        except Exception:
            return ""


def do_process_ios(process,
                   verbose=False,
                   output_out=sys.stdout,
                   output_err=sys.stderr,
                   stdout_pos=None,
                   stderr_pos=None,
                   stdout=None,
                   stderr=None):
    if stdout is None:
        stdout = cStringIO.StringIO()
    if stderr is None:
        stderr = cStringIO.StringIO()
    streams = {'out': stdout_pos, 'err': stderr_pos}
    if isinstance(process, vt.Terminal):
        stdout.truncate(0)
        stderr.seek(0)
        stdout.write(process.stream_stdout.getvalue())
        stderr.write(process.stream_stderr.getvalue())
    else:
        stdout.write(non_block_read(process.stdout))
        stderr.write(non_block_read(process.stderr))
    for k, val, out in (
        ('out', stdout.getvalue(), output_out),
        ('err', stderr.getvalue(), output_err),
    ):
        if not val:
            continue
        pos = streams[k]
        npos = len(val) - 1
        if val and ((pos == 0) or (npos != pos)):
            if verbose:
                out.write(val[pos:])
            streams[k] = npos
    return stdout_pos, stderr_pos


def format_error(ret):
    '''
    To avoid large memory usage, only lazy format errors on demand
    '''
    return (''
            '__SALTCALLER_ERROR_{pid}\n'
            '{error}\n'
            '__SALTCALLER_END_ERROR_{pid}\n'
            '').format(**ret)


def format_output(ret):
    '''
    To avoid large memory usage, only lazy format errors on demand
    '''
    return (''
            '__SALTCALLER_STDERR_{pid}\n'
            '{stderr}\n'
            '__SALTCALLER_END_STDERR_{pid}\n'
            '__SALTCALLER_STDOUT_{pid}\n'
            '{stdout}\n'
            '__SALTCALLER_END_STDOUT_{pid}\n'
            '').format(**ret)


def format_output_and_error(ret):
    '''
    To avoid large memory usage, only lazy format errors on demand
    '''
    return format_error(ret) + format_output(ret)


def cmd(args,
        timeout=None,
        stdin=None,
        stdout=None,
        sleep_interval=None,
        stderr=None,
        use_vt=None,
        no_quote=None,
        verbose=None,
        env=None):
    if not sleep_interval:
        sleep_interval = 0.04
    if no_quote is None:
        no_quote = False
    if not env:
        env = {}
    environ = copy.deepcopy(os.environ)
    environ.update(copy.deepcopy(env))
    now = time.time()
    cli = [api.magicstring(a) for a in args]
    ospid = pid = os.getpid()
    if not no_quote:
        cli = [pipes.quote(a) for a in cli]
    retcode, force_retcode = None, None
    stdout_pos, stderr_pos = None, None
    error = None
    if stdout is None:
        stdout = cStringIO.StringIO()
    if stderr is None:
        stderr = cStringIO.StringIO()
    try:
        if use_vt:
            process = vt.Terminal(
                args,
                shell=True,
                cwd=os.getcwd(),
                preexec_fn=None,
                env=env,
                stream_stdout=cStringIO.StringIO(),
                stream_stderr=cStringIO.StringIO())
        else:
            process = subprocess.Popen(
                cli,
                env=env,
                stdin=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        while True:
            if isinstance(process, vt.Terminal) and process.has_unread_data:
                process.recv()
            if pid == ospid or pid is None:
                pid = process.pid
            if timeout is not None and (time.time() >= now + timeout):
                terminate(process)
                error = (
                    'job too long to execute, process was killed\n'
                    '  {0}'
                ).format(cli)
                force_retcode = TIMEOUT_RETCODE
            else:
                if isinstance(process, vt.Terminal):
                    retcode = process.exitstatus
                    if retcode is None and force_retcode is not None:
                        force_retcode = VT_ERROR_RETCODE
                else:
                    retcode = process.poll()
                stdout_pos, stderr_pos = do_process_ios(
                    process, verbose=verbose,
                    stdout_pos=stdout_pos, stderr_pos=stderr_pos,
                    stdout=stdout, stderr=stderr)
            time.sleep(0.04)
            if retcode is not None or force_retcode is not None:
                break
    except (KeyboardInterrupt, Exception) as exc:
        trace = traceback.format_exc()
        print(trace)
        try:
            terminate(process)
        except UnboundLocalError:
            pass
        raise exc
    finally:
        stdout_pos, stderr_pos = do_process_ios(
            process, verbose=verbose,
            stdout_pos=stdout_pos, stderr_pos=stderr_pos,
            stdout=stdout, stderr=stderr)
        try:
            terminate(process)
        except UnboundLocalError:
            pass
    if force_retcode is not None:
        retcode = force_retcode
    if retcode is None:
        retcode = NO_RETCODE
    if retcode != 0 and not error:
        error = 'program error, check std streams'
    retcode = force_retcode or retcode
    ret = {'retcode': retcode,
           'status': None,
           'error': None,
           'pid': pid,
           'cli': ' '.join(cli),
           'stdout': stdout.getvalue(),
           'stderr': stderr.getvalue()}
    failed(ret, error=error)
    if verbose:
        # repeat stderr to avoid missing stuff
        # drowned  in the middle even in VT mode
        print(format_output_and_error(ret))
    return ret


def call(func,
         executable=None,
         args=None,
         loglevel=None,
         config_dir=None,
         stdin=None,
         stdout=None,
         stderr=None,
         timeout=None,
         output_queue=None,
         validate_states=None,
         retcode_passthrough=None,
         no_quote=None,
         sleep_interval=None,
         local=False,
         out=None,
         no_out=NO_RETURN,
         use_vt=None,
         no_display_ret=None,
         ret_format=None,
         verbose=None,
         env=None):
    if verbose is None:
        verbose = False
    if not executable:
        executable = 'salt-call'
    eargs = []
    for test, argpart in [
        (True, [executable]),
        (local, ['--local']),
        (retcode_passthrough, ['--retcode-passthrough']),
        (config_dir, ['-c', config_dir]),
        (loglevel, ['-l', loglevel]),
        (out, ['--out', out]),
        (True, [func] + args)
    ]:
        if test:
            eargs.extend(argpart)
    ret = cmd(args=eargs, env=env, timeout=timeout,
              use_vt=use_vt, verbose=verbose,
              no_quote=no_quote, sleep_interval=sleep_interval,
              stdin=stdin, stderr=stderr, stdout=stdout)
    decoders = {'json': mc_dumper.json_load,
                'yaml': mc_dumper.yaml_load}
    encoders = {
        'json': (
            lambda x: mc_dumper.json_dump(
                x, pretty=True)),
        'yaml': (
            lambda x: mc_dumper.yaml_dump(
                x, flow=False))}
    ret['salt_fun'] = func
    ret['salt_args'] = args
    ret['salt_out'] = None
    if out and out in decoders and ret['retcode'] == 0:
        try:
            out = decoders[out](ret['stdout'])
            if (
                validate_states is not False and
                func in ['state.highstate', 'state.sls']
            ):
                validate_states(out)
            if isinstance(out, dict):
                if [a for a in out] == ['local']:
                    out = out['local']
            ret['salt_out'] = out
        except (KeyError, ValueError):
            # no json output is equivalent as a failed call
            ret['retcode'] = 1
            if not ret['error']:
                ret['error'] = ''
            ret['error'] += '\nfailed to decode payload'
    if ret_format in encoders:
        ret = encoders[ret_format](ret)
    try:
        retcode = int(ret['retcode'])
    except ValueError:
        retcode = 666
    ret['retcode'] = retcode
    if output_queue:
        output_queue.put(ret)
    pid = os.getpid()
    if not no_display_ret:
        print("__SALTCALLER_RETURN_{0}".format(pid))
        print(mc_dumper.json_dump(ret, pretty=True))
        print("__SALTCALLER_END_RETURN_{0}".format(pid))
    return ret


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('func', nargs=1,
                        help='salt function to call')
    parser.add_argument('args',
                        nargs=argparse.REMAINDER,
                        help=('function arguments as you would use'
                              ' on cli to call salt-call'))
    parser.add_argument('--validate-states',
                        help=('for states function (sls, highstate),'
                              ' exist with non-0 status in case of errors'),
                        default=False, action='store_true')
    parser.add_argument('--executable')
    parser.add_argument('-c', '--config-dir')
    parser.add_argument('--ret-format')
    parser.add_argument('--local',
                        help='use --local when calling salt-call',
                        action='store_true')
    parser.add_argument('--retcode-passthrough', default=None,
                        action='store_true')
    parser.add_argument('--out', default=None)
    parser.add_argument('-l', '--loglevel')
    parser.add_argument('--timeout', default=None, type=int)
    parser.add_argument('--no-quote', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help=('if set, display command output on console'),
                        default=False)
    parser.add_argument('--use-vt', action='store_true',
                        help=('if set, streams the salt-call'
                              ' process input/output to console while '
                              'executing in real time and not at the end'),
                        default=False)
    parser.add_argument('--no-display-ret',
                        help=('Do not display the full return'
                              ' from process a JSON metadatas'),
                        action='store_true', default=False)
    args = parser.parse_args()
    vopts = vars(args)
    vopts['func'] = vopts['func'][0]
    return call(**vopts)


if __name__ == '__main__':
    sys.exit(main()['retcode'])
# vim:set et sts=4 ts=4 tw=0:
