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
    - running salt-call over remote (even masterless) salt installations

If this module gains salt core, there are some small makina-states deps:

    - mc_states.renderers.lyaml
    - mc_states.modules.mc_utils.magicstring (which needs chardet)

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
import salt.loader
import salt.minion
import salt.exceptions
import salt.utils
import salt.utils.args
import salt.utils.dictupdate
import salt.utils.pycrypto
import salt.utils.vt
import salt.exceptions
from salt.ext.six import string_types, integer_types
import salt.ext.six as six


_SSH_PASSWORD_PROMP_RE = re.compile('(([Pp]assword(: ?for.*)?:))',
                                    re.M | re.U)

RESULT_SEP = '----- SALTCALL RESULT {0}'
_SKIP_LINE_RE = re.compile(r"\+  *(touch|cp|cat|rm|exit|['][\]]) ",
                           re.U | re.X)
_SSH_IDENT_RE = re.compile(
    '[^@]+@(?P<host>[^\']+)[ ]*\'s password:',
    re.M | re.U)
_LETTERSDIGITS_RE = re.compile(
    '[^{0}]'.format(string.ascii_letters + string.digits),
    re.M | re.U)


_SH_WRAPPER = '''\
#!/usr/bin/env bash
if [ "x{sh_wrapper_debug}" != "x" ];then set -x;fi
{0}
exit ${{?}}
'''
_SALT_CALL_WRAPPER = '''\
#!/usr/bin/env bash
if [ "x{sh_wrapper_debug}" != "x" ];then set -x;fi
touch {quoted_outfile}
chmod 700 {quoted_outfile}
if [ ! -e {quoted_outfile} ];then
    exit 666
fi
{salt_call_bin} --retcode-passthrough {outputter} {local} {loglevel}\\
     --out-file="{outfile}" \\
     {fun} {sarg}
ret=${{?}}
echo {result_sep}
if [ -e {quoted_outfile} ];then
    cat {quoted_outfile}
    rm -f ${quoted_outfile}
fi
exit ${{ret}}
'''

TRANSFER_FILE_SCRIPT = '''\
#!/usr/bin/env sh
rsync_opts="-az"
sftp_opts="-qqq"
scp_opts="-qqq"
if [ "x{sh_wrapper_debug}" != "x" ];then
    set -x
    rsync_opts="${{rsync_opts}}vP"
    sftp_opts=""
    scp_opts=""
fi
ret=1
if ! test -e "{orig}";then
    echo "Unexisting script file: {orig}"
    exit 1
fi
fmode=$(stat -c "%a" "{orig}")
rsync ${{rsync_opts}} \\
        -e "ssh -p "{port}" {quoted_ssh_args}"\\
        "{orig}" "{user}@{host}":"{dest}"\\
        && fmode=''
ret=${{?}}
if [ "x${{ret}}" != "x0" ];then
    scp ${{scp_opts}} -P "{port}" {ttyfree_ssh_args}\\
            "{orig}" "{user}@{host}":"{dest}"
    ret=${{?}}
fi
if [ "x${{ret}}" != "x0" ];then
  echo "put -p \\"{orig}\\" \\"{dest}\\"" > "{tmpfile}"
  if [ "x{sh_wrapper_debug}" != "x" ];then
      sftp ${{sftp_opts}} -b "{tmpfile}" -P "{port}"\\
              {ttyfree_ssh_args} "{user}@{host}"
  else
      sftp ${{sftp_opts}} -b "{tmpfile}" -P "{port}"\\
              {ttyfree_ssh_args} "{user}@{host}" 1>/dev/null 2>&1
  fi
  ret=${{?}}
  rm -f "{tmpfile}"
fi
if [ "x${{ret}}" != "x0" ];then
  gzip -ck "{orig}" \\
          | ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
          'gzip -d > "{dest}"'
  ret=${{?}}
fi
if [ "x${{ret}}" != "x0" ];then
  cat "{orig}" \\
          | ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
          'cat > "{dest}"'
  ret=${{?}}
fi
if [ "x${{ret}}" = "x0" ] && [ "x${{fmode}}" != "x" ];then
 if [ "x{sh_wrapper_debug}" != "x" ];then
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
       "set -x;chmod ${{fmode}} \\"{dest}\\""
 else
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
      "chmod ${{fmode}} \\"{dest}\\""
 fi
  ret=${{?}}
fi
exit ${{ret}}
'''

TRANSFER_DIR_SCRIPT = '''\
#!/usr/bin/env sh
rsync_opts="-az"
sftp_opts="-qqq"
scp_opts="-qqq"
if [ "x{sh_wrapper_debug}" != "x" ];then
    set -x
    rsync_opts="${{rsync_opts}}vP"
    sftp_opts=""
    scp_opts=""
fi
ret=1
if ! test -e "{orig}";then
    echo "Unexisting script file: {orig}"
    exit 1
fi
fmode=$(stat -c "%a" "{orig}")
rsync ${{rsync_opts}} \\
        -e "ssh -p "{port}" {quoted_ssh_args}"\\
        "{corig}" "{user}@{host}":"{cdest}"\\
        && fmode=''
ret=${{?}}
if [ "x${{ret}}" != "x0" ];then
    scp -r ${{scp_opts}} -P "{port}" {ttyfree_ssh_args}\\
            "{orig}" "{user}@{host}":"{dest}"
    ret=${{?}}
fi
if [ "x${{ret}}" != "x0" ];then
  echo "put -p \\"{orig}\\" \\"{dest}\\"" > "{tmpfile}"
  if [ "x{sh_wrapper_debug}" != "x" ];then
      sftp -r ${{sftp_opts}} -b "{tmpfile}" -P "{port}"\\
              {ttyfree_ssh_args} "{user}@{host}"
  else
      sftp -r ${{sftp_opts}} -b "{tmpfile}" -P "{port}"\\
              {ttyfree_ssh_args} "{user}@{host}" 1>/dev/null 2>&1
  fi
  ret=${{?}}
  rm -f "{tmpfile}"
fi
if [ "x${{ret}}" = "x0" ] && [ "x${{fmode}}" != "x" ];then
 if [ "x{sh_wrapper_debug}" != "x" ];then
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
       "set -x;chmod ${{fmode}} \\"{dest}\\""
 else
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
      "chmod ${{fmode}} \\"{dest}\\""
 fi
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


def log_enabled_for(lvl='info', name=None):
    if isinstance(lvl, string_types):
        lvl = lvl.upper()
    if isinstance(name, logging.Logger):
        logger = name
    if isinstance(name, string_types):
        logger = logging.getLogger(name)
    else:
        logger = logging.root
    effective_lvl = 0
    while logger:
        for hdlr in logger.handlers:
            effective_lvl = hdlr.level
            break
        if not logger.propagate:
            logger = None
        else:
            logger = logger.parent
    try:
        loglevel = int(logging._levelNames.get(lvl, 0))
    except Exception:
        loglevel = 0
    return loglevel >= effective_lvl


def _mangle_kw_for_script(kw=None):
    if kw is None:
        kw = {}
    kw = copy.deepcopy(kw)
    if isinstance(kw, dict):
        for k in [a for a in kw if a.startswith('__')]:
            kw.pop(a, None)
        # add shell debug
        kw.setdefault('sh_wrapper_debug', '')
        if log_enabled_for('debug'):
            kw['sh_wrapper_debug'] = 1
    return kw


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
        self.output_loglevel = kw.get('vt_loglevel',
                                      kw.get('output_loglevel',
                                             'info'))
        self._proc = None
        self._pid = -1
        self.stdout = ''
        self.stderr = ''
        # raw encoded chunks
        self.out_chunks = []
        self.err_chunks = []
        # utf8 encoded chunks
        self.safe_out_chunks = []
        self.safe_err_chunks = []
        self.chunks = 0

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

    def interact(self):
        raise Exception('not implemented')

    def run(self):
        cmd = self.cmd
        try:
            # handle correctly py26 try/finally
            try:
                try:
                    begin = time.time()
                    # calling the property starts the ssh session
                    while self.proc.isalive() or self.proc.has_unread_data:
                        try:
                            cout, cerr =  self.proc.recv()
                            if not cout:
                                cout = ''
                            if not cerr:
                                cerr = ''
                            if cout:
                                scout = __salt__['mc_utils.magicstring'](cout)
                                self.stdout += scout
                                self.out_chunks.append(cout)
                                self.safe_out_chunks.append(scout)
                            if cerr:
                                scerr = __salt__['mc_utils.magicstring'](cerr)
                                self.stderr += scerr
                                self.err_chunks.append(cerr)
                                self.safe_err_chunks.append(scerr)
                            cur_len = (len(self.err_chunks)
                                       + len(self.out_chunks))
                            if cur_len > self.chunks:
                                self.chunks = cur_len
                                self.interact()
                            if (
                                self.timeout
                                and ((time.time() - begin) >= self.timeout)
                            ):
                                raise _SSHTimeoutError(
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
                elif isinstance(exc, _SSHTimeoutError):
                    retcode = 1257
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
                flows = {'stdout': self.stdout, 'stderr': self.stderr}
                if retcode != 1252:
                    # if command failed not for a login reason
                    # stip out the password challenges lines
                    for flow in [a for a in flows]:
                        vflow = flows[flow]
                        if not vflow:
                            continue
                        lines = []
                        for line in vflow.splitlines():
                            if not _SSH_IDENT_RE.match(line):
                                lines.append(line)
                        flows[flow] = '\n'.join(lines)
                exc.exec_ret.update({'pid': self.pid,
                                     'retcode': retcode,
                                     'trace': trace})
                exc.exec_ret.update(flows)
                if retcode == 0:
                    return exc.exec_ret
                else:
                    _reraise(exc, trace=_trace)
        finally:
            if isinstance(self.proc, salt.utils.vt.Terminal):
                self.proc.close(terminate=True, kill=True)


class _SSHPasswordChallenger(_AbstractSshSession):

    def __init__(self, cmd, *a, **kw):
        super(_SSHPasswordChallenger, self).__init__(cmd, *a, **kw)
        self.password = kw.get('password', None)
        self.password_retries = kw.get('password_retries', 3)
        self.sent_password = 0
        self.pwd_index = 0

    def interact(self):
        '''
        Do the ssh password challenge
        '''
        _s = __salt__
        occ = _SSH_PASSWORD_PROMP_RE.findall(self.stdout)
        self.cur_len = len(self.safe_out_chunks)
        if occ:
            if self.password:
                password_challenges = len(occ)
                if (
                    (password_challenges > self.sent_password)
                    and (self.sent_password < self.password_retries)
                ):
                    self.sent_password += 1
                    host = ''
                    m = _SSH_IDENT_RE.search(self.stdout)
                    if m:
                        host = ' on {0}'.format(m.groupdict()['host'])
                    msg = 'Sending SSH password ({0}){1}'.format(
                        self.sent_password, host)
                    log.debug(msg)
                    self.proc.sendline(self.password)
                    self.pwd_index = self.cur_len - 1
                    test_establish = False
                else:
                    test_establish = True
                if test_establish:
                    if all([
                        [a > 1 for a in [password_challenges,
                                         self.sent_password]]
                        + [password_challenges == self.sent_password]
                    ]):
                        after_last_challenge_buf = ''.join(
                            self.safe_out_chunks[self.pwd_index:])
                        if after_last_challenge_buf.count('\n') > 0:
                            log.debug('SSH connection established')
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
                     '-oLogLevel=QUIET',
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

        ssh_gateway_args = [
            # Don't add new hosts to the host key database
            '-oStrictHostKeyChecking=no',
            # Set hosts key database path to /dev/null
            '-oUserKnownHostsFile={0}'.format(known_hosts_file),
            # Don't re-use the SSH connection. Less failures.
            '-oControlPath=none',
            '-oPasswordAuthentication=no',
            '-oChallengeResponseAuthentication=no',
            '-oPubkeyAuthentication=yes',
            '-oKbdInteractiveAuthentication=no',
            '-oLogLevel=QUIET']
        ssh_args.extend([
            # Setup ProxyCommand
            '-oProxyCommand="ssh {0} -i {1}'
            ' {2}@{3} -p {4} nc -q0 %h %p"'
            ''.format(
                ' '.join(ssh_gateway_args),
                ssh_gateway_key,
                ssh_gateway_user,
                ssh_gateway,
                ssh_gateway_port)])
        log.debug('Using SSH gateway {0}@{1}:{2}'.format(
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
    vt_loglevel
        vt loglevel

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
    _ssh_args = _get_ssh_args(**kw)
    tmpfile = tempfile.mkstemp()[1]
    # transfer via scp, fallback on scp, fallback on rsync
    ttyfree_ssh_args = ' '.join([a for a in _ssh_args if a not in ['-t']])
    quoted_ssh_args = ' '.join([a.replace('"', '\\"')
                                for a in _ssh_args if a not in ['-t']])
    ssh_args = ' '.join(_ssh_args)
    cmd = TRANSFER_FILE_SCRIPT.format(
        **_mangle_kw_for_script({
            'ttyfree_ssh_args': ttyfree_ssh_args,
            'quoted_ssh_args': quoted_ssh_args,
            'orig': orig,
            'dest': dest,
            'user': user,
            'host': host,
            'port': port,
            'tmpfile': tmpfile,
            'ssh_args': ssh_args}))
    return interactive_ssh(cmd, **kw)


def ssh_transfer_dir(host, orig, dest=None, **kw):
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
    vt_loglevel
        vt loglevel

    Any extra keywords parameters will by forwarded to:
        _get_ssh_args
            (see doc)
            to mangle connection details
        interactive_ssh(& interaction_class)
            (see doc)
            to interact during ssh session
    '''

    append_slashes = kw.setdefault('append_slashes', True)
    corig, cdest = orig, dest
    if append_slashes:
        if not orig.endswith('/'):
            corig = orig + '/'
        if not dest.endswith('/'):
            cdest = dest + '/'
    user = kw.get('user', 'root')
    port = kw.get('port', 22)
    if dest is None:
        dest = orig
    kw = copy.deepcopy(kw)
    # as we chain three login,methods, we multiplicate password challenges
    kw['password_retries'] = kw.get('password_retries', 3) * 8
    _ssh_args = _get_ssh_args(**kw)
    tmpfile = tempfile.mkstemp()[1]
    # transfer via scp, fallback on scp, fallback on rsync
    ttyfree_ssh_args = ' '.join([a for a in _ssh_args if a not in ['-t']])
    quoted_ssh_args = ' '.join([a.replace('"', '\\"')
                                for a in _ssh_args if a not in ['-t']])
    ssh_args = ' '.join(_ssh_args)
    cmd = TRANSFER_DIR_SCRIPT.format(
        **_mangle_kw_for_script({
            'ttyfree_ssh_args': ttyfree_ssh_args,
            'quoted_ssh_args': quoted_ssh_args,
            'corig': corig,
            'cdest': cdest,
            'orig': orig,
            'dest': dest,
            'user': user,
            'host': host,
            'port': port,
            'tmpfile': tmpfile,
            'ssh_args': ssh_args}))
    return interactive_ssh(cmd, **kw)


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
    vt_loglevel
        loglevel to use for vt

    Even in case of a command, it will be wrapped before execution to ease
    shell quoting

    Any extra keywords parameters will by forwarded to:
        _get_ssh_args
            (see doc)
            to mangle connection details
        interactive_ssh(& interaction_class)
            (see doc)
            to interact during ssh session

    CLI Examples::

        salt-call mc_remote.ssh foo.net ssh_gateway=127.0.0.1 port=40007 \\
                "cat /etc/hostname" user=mytest password=secret

        salt-call mc_remote.ssh foo.net \\
                "cat /etc/hostname"

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
        script = _SH_WRAPPER.format(script, **_mangle_kw_for_script(kw))
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
            cmd = 'ssh {0} "{3}@{4}" -p "{5}" "chmod +x \\{2}\\"'.format(
                sssh_args, script_p, dest, user, host, port)
            cret = interactive_ssh(cmd, **copy.deepcopy(kw))
        # Exec the script, eventually
        if kw.get('show_running_cmd', True):
            log.info(msg)
        cmd = 'ssh {0} "{3}@{4}" -p "{5}" "{2}"'.format(
            sssh_args, script_p, dest, user, host, port)
        cret = interactive_ssh(cmd, **kw)
    except (_SSHExecError,) as exc:
        log.error("{0}".format(exc))
        cret = exc.exec_ret
    finally:
        if inline_script and script_p and os.path.exists(script_p):
            os.remove(script_p)
        # try to delete the remove pass
        if transfered:
            try:
                cmd = ('ssh {0} "{3}@{4}" -p "{5}" '
                       '"'
                       'if [ -f\"{2}\" ];then rm -f \"{2}\";fi'
                       '"').format(
                           sssh_args, script_p, dest, user, host, port)
                interactive_ssh(cmd, **copy.deepcopy(kw))
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


def yamldump_arg(arg, default_flow_style=True, line_break='\n', strip=True):
    '''
    yaml.safe_dump the arg
    This is the counterpart of salt.utils.args.yamlify_arg
    '''
    original_arg = arg
    try:
        # Explicit late import to avoid circular import. DO NOT MOVE THIS.
        from salt.utils import yamldumper
        import yaml
        arg = yaml.dump(arg,
                        line_break=line_break,
                        default_flow_style=default_flow_style,
                        Dumper=yamldumper.SafeOrderedDumper)
    except Exception:
        # In case anything goes wrong...
        arg = original_arg
    if strip and isinstance(arg, (six.text_type, six.string_types)):
        if arg.endswith('...\n'):
            arg = arg[:-4]
        if arg.endswith('\n'):
            while arg and arg.endswith('\n'):
                arg = arg[:-1]
    return arg


def salt_call(host,
              fun=None,
              arg=None,
              kwarg=None,
              outputter='json',
              transformer=None,
              unparse=True,
              loglevel='info',
              salt_call_bin='salt-call',
              masterless=True,
              minion_id='local',
              salt_call_script=None,
              strip_out=None,
              *args,
              **kw):
    '''
    Executes a salt_call call remotely via ssh

    fun
        saltcall function to call
    arg
        args for the saltcall function
    kwarg
        kwargs for the saltcall function
    outputter
        outputter for the saltcall return
    transformer
        outputter used to unparse the value returned from the call
    unparse
        unserialise the return and tries to
        split out the local result from
        regular salt call
    loglevel
        loglevel to use
    vt_loglevel
        loglevel to use for vt
    salt_call_bin
        binary to run
    masterless
        do we run masterless (--local)
    salt_call_script
        override default salt call wrapper shell script
    args
        are appended to arg as arguments to the called salt function
    kwargs
        They are forwarded to ssh helper functions !

    CLI Examples::

        salt-call --local mc_remote.salt_call \\
                foo.net test.ping

        salt-call --local mc_remote.salt_call \\
                foo.net cmd.run \\
                'for i in $(seq 5);do echo $i;sleep 1;done' \\
                kwarg='{use_vt: True, python_shell: True, user: ubuntu}' \\
                ssh_gateway=127.0.0.1 port=40007

        salt-call --local mc_remote.salt_call \\
                foo.net cmd.run \\
                'for i in $(seq 2);do echo $i;sleep 1;done;echo é' \\
                kwarg='{use_vt: True, python_shell: True, user: ubuntu}' \\
                outputter=yaml

        salt-call --local mc_remote.salt_call \\
                foo.net cmd.run \\
                'for i in $(seq 2);do echo $i;sleep 1;done;echo é' \\
                kwarg='{use_vt: True, python_shell: True, user: ubuntu}' \\
                unparse=False outputter=yaml

    '''
    vt_lvl = kw.setdefault('vt_loglevel', 'warning')
    lvl = kw.setdefault('loglevel', __opts__.get('log_level', 'warning'))
    sc, dso = False, False
    if vt_lvl in ['info', 'debug', 'trace']:
        dso = True
    if lvl in ['info', 'debug', 'trace']:
        dso = True
    if lvl in ['debug', 'trace']:
        sc = True
    kw.setdefault('display_ssh_output', dso)
    kw.setdefault('show_running_cmd', sc)
    if arg is None:
        arg = []
    if not args:
        args = []
    if not isinstance(arg, (list, tuple)):
        arg = [arg]
    else:
        arg = [a for a in arg]
    if isinstance(salt_call_script, string_types):
        try:
            if os.path.exists(salt_call_script):
                with open(salt_call_script) as fic:
                    salt_call_script = fic.read()
        except Exception:
            salt_call_script = None
    if not salt_call_script:
        salt_call_script = _SALT_CALL_WRAPPER
    if fun is not None:
        if not isinstance(fun, string_types):
            raise ValueError('fun must be a string: {0}'.format(fun))
        elif ' ' in fun:
            raise ValueError('fun must only be the '
                             'function (state.fun): {0}'.format(fun))
    arg += [a for a in args]
    if kwarg is None:
        kwarg = {}
    if not isinstance(arg, list):
        raise ValueError('arg must be a list')
    if not isinstance(kwarg, dict):
        raise ValueError('kwarg must be a dict')
    kwarg['__kwarg__'] = True
    arg.append(kwarg)
    arg, kwarg = salt.utils.args.parse_input(arg, condition=False)
    sarg = ''
    for i in arg:
        try:
            if isinstance(i, (six.text_type, six.string_types)):
                i = __salt__['mc_utils.magicstring'](i)
            if i is None:
                val = 'null'
            elif not isinstance(i, (string_types,
                                    integer_types,
                                    long,
                                    complex,
                                    bytearray,
                                    float)):
                pass
            else:
                val = yamldump_arg(i)
            val = ' {0}'.format(pipes.quote(val))
            sarg += val
        except Exception:
            try:
                raise ValueError('Cannot serialize {0}'.format(arg))
            except Exception:
                raise ValueError(u'Cannot serialize {0}'.format(arg))
    for k, i in kwarg.items():
        try:
            if isinstance(i, (six.text_type, six.string_types)):
                i = __salt__['mc_utils.magicstring'](i)
            val = yamldump_arg(i)
            sarg += ' {0}={1}'.format(pipes.quote(k), pipes.quote(val))
        except Exception:
            try:
                raise ValueError('Cannot serialize {0}'.format(arg))
            except Exception:
                raise ValueError(u'Cannot serialize {0}'.format(arg))
    rand = _LETTERSDIGITS_RE.sub('_', salt.utils.pycrypto.secure_password(64))
    tmpdir = kw.get('tmpdir', tempfile.tempdir or '/tmp')
    outfile = os.path.join(tmpdir, '{0}.out'.format(rand))
    result_sep = RESULT_SEP.format(outfile)
    sh_wrapper_debug = kw.get('sh_wrapper_debug', '')
    if not kw.get('vt_loglevel'):
        kw['vt_loglevel'] = loglevel
    skwargs = _mangle_kw_for_script({
        'outputter': '--out="{0}"'.format(outputter),
        'local': bool(masterless) and '--local' or '',
        'sh_wrapper_debug': sh_wrapper_debug,
        'loglevel': '-l{0}'.format(loglevel),
        'vt_loglevel': '-l{0}'.format(kw['vt_loglevel']),
        'salt_call_bin': salt_call_bin,
        'salt_call_script': salt_call_script,
        'outfile': outfile,
        'quoted_outfile': pipes.quote(outfile),
        'result_sep': pipes.quote(result_sep),
        'fun': fun,
        'arg': arg,
        'kwarg': kwarg,
        'sarg': sarg})
    script = salt_call_script.format(**skwargs)
    ret = ssh(host, script, **kw)
    ret['result_type'] = outputter
    ret['raw_result'] = 'NO RETURN FROM {0}'.format(outfile)
    if ret['stdout']:
        collect, result = False, ''
        for line in ret['stdout'].splitlines():
            skip_collect = False
            if collect:
                if sh_wrapper_debug:
                    skip_collect = _SKIP_LINE_RE.search(line)
                if not skip_collect:
                    result += line
                    result += "\n"
            if line.startswith(result_sep):
                collect = True
        ret['raw_result'] = ret['result'] = result
    ret['transformer'] = None
    ret['unparser'] = None
    if unparse:
        renderers = salt.loader.render(__opts__, __salt__)
        outputters = salt.loader.outputters(__opts__)
        rtype = ret['result_type']
        if transformer is None:
            transformer = rtype
        transformer = {'yaml': 'lyaml',
                       'lyaml': 'lyaml',
                       'highstate': 'highstate',
                       'nested': 'nested',
                       'json': 'json'}.get(transformer, 'noop')
        unparser = {'yaml': 'lyaml',
                    'lyaml': 'lyaml',
                    'json': 'json'}.get(rtype, 'noop')
        ret['transformer'] = transformer
        ret['unparser'] = unparser
        if unparser != 'noop':
            try:
                ret['result'] = renderers[unparser](ret['result'])
            except Exception:
                try:
                    # try to remove debugs from shell running with set -e
                    cret = '\n'.join(
                        [a for a in ret['result'].splitlines() if not
                         a.startswith('+ ')])
                    ret['result'] = renderers[unparser](cret)
                except:
                    if ret['raw_result'].startswith(
                        'NO RETURN FROM'
                    ):
                        trace = traceback.format_exc()
                        log.error(trace)
                    else:
                        raise
        if transformer != 'noop' and transformer != unparser:
            if transformer in renderers:
                try:
                    ret['result'] = renderers[transformer](ret['result'])
                except salt.exceptions.SaltRenderError:
                    trace = traceback.format_exc()
                    log.error(trace)
            elif transformer in outputters:
                try:
                    ret['result'] = outputters[transformer](ret['result'])
                except Exception:
                    if ret['raw_result'].startswith(
                        'NO RETURN FROM'
                    ):
                        trace = traceback.format_exc()
                        log.error(trace)
                    else:
                        raise
        if 'result' not in ret and ret.get('retcode'):
            ret['result'] = 'Salt Call Failed'
        if isinstance(ret['result'], dict):
            if [a for a in ret['result']] == [minion_id]:
                ret['result'] = ret['result'][minion_id]
    if strip_out and (ret['retcode'] in [0]):
        ret['stdout'] = ret['stderr'] = ''
    return ret


def sls(host,
        sls,
        outputter='json',
        transformer='highstate',
        strip_out=True,
        **kw):
    '''
    Run a state file on an host and fails on error
    kwargs are forwarded to ssh helper functions !

    CLI Examples::

        salt-call --local mc_remote.sls foo.net mysls

    '''
    kw.setdefault('outputter', outputter)
    kw.setdefault('transformer', transformer)
    kw.setdefault('strip_out', strip_out)
    ret = salt_call(host, 'state.sls', sls, **kw)
    if strip_out and (ret['retcode'] in [0]):
        ret = ret['result']
    return ret


def highstate(host,
              outputter='json',
              transformer='highstate',
              strip_out=True,
              **kw):
    '''
    Run an highstate on an host and fails on error
    kwargs are forwarded to ssh helper functions !

    CLI Examples::

        salt-call --local mc_remote.highstate foo.net

    '''
    kw.setdefault('outputter', outputter)
    kw.setdefault('transformer', transformer)
    kw.setdefault('strip_out', strip_out)
    ret = salt_call(host, 'state.highstate', **kw)
    if strip_out and (ret['retcode'] in [0]):
        ret = ret['result']
    return ret
# vim:set et sts=4 ts=4 tw=80:
