# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
__docformat__ = 'restructuredtext en'
'''

.. _module_mc_remote:

mc_remote / remote execution functions
============================================
The following functions are related to do remote executions over ssh transport.
This for both raw commands and local salt executions.
Those functions are just variations from salt.utils.cloud (which i (kiorky)
also helped to wrote for some parts, like... the remote exec ones :))

This have nice features like:

    - handling interactive passwords
    - using ssh gateways
    - transfering files using different fallback methods
    - running a remote masterless salt installation

'''

import stat
import time
import re
import string
import sys
import logging
import copy
import os
import tempfile
import traceback
import pipes
import salt.utils
import salt.utils.dictupdate
import salt.utils.pycrypto
import salt.utils.vt
import salt.exceptions

_SSH_PASSWORD_PROMP_RE = re.compile(r'(?:.*)[Pp]assword(?: for .*)?:',
                                    re.M | re.U)

_LETTERSDIGITS_RE = re.compile(
    '[^{0}]'.format(string.ascii_letters + string.digits),
    re.M | re.U)
_SH_WRAPPER = '''\
#!/usr/bin/env bash
set -x
{0}
exit ${{?}}
'''
_SALT_CALL_WRAPPER = '''\
#!/usr/bin/env bash
set -x
{salt_call} --retcode-passthrough {outputter} {local} {loglevel}\
        {module_fun} {args}
exit ${?}
'''

TRANSFER_FILE_SCRIPT = '''\
#!/usr/bin/env sh
if [ "x${{TRANSFER_DEBBUG}}" = "x1" ];then
    set -x
fi
ret=1
fmode=$(stat -c "%a" "{1}")
rsync -Pavz -e "ssh -p "{5}" {0}" "{1}" "{3}@{4}":"{2}" && fmode=''
ret=${{?}}
if [ "x${{ret}}" != "x0" ];then
    scp -P "{5}" {0} "{1}" "{3}@{4}":"{2}"
    ret=${{?}}
fi
if [ "x${{ret}}" != "x0" ];then
  echo "put -p \\"{1}\\" \\"{2}\\"" > "{6}"
  sftp  -b "{6}" -P "{5}" {0} "{3}@{4}"
  ret=${{?}}
  rm -f "{6}"
fi
if [ "x${{ret}}" != "x0" ];then
  gzip -ck "{1}" | ssh -p "{5}" {0} "{3}@{4}" 'gzip -d > "{2}"'
  ret=${{?}}
fi
if [ "x${{ret}}" != "x0" ];then
  cat "{1}" | ssh -p "{5}" {0} "{3}@{4}" 'cat > "{2}"'
  ret=${{?}}
fi
if [ "x${{ret}}" = "x0" ] && [ "x${{fmode}}" != "x" ];then
  ssh -p "{5}" {0} "{3}@{4}" "set -x;chmod ${{fmode}} \\"{2}\\""
  ret=${{?}}
fi
exit ${{ret}}
'''

_marker = object()
log = logging.getLogger(__name__)


def _get_ret(**kw):
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
            exec_ret = _get_ret()
        self.exec_ret = exec_ret


class _SSHLoginError(_SSHExecError):
    """."""


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


def _reraise(exc, typ=None, trace=None, message=None):
    '''
    Reraise an exception as somehow another.
    Useful to give information in tracebacks or specialize the exception

    If this is a ssh exception, it will also add information from stdout,
    stderr and collected traceback
    '''
    if not typ:
        typ = type(exc)
    if not message:
        message = "{0}".format(exc)
    eargs = (message,)
    if isinstance(exc, _SSHExecError):
        exec_ret = exc.exec_ret
        for stream in ['stdout', 'stderr']:
            out = exec_ret[stream].strip()
            if not out:
                continue
            if not message.endswith('\n'):
                message += '\n'
            message += '\n'
            message += '{0}:\n'.format(stream.upper())
            message += __salt__['mc_utils.magicstring'](out)
        exec_ret['trace'] = exec_ret['trace'].replace(
            exc.__class__.__name__, typ.__name__)
        eargs = (message, exec_ret)
    raise typ, eargs, trace


class _AbstractSshSession(object):
    def __init__(self, cmd, *a, **kw):
        self._proc = None
        self.cmd = cmd
        if kw.get('quote', False):
            self.cmd = pipes.quote(cmd)
        self.timeout = kw.get('timeout', False)
        self.loop_interval = kw.get('loop_interval', 0.05)
        self.display_ssh_output = kw.get('display_ssh_output', True)
        self.output_loglevel = kw.get('output_loglevel', 'info')
        self._proc = None
        self._pid = -1
        self.stdout = ''
        self.stderr = ''

    @property
    def proc(self):
        if self._proc is None:
            log.debug('Running command: {0!r}'.format(self.cmd))
            self._proc = salt.utils.vt.Terminal(
                self.cmd,
                shell=True,
                log_stdout_level=self.output_loglevel,
                log_stdin_level=self.output_loglevel,
                log_stderr_level=self.output_loglevel,
                stream_stdout=self.display_ssh_output,
                stream_stderr=self.display_ssh_output)
            # let the connexion establish
            time.sleep(self.loop_interval)
        return self._proc

    @property
    def pid(self):
        if self.proc is not None:
            self._pid = self.proc.pid
        return self._pid

    def interact(self, stdout, stderr, cstdout, cstderr):
        raise Exception('not implemented')

    def run(self):
        cmd = self.cmd
        try:
            # handle correctly py26 try/finally
            try:
                try:
                    begin = time.time()
                    # calling the property starts the ssh session
                    while self.proc.has_unread_data:
                        try:
                            self.interact(*self.proc.recv())
                            if (
                                self.timeout
                                and ((time.time() - begin) >= self.timeout)
                            ):
                                raise _SSHLoginError(
                                    'Command timeout({0}s): {1}'.format(
                                        self.timeout, cmd))
                        except KeyboardInterrupt:
                            raise _SSHInterruptError(
                                'SSH session interrupted: ' + cmd)
                    status = 'Command '
                    if self.proc.exitstatus != 0:
                        eklass = _SSHCommandFailed
                        status += 'failed({0})'.format(self.proc.exitstatus)
                    else:
                        eklass = _SSHCommandFinished
                        status += 'finished'
                    status += ': {0}'.format(cmd)
                    raise eklass(status)
                except (salt.utils.vt.TerminalException) as exc:
                    exc = _SSHVtError('VT unhandled error: {0}'.format(exc))
                    trace = traceback.format_exc()
                    exc.exec_ret['trace'] = trace
                    raise
            except (_SSHExecError,) as exc:
                typ, eargs, _trace = sys.exc_info()
                trace = traceback.format_exc()
                if isinstance(exc, _SSHCommandFailed):
                    retcode = self.proc.exitstatus
                elif isinstance(exc, _SSHCommandFinished):
                    retcode = self.proc.exitstatus
                    trace = ''
                elif isinstance(exc, _SSHInterruptError):
                    retcode = 1251
                elif isinstance(exc, _SSHLoginError):
                    retcode = 1252
                elif isinstance(exc, _SSHCommandTimeout):
                    retcode = 1256
                elif isinstance(exc, _SSHExecError):
                    retcode = 1257
                elif isinstance(exc, salt.utils.vt.TerminalException):
                    retcode = 1253
                    trace = exc.exec_ret['trace']
                else:
                    retcode = 1254
                if retcode == 0:
                    return exc.exec_ret
                else:
                    exc.exec_ret.update({'pid': self.pid,
                                         'stdout': self.stdout,
                                         'stderr': self.stderr,
                                         'retcode': retcode,
                                         'trace': trace})
                    _reraise(exc)
        finally:
            if isinstance(self.proc, salt.utils.vt.Terminal):
                self.proc.close(terminate=True, kill=True)


class _SSHPasswordChallenger(_AbstractSshSession):

    def __init__(self, cmd, *a, **kw):
        super(_SSHPasswordChallenger, self).__init__(cmd, *a, **kw)
        self.password = kw.get('password', None)
        self.password_retries = kw.get('password_retries', 3)
        self.login_established = False
        self.sent_password = 0

    def interact(self, cstdout, cstderr):
        '''
        Do the ssh password challenge
        '''
        _s = __salt__
        if not cstdout:
            cstdout = ''
        if not cstderr:
            cstderr = ''
        self.stdout += __salt__['mc_utils.magicstring'](cstdout)
        self.stderr += __salt__['mc_utils.magicstring'](cstderr)
        if (
            cstdout
            and _SSH_PASSWORD_PROMP_RE.search(self.stdout)
            and not self.login_established
        ):
            if self.password and (self.sent_password < self.password_retries):
                self.sent_password += 1
                self.proc.sendline(self.password)
                self.login_established = True
            else:
                raise _SSHLoginError('Login failed: ' + self.cmd)
        # 0.0125 is really too fast on some systems
        time.sleep(self.loop_interval)


def interactive_ssh(cmd, **kw):
    '''
    Establish a ssh connection layer, executes a command, interact.

    This session can can be password interactive and we will by default a
    password challenge and forward the result to the user.

    The session control behavior can be controller by subclassing the
    AbstractSshSession class, see 'interaction_class':
    cmd
        the full ssh command to wrap the execution from
        eg::

            ssh foo.com "ls /"
    quote
        do we force the script to be quoted
    display_ssh_output
        do we send output on the console
    output_loglevel
        log level
    password_retries
        how many retries do we try for the password
    interaction_class
        _AbstractSshSession subclass(not instance)
        (_SSHPasswordChallenger by default)
    timeout
        timeout for command execution

    '''
    # dont use regular named args to support multi layer of forwarded kwargs
    ssh_interaction_class = kw.get('interaction_class', _SSHPasswordChallenger)
    acmd = __salt__['mc_utils.magicstring'](cmd)
    session = ssh_interaction_class(acmd, **kw)
    return session.run()


def _get_ssh_args(**kw):
    '''
    Common ssh args for ssh functions.

    tty
        use a tty (-t)
    key_filename
        ssh key to use
    known_hosts_file
        known host file to use (default to disable)
    host_key_checking
        known host check (default to disable)
    ssh_gateway
        ssh gateway to use
    ssh_gateway_key
        ssh gateway key to use (no password auth for gw)
    ssh_gateway_user
        ssh gateway gateway to use
    ssh_gateway_port
        ssh gateway port to use
    '''
    tty = kw.get('tty', True)
    id_file = '~/.ssh/id_rsa'
    for k in ['~/.ssh/id_rsa', '~/.ssh/id_dsa']:
        k = os.path.expanduser(k)
        if os.path.exists(k):
            id_file = k
            break
    key_filename = kw.get('key_filename', id_file)
    known_hosts_file = kw.get('known_hosts_file', '/dev/null')
    host_key_checking = kw.get('host_key_checking', 'no')
    ssh_gateway = kw.get('ssh_gateway', None)
    ssh_gateway_key = kw.get('ssh_gateway_key', id_file)
    ssh_gateway_user = kw.get('ssh_gateway_user', 'root')
    ssh_gateway_port = kw.get('ssh_gateway_port', 22)
    password = kw.get('password', None)
    ssh_args = []
    if tty:
        # Use double `-t` on the `ssh` script, it's necessary when `sudo` has
        # `requiretty` enforced.
        ssh_args.extend(['-t', '-t'])
    if known_hosts_file != '/dev/null':
        host_key_checking = 'yes'
    ssh_args.extend(['-oStrictHostKeyChecking={0}'.format(host_key_checking),
                     '-oUserKnownHostsFile={0}'.format(known_hosts_file),
                     '-oControlPath=none'])
    if not password:
        # There should never be both a password and an ssh key passed in, so
        ssh_args.extend(['-oPasswordAuthentication=no',
                         '-oChallengeResponseAuthentication=no',
                         '-oPubkeyAuthentication=yes',
                         '-oKbdInteractiveAuthentication=no',
                         '-i {0}'.format(key_filename)])
    if ssh_gateway:
        if ':' in ssh_gateway:
            ssh_gateway, ssh_gateway_port = ssh_gateway.split(':')
        ssh_args.extend([
            # Setup ProxyCommand
            '-oProxyCommand="ssh {0} {1} {2} -i {3}'
            ' {4}@{5} -p {6} nc -q0 %h %p"'
            ''.format(
                # Don't add new hosts to the host key database
                '-oStrictHostKeyChecking=no',
                # Set hosts key database path to /dev/null, i.e., non-existing
                '-oUserKnownHostsFile=/dev/null',
                # Don't re-use the SSH connection. Less failures.
                '-oControlPath=none',
                ssh_gateway_key,
                ssh_gateway_user,
                ssh_gateway,
                ssh_gateway_port)])
        log.info('Using SSH gateway {0}@{1}:{2}'.format(
            ssh_gateway_user, ssh_gateway, ssh_gateway_port))
    return ssh_args


def ssh_transfer_file(host, orig, dest=None, **kw):
    '''
    Transfer files to an host via ssh layer

    This will try then fallback on next transfer method.
    In order we try:
        - rsync
        - scp
        - sftp
        - gzip piped to dest host gunzip
        - cat piped to dest host uncat

    host
        host to tranfer to
    orig
        filepath to transfer
    dest
        where to upload, defaults to orig

    Any extra keywords parameters will by forwarded to:
        _get_ssh_args
            (see doc)
            to mangle connection details
        interactive_ssh(& interaction_class)
            (see doc)
            to interact during ssh session
    '''

    user = kw.get('user', 'root')
    port = kw.get('port', 22)
    if dest is None:
        dest = orig
    kw = copy.deepcopy(kw)
    # as we chain three login,methods, we multiplicate password challenges
    kw['password_retries'] = kw.get('password_retries', 3) * 8
    ssh_args = _get_ssh_args(**kw)
    tmpfile = tempfile.mkstemp()[1]
    # transfer via scp, fallback on scp, fallback on rsync
    ttyfree_sssh_args = ' '.join([a for a in ssh_args if a not in ['-t']])
    sssh_args = ' '.join(ssh_args)
    cmd = TRANSFER_FILE_SCRIPT.format(ttyfree_sssh_args,
                                      orig,
                                      dest,
                                      user,
                                      host,
                                      port,
                                      tmpfile,
                                      sssh_args)
    return interactive_ssh(cmd)


def ssh(host, script, **kw):
    '''
    Executes a script command remotly via ssh
    Attention, if you use a gateway, only key auth is possible on the gw

    host
        host to execute the script on
    tmpdir
        tempfile to upload script to (default to /tmp, this mountpoint
        must not have the -noexec mount flag)
    script
        script or command to execute:
        if the script contains multiple lines
            We put the content in a temporary file, as-is before
            uploading it
        If the script is a filepath
            we upload it as-is
        In other cases
            we wrap it in a simple shell wrapper before uploading

    Even in case of a command, it will be wrapped before execution to ease
    shell quoting

    Any extra keywords parameters will by forwarded to:
        _get_ssh_args
            (see doc)
            to mangle connection details
        interactive_ssh(& interaction_class)
            (see doc)
            to interact during ssh session

    '''
    rand = _LETTERSDIGITS_RE.sub('_', salt.utils.pycrypto.secure_password(64))
    tmpdir = kw.get('tmpdir', tempfile.tempdir or '/tmp')
    dest = os.path.join(tmpdir, '{0}.sh'.format(rand))
    user = kw.get('user', 'root')
    port = kw.get('port', 22)
    script_p, inline_script = script, False
    cret = _get_ret()
    msg = ('Running:\n'
           '{0}'.format(
               __salt__['mc_utils.magicstring'](script))).strip()
    if '\n' in script:
        inline_script = True
    elif script and os.path.exists(script):
        inline_script = False
    else:
        inline_script = True
        script = _SH_WRAPPER.format(script)
    if inline_script:
        tmpfh, script_p = tempfile.mkstemp()
        with salt.utils.fopen(script_p, 'w') as tmpfile:
            tmpfile.write(script)
        os.chmod(script_p, 0755)
    executable = False
    if os.path.exists(script_p):
        fmode = os.stat(script_p)[stat.ST_MODE]
        if all(
            [stat.S_IXUSR & fmode,
             stat.S_IXGRP & fmode,
             stat.S_IXOTH & fmode]
        ):
            executable = True
    transfered = False
    try:
        # transfer via scp, fallback on scp, fallback on rsync
        ssh_args = _get_ssh_args(**kw)
        sssh_args = ' '.join(ssh_args)
        cret = ssh_transfer_file(
            host, script_p, dest=dest, **copy.deepcopy(kw))
        transfered = cret['retcode'] == 0
        # chmod the script to be executable if it is not locally
        # indeed, the transfer script conserve execution permisions
        if not executable:
            cmd = 'ssh {0} {3}@{4} -p {5} chmod +x {2}'.format(
                sssh_args, script_p, dest, user, host, port)
            cret = interactive_ssh(cmd, **copy.deepcopy(kw))
        # Exec the script, eventually
        log.info(msg)
        cmd = 'ssh {0} {3}@{4} -p {5} {2}'.format(
            sssh_args, script_p, dest, user, host, port)
        cret = interactive_ssh(cmd, *kw)
    except (_SSHExecError,) as exc:
        log.error("{0}".format(exc))
        return exc.exec_ret
    finally:
        if inline_script and script_p and os.path.exists(script_p):
            os.remove(script_p)
        # try to delete the remove pass
        if transfered:
            try:
                cmd = ('ssh {0} {3}@{4} -p {5} '
                       '"if [ -f\'{2}\' ];then rm -f \'{2}\';fi'
                       '"').format(
                           sssh_args, script_p, dest, user, host, port)
                cret = interactive_ssh(cmd, **copy.deepcopy(kw))
            except _SSHExecError:
                pass
    return cret


def ssh_retcode(host, script, **kw):
    '''
    Wrapper to ssh_call

    kwargs are forwarded to ssh helper functions !

    returning only the code exist status
    '''
    return ssh(host, script, **kw)['retcode']


def salt_call(host,
              module_fun,
              arg=None,
              kwarg=None,
              outputter='json',
              loglevel='info',
              mode='salt',
              masterless=True,
              *a, **kw):
    '''
    Executes a salt_call call remotely via ssh
    kwargs are forwarded to ssh helper functions !
    '''
    if arg is None:
        arg = []
    elif isinstance(arg, basestring):
        arg = [arg]
    if kwarg is None:
        kwarg = {}
    skwargs = {'outputter': '--out="{0}"'.format(outputter),
               'local': bool(masterless) and '--local' or '',
               'loglevel': '-l{0}'.format(loglevel),
               'module_fun': module_fun,
               'salt_call': mode == 'salt' and 'salt' or 'mastersalt-call',
               'args': arg,
               'kwarg': kwarg}
    script = _SALT_CALL_WRAPPER.format(skwargs)
    return ssh(host, script, *a, **kw)


def sls(host, sls, **kw):
    '''
    Run a state file on an host and fails on error
    kwargs are forwarded to ssh helper functions !
    '''
    return salt_call(host, 'state.sls', arg=[sls])


def highstate(host, sls, **kw):
    '''
    Run an highstate on an host and fails on error
    kwargs are forwarded to ssh helper functions !
    '''
    return salt_call(host, 'state.highstate')
# vim:set et sts=4 ts=4 tw=80:
