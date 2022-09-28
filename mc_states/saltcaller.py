#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
'''

.. _mc_states_saltcaller:

wrappers to salt shell commands
=================================

This is not included in a salt module and isolated to be
picklable and used thorough python multiprocessing as a target


The module has redundant functions with the makina-states codebase but the goal is that it is selfcontained and dependency less.

'''

import shlex
import argparse
import copy

try:
    import cStringIO
except ImportError:
    import io as cStringIO
import os
import pipes
import subprocess
import sys
import six
import time
import traceback
import logging
import fcntl
import datetime
import json


try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False


_marker = object()
NO_RETURN = '__CALLER_NO_RETURN__'
NORETURN_RETCODE = 5
NODATA_RETCODE = 6
NODICT_RETCODE = 7
NO_INNER_DICT_RETCODE = 8
STATE_RET_IS_NOT_A_DICT_RETCODE = 11
STATE_FAILED_RETCODE = 9
TIMEOUT_RETCODE = -666
NO_RETCODE = -668
log = logging.getLogger(__name__)


def json_load(data):
    content = data.replace(' ---ANTLISLASH_N--- ', '\n')
    content = json.loads(content)
    return content


def json_dump(data, pretty=False):
    if pretty:
        content = json.dumps(
            data, indent=4, separators=(',', ': '))
    else:
        content = json.dumps(data)
        content = content.replace('\n', ' ---ANTLISLASH_N--- ')
    return content


def magicstring(thestr):
    '''
    Convert any string to UTF-8 ENCODED one
    '''
    if not HAS_CHARDET:
        return thestr
    seek = False
    if (
        isinstance(thestr, (int, float, long,
                            datetime.date,
                            datetime.time,
                            datetime.datetime))
    ):
        thestr = "{0}".format(thestr)
    if isinstance(thestr, six.text_type):
        try:
            thestr = thestr.encode('utf-8')
        except Exception:
            seek = True
    if seek:
        try:
            detectedenc = chardet.detect(thestr).get('encoding')
        except Exception:
            detectedenc = None
        if detectedenc:
            sdetectedenc = detectedenc.lower()
        else:
            sdetectedenc = ''
        if sdetectedenc.startswith('iso-8859'):
            detectedenc = 'ISO-8859-15'

        found_encodings = [
            'ISO-8859-15', 'TIS-620', 'EUC-KR',
            'EUC-JP', 'SHIFT_JIS', 'GB2312', 'utf-8', 'ascii',
        ]
        if sdetectedenc not in ('utf-8', 'ascii'):
            try:
                if not isinstance(thestr, six.text_type):
                    thestr = thestr.decode(detectedenc)
                thestr = thestr.encode(detectedenc)
            except Exception:
                for idx, i in enumerate(found_encodings):
                    try:
                        if not isinstance(thestr, six.text_type) and detectedenc:
                            thestr = thestr.decode(detectedenc)
                        thestr = thestr.encode(i)
                        break
                    except Exception:
                        if idx == (len(found_encodings) - 1):
                            raise
    if isinstance(thestr, six.text_type):
        thestr = thestr.encode('utf-8')
    thestr = thestr.decode('utf-8').encode('utf-8')
    return thestr


def terminate(process):
    for i in ['terminate', 'kill']:
        try:
            getattr(process, i)()
        except Exception:
            pass


def do_validate_states(data, retcode_passthrough=None, retcode=None):
    if not data:
        return NODATA_RETCODE
    if not isinstance(data, dict):
        return NODICT_RETCODE
    try:
        # if we set rc_passthrough(default)
        # and we got a well known return code, then use it
        rc = int(retcode)
        assert rc in [0, 2] and retcode_passthrough
        return rc
    except AssertionError:
        pass
    # else try to get ourselves if everything did gone well
    for i, rdata in data.items():
        if not isinstance(rdata, dict):
            return NO_INNER_DICT_RETCODE
        for j, statedata in rdata.items():
            if not isinstance(statedata, dict):
                return STATE_RET_IS_NOT_A_DICT_RETCODE
            elif statedata.get('result', None) is False:
                if not retcode_passthrough:
                    return STATE_FAILED_RETCODE
    return 0


def failed(ret, error=None):
    ret['status'] = ret['retcode'] == 0
    if error is not None and not ret['status']:
        ret['error'] = error
    if ret['error']:
        ret['error'] = magicstring(ret['error'])
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
    stdo = non_block_read(process.stdout)
    stde = non_block_read(process.stderr)
    if stdo:
        stdout.write(stdo)
    if stde:
        stderr.write(stde)
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
    return streams['out'], streams['err'], stdo, stde


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
    cli = [magicstring(a) for a in args]
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
    process = None
    try:
        process = subprocess.Popen(
            cli,
            env=env,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        while True:
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
                retcode = process.poll()
                stdout_pos, stderr_pos, stdo, stde = do_process_ios(
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
        if process is not None:
            stdout_pos, stderr_pos, stdo, stde = do_process_ios(
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
        print(format_output_and_error(ret))
    return ret


def complex_json_output_simple(string):
    '''
    Extract json output from stdout (string parse variant)

    if states garbled the stdout, but we still have a result like::

        ...command gargage output...
        {"local": true}

    we will try to remove the starting output and so extract
    the result from the output
    '''
    if not isinstance(string, six.string_types):
        return string
    ret = _marker
    for pos, i in enumerate(string):
        if i == '{':
            try:
                ret = json.loads(string[pos:])
                break
            except ValueError:
                pass
    if ret is _marker:
        raise ValueError('Cant extract json output')
    return ret


def complex_json_output_multilines(string):
    '''
    Extract json output from stdout (lines parse variant)

    if states garbled the stdout, but we still have a result like::

        ...command gargage output...
        {"local": true}

    we will try to remove the starting output and so extract
    the result from the output
    '''
    if not isinstance(string, six.string_types):
        return string
    ret = _marker
    lines = string.splitlines()
    for pos, line in enumerate(lines):
        sline = magicstring(line.strip())
        if sline.startswith('{'):
            try:
                ret = json.loads(''.join([magicstring(a)
                                          for a in lines[pos:]]))
                break
            except ValueError:
                pass
    if ret is _marker:
        raise ValueError('Cant extract json output')
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
         no_retcode_passthrough=None,
         no_quote=None,
         sleep_interval=None,
         local=False,
         out=None,
         no_out=NO_RETURN,
         no_display_ret=None,
         ret_format=None,
         verbose=None,
         env=None):
    if args is None:
        args = []
    if isinstance(args, six.string_types):
        args = shlex.split(args)
    if out is None:
        out = 'json'
    if ret_format is None:
        ret_format = 'json'
    if verbose is None:
        verbose = False
    if not executable:
        executable = 'salt-call'
    if retcode_passthrough is None:
        retcode_passthrough = True
    if no_retcode_passthrough is None:
        no_retcode_passthrough = False
    eargs = []
    if no_retcode_passthrough:
        retcode_passthrough = False
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
              verbose=verbose,
              no_quote=no_quote, sleep_interval=sleep_interval,
              stdin=stdin, stderr=stderr, stdout=stdout)
    decoders = {'json': json_load}
    encoders = {'json': (lambda x: json_dump(x, pretty=True))}
    ret['salt_fun'] = func
    ret['salt_args'] = args
    ret['salt_out'] = None
    if out and out in decoders and ret.get('stdout', ''):
        try:
            dout = None
            try:
                dout = decoders[out](ret['stdout'])
            except (KeyError, ValueError):
                if out == 'json':
                    try:
                        dout = complex_json_output_multilines(
                            ret['stdout'])
                    except (KeyError, ValueError):
                        dout = complex_json_output_simple(
                            ret['stdout'])
                if dout is None:
                    raise
            if isinstance(dout, dict):
                if (
                    validate_states is not False and
                    func in ['state.highstate', 'state.sls']
                ):
                    src = do_validate_states(dout,
                                             retcode_passthrough=retcode_passthrough,
                                             retcode=ret['retcode'])
                    if src != 0 and (ret['retcode'] == 0):
                        ret['retcode'] = src
                if [a for a in dout] == ['local']:
                    dout = dout['local']
            ret['salt_out'] = dout
        except (KeyError, ValueError):
            # no json output is equivalent as a failed call
            ret['retcode'] = NORETURN_RETCODE
            if not ret['error']:
                ret['error'] = ''
            ret['error'] += '\nfailed to decode payload'
    try:
        retcode = int(ret['retcode'])
    except ValueError:
        retcode = 666
    ret['retcode'] = retcode
    if output_queue:
        output_queue.put(ret)
    pid = os.getpid()
    if not no_display_ret:
        eret = ret
        if ret_format in encoders:
            eret = encoders[ret_format](eret)
        print("__SALTCALLER_RETURN_{0}".format(pid))
        print(eret)
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
    parser.add_argument('--no-retcode-passthrough', default=None,
                        action='store_true')
    parser.add_argument('--out', default=None)
    parser.add_argument('-l', '--loglevel')
    parser.add_argument('--timeout', default=None, type=int)
    parser.add_argument('--no-quote', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help=('if set, display command output on console'),
                        default=False)
    parser.add_argument('--no-display-ret',
                        help=('Do not display the full return'
                              ' from process a JSON metadatas'),
                        action='store_true', default=False)
    args = parser.parse_args()
    vopts = vars(args)
    vopts['func'] = vopts['func'][0]
    return call(**vopts)


if __name__ == '__main__' and not os.environ.get('NO_PYEXEC'):
    sys.exit(main()['retcode'])
# vim:set et sts=4 ts=4 tw=0:
