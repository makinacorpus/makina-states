# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# pylint: disable=W0105
'''
.. _module_mc_remote:

mc_remote / remote execution functions
========================================



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

from pprint import pformat
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
from salt.utils.odict import OrderedDict
try:
    import salt.utils.args
    HAS_ARGS = True
except ImportError:
    HAS_ARGS = False
import salt.utils.dictupdate
import salt.utils.pycrypto
import salt.utils.vt
import mc_states.saltapi

six = mc_states.saltapi.six
string_types = six.string_types
integer_types = six.integer_types

__func_alias__ = {
    'sls_': 'sls',
}

_get_ret = mc_states.saltapi._get_ssh_ret
asbool = mc_states.saltapi.asbool
_marker = mc_states.saltapi._marker
_SSHExecError = mc_states.saltapi.SSHExecError
_SSHLoginError = mc_states.saltapi.SSHLoginError
_SSHTimeoutError = mc_states.saltapi.SSHTimeoutError
_SSHVtError = mc_states.saltapi.SSHVtError
_SSHInterruptError = mc_states.saltapi.SSHInterruptError
_SSHCommandFinished = mc_states.saltapi.SSHCommandFinished
_SSHCommandFailed = mc_states.saltapi.SSHCommandFailed
_SSHCommandTimeout = mc_states.saltapi.SSHCommandTimeout
_SSHTransferFailed = mc_states.saltapi.SSHTransferFailed
_SaltCallFailure = mc_states.saltapi.SaltCallFailure
_RemoteResultProcessError = mc_states.saltapi.RemoteResultProcessError
_TransformError = mc_states.saltapi.TransformError
_RenderError = mc_states.saltapi.RenderError


# pylint: disable=R0903
class _EvalFalse(object):
    def __nonzero__(self):
        return False

    # pylint: disable=R0201
    def __unicode__(self):
        return "Failed"

    def __str__(self):
        return "Failed"

    def __repr__(self):
        return "Failed"


_EXECUTION_FAILED = _EvalFalse()
_SSH_PASSWORD_PROMP_RE = re.compile('(([Pp]assword(: ?for.*)?:))',
                                    re.M | re.U)

RESULT_SEP = '----- SALTCALL RESULT {0}'
SIMPLE_RESULT_SEP = RESULT_SEP.format('')
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
{script_content}
ret=${{?}}
if [ "x${{ret}}" != "x0" ];then
    echo "Failed \\"{script_path}\\"" >&2
    if [ "x{display_content_on_error}" = "x1" ] && [ -e "${{0}}" ];then
        echo "FAILED SCRIPT CONTENT:" >&2
        echo "----------------------" >&2
        cat "${{0}}" >&2
    fi
fi
exit ${{ret}}
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
    rsync_opts="${{rsync_opts}}v"
    sftp_opts=""
    scp_opts=""
fi
ret=0
has_ssh=0
if [ "x{progress}" = "x1" ] || [ "x{sh_wrapper_debug}" != "x" ];then
    rsync_opts="${{rsync_opts}}P"
fi
if [ "x{rsync_opts}" != "x" ];then
    rsync_opts="${{rsync_opts}} {rsync_opts}"
fi
if [ "x${{ret}}" = "x0" ];then
    if ! test -e "{orig}";then
        echo "Unexisting origin: {orig}" >&2
        ret=1
    else
        fmode=$(stat -c "%a" "{orig}")
        cmode=$(stat -c "%a" "{orig_container}")
    fi
fi
if [ "x${{ret}}" = "x0" ];then
    # ensure to have a connection
    if [ "x{sh_wrapper_debug}" != "x" ];then
        ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}" "set +x;date"
    else
        ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}" \
                "date 1>/dev/null 2>&1"
    fi
    if [ "x${{?}}" != "x0" ];then
        echo "SSH connection did not estasblish(file),"\
             " will fallback on scp/sftp" >&2
        has_ssh=1
    fi
fi
if [ "x${{has_ssh}}" = "x0" ] && [ "x${{ret}}" = "x0" ];then
    if [ "x{makedirs}" = "x1" ];then
     if [ "x{sh_wrapper_debug}" != "x" ];then
        ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
          "set -x;\
           if [ ! -e \\"{container}\\" ];then \
            mkdir -pv \\"{container}\\";\
            chmod -v  ${{cmode}} \\"{container}\\";\
           fi"
        ctret=${{?}}
     else
        ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
          "if [ ! -e \\"{container}\\" ];then \
            mkdir -p  \\"{container}\\";\
            chmod     ${{cmode}} \\"{container}\\";\
           fi"
        ctret=${{?}}
     fi
     if [ "x${{ctret}}" != "x0" ];then
         echo "Remote directory \\"{container}\\" creation failed">&2
         ret=1
     fi
    fi
fi
if [ "x${{has_ssh}}" = "x0" ] && [ "x${{ret}}" = "x0" ];then
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
            "test -e \\"{container}\\" \
            && test ! -f  \\"{container}\\""
    ctret=${{?}}
    if [ "x${{ctret}}" != "x0" ];then
        echo \
"Remote directory \\"{container}\\" does not exits or is not a directory">&2
        ret=1
    fi
fi
if [ "x${{has_ssh}}" = "x0" ] && [ "x${{ret}}" = "x0" ];then
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
       "if [ -d \\"{dest}\\" ];then\
         exit 1;\
        else\
         exit 0;\
        fi"
    if [ "x${{?}}" != "x0" ];then
         echo \
"Remote destination \\"{dest}\\" is a directory and not a file">&2
         ret=1
    fi
fi
if [ "x${{has_ssh}}" = "x0" ] && [ "x${{ret}}" = "x0" ];then
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
       "test -e \\"{container}\\""
    if [ "x${{?}}" != "x0" ];then
        echo "Remote directory \\"{container}\\" does not exits">&2
        ret=1
    fi
fi
if [ "x${{ret}}" = "x0" ];then
    if [ "x${{has_ssh}}" = "x0" ];then
        rsync ${{rsync_opts}} \\
                -e "ssh -p "{port}" {quoted_ssh_args}"\\
                "{orig}" "{user}@{host}":"{dest}"\\
                && fmode=''
        ret=${{?}}
    else
        ret=1
    fi
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
fi
if [ "x${{has_ssh}}" = "x0" ] && [ "x${{ret}}" = "x0" ] \
   && [ "x${{fmode}}" != "x" ];then
 if [ "x{sh_wrapper_debug}" != "x" ];then
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
       "set -x;chmod ${{fmode}} \\"{dest}\\""
 else
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
      "chmod ${{fmode}} \\"{dest}\\""
 fi
  ret=${{?}}
fi
if [ "x${{ret}}" != "x0" ];then
    echo "Failed transfer for \\"{orig}\\"" >&2
    if [ "x{display_content_on_error}" = "x1" ] && [ -e "{orig}" ];then
        cat "{orig}" >&2
        echo "CONTENTS:" >&2
        echo "---------" >&2
    fi
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
    rsync_opts="${{rsync_opts}}v"
    sftp_opts=""
    scp_opts=""
fi
if [ "x{progress}" = "x1" ] || [ "x{sh_wrapper_debug}" != "x" ];then
    rsync_opts="${{rsync_opts}}P"
fi
if [ "x{sync_identical}" = "x1" ];then
    rsync_opts="${{rsync_opts}} --delete --delete-excluded"
fi
if [ "x{rsync_opts}" != "x" ];then
    rsync_opts="${{rsync_opts}} {rsync_opts}"
fi
ret=0
has_ssh=0
if [ "x${{ret}}" = "x0" ];then
    if ! test -e "{orig}";then
        echo "Unexisting origin: {orig}" >&2
        ret=1
    else
        fmode=$(stat -c "%a" "{orig}")
        cmode=$(stat -c "%a" "{orig_container}")
    fi
fi
if [ "x${{ret}}" != "x0" ];then
    # ensure to have a connection
    if [ "x{sh_wrapper_debug}" != "x" ];then
        ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}" "set +x;date"
    else
        ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}" \
                "date 1>/dev/null 2>&1"
    fi
    if [ "x${{?}}" != "x0" ];then
        echo "SSH connection did not estasblish(file),"\
             " will fallback on scp/sftp" >&2
        has_ssh=1
    fi
fi
if [ "x${{ret}}" = "x0" ];then
    if [ "x{makedirs}" = "x1" ];then
     if [ "x{sh_wrapper_debug}" != "x" ];then
        ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
          "set -x;\
           if [ ! -e \\"{container}\\" ];then \
            mkdir -pv \\"{container}\\";\
            chmod -v  ${{cmode}} \\"{container}\\";\
           fi"
        ctret=${{?}}
     else
        ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
          "if [ ! -e \\"{container}\\" ];then \
            mkdir -p  \\"{container}\\";\
            chmod     ${{cmode}} \\"{container}\\";\
           fi"
        ctret=${{?}}
     fi
     if [ "x${{ctret}}" != "x0" ];then
         echo "Remote directory \\"{container}\\" creation failed">&2
         ret=1
     fi
    fi
fi
if [ "x${{has_ssh}}" = "x0" ] && [ "x${{ret}}" = "x0" ];then
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
            "test -e \\"{container}\\" \
            && test ! -f  \\"{container}\\""
    ctret=${{?}}
    if [ "x${{ctret}}" != "x0" ];then
        echo \
"Remote directory \\"{container}\\" does not exits or is not a directory">&2
        ret=1
    fi
fi
if [ "x${{has_ssh}}" = "x0" ] && [ "x${{ret}}" = "x0" ];then
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
       "if [ -e \\"{dest}\\" ];then\
         if test -d \\"{dest}\\";then\
            exit 0;\
         else\
            exit 1;\
         fi
        else\
         exit 0;\
        fi"
    dret=${{?}}
    if [ "x${{dret}}" != "x0" ];then
      echo "Remote destination \\"{dest}\\" is not a directory">&2
      ret=1
    fi
fi
if [ "x${{ret}}" = "x0" ];then
    if [ "x${{has_ssh}}" = "x0" ];then
        rsync ${{rsync_opts}} \\
                -e "ssh -p "{port}" {quoted_ssh_args}"\\
                "{corig}" "{user}@{host}":"{cdest}"\\
                && fmode=''
        ret=${{?}}
    else
        ret=1
    fi
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
fi
if [ "x${{has_ssh}}" = "x0" ] && [ "x${{ret}}" = "x0" ] \
   && [ "x${{fmode}}" != "x" ];then
 if [ "x{sh_wrapper_debug}" != "x" ];then
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
       "set -x;chmod ${{fmode}} \\"{dest}\\""
 else
    ssh -p "{port}" {ttyfree_ssh_args} "{user}@{host}"\\
      "chmod ${{fmode}} \\"{dest}\\""
 fi
  ret=${{?}}
fi
if [ "x${{ret}}" != "x0" ];then
    echo "Failed transfer for \\"{orig}\\"" >&2
fi
exit ${{ret}}
'''


log = logging.getLogger(__name__)
_default = object()


def get_localhost():
    return None, __grains__['id'], '127.0.0.1', 'localhost'


def ssh_kwargs(first_argument_kwargs=None, **kw):
    """
    Lookup & sanitize input in kwargs to have
    only one value for various & well known
    SSH connection parameters & other related to mc_remote.

    The resulting structure is an well known interface dict
    usable and used in all this module functions.

    All kwargs will be lookup in the form ssh_param and then param.

    Eg: ssh_username, if no value, user, if not value, default.

    This supports for now:

        user
            root
        tty
            use ssh -t (true)
        port
            22
        key_filename
            ~/id_{rsa,dsa} if existing else ~/.ssh/id_rsa
        gateway_key
            ~/id_{rsa,dsa} if existing else ~/.ssh/id_rsa
        gateway
            gateway host/ip if any
        gateway_user
            root
        gateway_port
            22
        password
            clear password if any (None)
        password_retries
            how many do we retry a failed password (3)
        known_hosts_file
            known_hosts_file if any (/dev/null)
        host_key_checking
            toggle host checking (no)
        makedirs
            When transfering files or the shell wrapper,
            are we allowed to create the conttainer(s)
            (false)
        quote
            quote commands (false)
        progress
            display ssh transfer stats (false)
        show_running_cmd
            flag for extra logs (true)
        no_error_log
            Do not report execution failure in logs
        display_ssh_output
            flag to stream output streams (true)
    """
    if not isinstance(first_argument_kwargs, dict):
        first_argument_kwargs = {}
    kw = copy.deepcopy(kw)
    res = OrderedDict()
    id_file = '~/.ssh/id_rsa'
    for k in ['~/.ssh/id_rsa', '~/.ssh/id_dsa']:
        k = os.path.expanduser(k)
        if os.path.exists(k):
            id_file = k
            break
    pretendants = OrderedDict([
        ('rsync_opts', ''),
        ('sync_identical', False),
        ('port', 22),
        ('tty', True),
        ('gateway_key', id_file),
        ('key_filename', id_file),
        ('display_content_on_error', True),
        ('show_running_cmd', True),
        ('gateway', None),
        ('gateway_user', 'root'),
        ('no_error_log', False),
        ('quote', False),
        ('gateway_port', 22),
        ('interaction_class', _SSHPasswordChallenger),
        ('tmpdir', tempfile.tempdir or '/tmp'),
        ('password', None),
        ('output_loglevel', 'info'),
        ('display_ssh_output', True),
        ('makedirs', False),
        ('progress', False),
        ('password_retries', 3),
        ('known_hosts_file', '/dev/null'),
        ('host_key_checking', 'no'),
        ('user', 'root')])
    for kwarg in [kw, first_argument_kwargs]:
        for param in [a for a in six.iterkeys(kwarg)]:
            fparam = param
            value = default_value = kwarg[param]
            if fparam in res:
                continue
            if isinstance(param, six.string_types):
                if (len(param) > 4) and param.startswith('ssh_'):
                    param = param[4:]
                if param in six.iterkeys(pretendants):
                    fparam = 'ssh_{0}'.format(param)
                    default_value = pretendants[param]
                for lparam in [param, fparam]:
                    value = kwarg.get(lparam, None)
                    if value not in [None, default_value]:
                        value = kwarg[lparam]
                        break
                if value in [None, default_value]:
                    continue
            res[fparam] = value
    for param, value in six.iteritems(pretendants):
        fparam = "ssh_{0}".format(param)
        if fparam not in res:
            res[fparam] = value
    return res


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
    # pylint: disable=E0702
    raise typ, eargs, trace


# pylint: disable=R0902
class _AbstractSshSession(object):
    def __init__(self, cmd, *a, **kw):
        self._proc = None
        self.cmd = cmd
        kw = ssh_kwargs(kw)
        if kw['ssh_quote']:
            self.cmd = pipes.quote(cmd)
        self.timeout = kw.get('timeout', False)
        self.loop_interval = kw.get('loop_interval', 0.05)
        self.ssh_display_ssh_output = kw['ssh_display_ssh_output']
        self.ssh_output_loglevel = kw.get('vt_loglevel',
                                          kw['ssh_output_loglevel'])
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
                log_stdout_level=self.ssh_output_loglevel,
                log_stdin_level=self.ssh_output_loglevel,
                log_stderr_level=self.ssh_output_loglevel,
                stream_stdout=self.ssh_display_ssh_output,
                stream_stderr=self.ssh_display_ssh_output)
            # let the connexion establish
            time.sleep(self.loop_interval)
        return self._proc

    @property
    def pid(self):
        if self.proc is not None:
            self._pid = self.proc.pid
        return self._pid

    # pylint: disable=R0201
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
                            cout, cerr = self.proc.recv()
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
                # log.error(trace)
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
        except Exception:
            trace = traceback.format_exc()
            # log.error(trace)
            raise
        finally:
            if isinstance(self.proc, salt.utils.vt.Terminal):
                self.proc.close(terminate=True, kill=True)


class _SSHPasswordChallenger(_AbstractSshSession):

    def __init__(self, cmd, *a, **kw):
        super(_SSHPasswordChallenger, self).__init__(cmd, *a, **kw)
        skw = ssh_kwargs(**kw)
        self.password = skw['ssh_password']
        self.password_retries = skw['ssh_password_retries']
        self.sent_password = 0
        self.pwd_index = 0
        self.cur_len = 0

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
    AbstractSshSession class, see 'ssh_interaction_class':

    cmd
        the full ssh command to wrap the execution from

        eg::

            ssh foo.com "ls /"

    ssh_quote
        do we force the script to be quoted
    ssh_display_ssh_output
        do we send output on the console
    ssh_output_loglevel
        log level
    ssh_password_retries
        how many retries do we try for the password
    ssh_interaction_class
        _AbstractSshSession subclass(not instance)
        (_SSHPasswordChallenger by default)
    timeout
        timeout for command execution

    '''
    # dont use regular named args to support multi layer of forwarded kwargs
    kw = ssh_kwargs(**kw)
    ssh_interaction_class = kw['ssh_interaction_class']
    acmd = __salt__['mc_utils.magicstring'](cmd)
    session = ssh_interaction_class(acmd, **kw)
    return session.run()


def _get_ssh_args(**kwargs):
    '''
    Compute common CLI ssh args for ssh functions.

    Please also look ssh_kwargs
    '''
    kw = ssh_kwargs(**kwargs)
    tty = kw['ssh_tty']
    ssh_key_filename = kw['ssh_key_filename']
    ssh_known_hosts_file = kw['ssh_known_hosts_file']
    ssh_host_key_checking = kw['ssh_host_key_checking']
    ssh_gateway = kw['ssh_gateway']
    ssh_gateway_key = kw['ssh_gateway_key']
    ssh_gateway_user = kw['ssh_gateway_user']
    ssh_gateway_port = kw['ssh_gateway_port']
    ssh_password = kw['ssh_password']
    ssh_args = []
    if tty:
        # Use double `-t` on the `ssh` script, it's necessary when `sudo` has
        # `requiretty` enforced.
        ssh_args.extend(['-t', '-t'])
    if ssh_known_hosts_file != '/dev/null':
        ssh_host_key_checking = 'yes'
    ssh_args.extend([
        '-oStrictHostKeyChecking={0}'.format(
            ssh_host_key_checking),
        '-oLogLevel=QUIET',
        '-oUserKnownHostsFile={0}'.format(ssh_known_hosts_file),
        '-oControlPath=none'])
    if not ssh_password:
        # There should never be both a password and an ssh key passed in, so
        ssh_args.extend(['-oPasswordAuthentication=no',
                         '-oChallengeResponseAuthentication=no',
                         '-oPubkeyAuthentication=yes',
                         '-oKbdInteractiveAuthentication=no',
                         '-i {0}'.format(ssh_key_filename)])
    if ssh_gateway:
        if ':' in ssh_gateway:
            ssh_gateway, ssh_gateway_port = ssh_gateway.split(':')

        ssh_gateway_args = [
            # Don't add new hosts to the host key database
            '-oStrictHostKeyChecking=no',
            # Set hosts key database path to /dev/null
            '-oUserKnownHostsFile={0}'.format(ssh_known_hosts_file),
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


def ssh_transfer_file(host, orig, dest=None, **kwargs):
    '''
    Transfer files to an host via ssh layer
    Please also look ssh_kwargs

    This will try then fallback on next transfer method.
    In order we try:

        - rsync
        - scp
        - sftp
        - gzip piped to dest host gunzip
        - cat piped to dest host uncat

    host
        host to tranfer to
    ssh_username/user (first win)
        user to connect as
    ssh_port/port (first win)
        Port to connect onto
    orig
        filepath to transfer
    dest
        where to upload, defaults to orig
    makedirs
        create parents if any
    vt_loglevel
        vt loglevel
    progress
        activate transfers statsv
    display_content_on_error
        show script on error

    Any extra keywords parameters will by forwarded to:
        _get_ssh_args
            (see doc)
            to mangle connection details
        interactive_ssh(& ssh_interaction_class)
            (see doc)
            to interact during ssh session
    '''
    kwargs.setdefault('ssh_display_content_on_error', False)
    kw = ssh_kwargs(kwargs)
    user = mc_states.saltapi.get_ssh_username(kw)
    port = kw['ssh_port']
    progress = kw['ssh_progress']
    makedirs = kw['ssh_makedirs']
    display_content_on_error = kw['ssh_display_content_on_error']
    if asbool(display_content_on_error):
        display_content_on_error = '1'
    else:
        display_content_on_error = '0'
    if asbool(makedirs):
        makedirs = '1'
    else:
        makedirs = '0'
    if asbool(kw['ssh_sync_identical']):
        sync_identical = '1'
    else:
        sync_identical = '0'
    if asbool(progress):
        progress = '1'
    else:
        progress = '0'
    if dest is None:
        dest = orig
    if not os.path.exists(orig):
        raise OSError("{0} does not exists".format(orig))
    if not any([
        os.path.islink(orig),
        os.path.isfile(orig)
    ]):
        raise OSError("{0} is not a file".format(orig))
    kw = copy.deepcopy(kw)
    # as we chain three login,methods, we multiplicate password challenges
    kw['ssh_password_retries'] = kw.get('ssh_password_retries', 3) * 8
    _ssh_args = _get_ssh_args(**kw)
    tmpfile = tempfile.mkstemp()[1]
    # transfer via scp, fallback on scp, fallback on rsync
    ttyfree_ssh_args = ' '.join([a for a in _ssh_args if a not in ['-t']])
    quoted_ssh_args = ' '.join([a.replace('"', '\\"')
                                for a in _ssh_args if a not in ['-t']])
    ssh_args = ' '.join(_ssh_args)
    try:
        cmd = TRANSFER_FILE_SCRIPT.format(
            **_mangle_kw_for_script({
                'ttyfree_ssh_args': ttyfree_ssh_args,
                'quoted_ssh_args': quoted_ssh_args,
                'rsync_opts':  kw['ssh_rsync_opts'],
                'sync_identical': sync_identical,
                'display_content_on_error': (
                    display_content_on_error),
                'orig': orig,
                'dest': dest,
                'progress': progress,
                'user': user,
                'orig_container': os.path.dirname(
                    os.path.abspath(orig)),
                'container': os.path.dirname(
                    os.path.abspath(dest)),
                'makedirs': makedirs,
                'host': host,
                'port': port,
                'tmpfile': tmpfile,
                'ssh_args': ssh_args})
        ).replace('-p "22"', '').replace('-P "22"', '')
        ret = interactive_ssh(cmd, **kw)
    finally:
        try:
            if os.path.exists(tmpfile):
                os.remove(tmpfile)
        except Exception:
            pass
    return ret


def ssh_transfer_dir(host, orig, dest=None, **kwargs):
    '''
    Transfer directories to an host via ssh layer
    Please also look ssh_kwargs

    This will try then fallback on next transfer method.
    In order we try:

        - rsync
        - scp
        - sftp

    host
        host to tranfer to
    ssh_username/user (first win)
        user to connect as
    ssh_port/port (first win)
        Port to connect onto
    orig
        filepath to transfer
    dest
        where to upload, defaults to orig
    makedirs
        create parents if any
    vt_loglevel
        vt loglevel
    progress
        activate transfer progress

    Any extra keywords parameters will by forwarded to:
        _get_ssh_args
            (see doc)
            to mangle connection details
        interactive_ssh(& ssh_interaction_class)
            (see doc)
            to interact during ssh session
    '''
    display_content_on_error = kwargs.setdefault(
        'ssh_display_content_on_error', False)
    kw = ssh_kwargs(kwargs)
    makedirs = kw['ssh_makedirs']
    user = mc_states.saltapi.get_ssh_username(kw)
    port = kw['ssh_port']
    progress = kw.get('progress', False)
    if asbool(makedirs):
        makedirs = '1'
    else:
        makedirs = '0'
    if asbool(kw['ssh_sync_identical']):
        sync_identical = '1'
    else:
        sync_identical = '0'
    if asbool(progress):
        progress = '1'
    else:
        progress = '0'
    if asbool(display_content_on_error):
        display_content_on_error = '1'
    else:
        display_content_on_error = '0'
    append_slashes = kw.setdefault('append_slashes', True)
    if dest is None:
        dest = orig
    corig, cdest = orig, dest
    if append_slashes:
        if not orig.endswith('/'):
            corig = orig + '/'
        if not dest.endswith('/'):
            cdest = dest + '/'
    kw = copy.deepcopy(kw)
    # as we chain three login,methods, we multiplicate password challenges
    kw['ssh_password_retries'] = kw.get('ssh_password_retries', 3) * 8
    _ssh_args = _get_ssh_args(**kw)
    if not os.path.exists(orig):
        raise OSError("{0} does not exists".format(orig))
    if os.path.isfile(orig):
        raise OSError("{0} is not a directory".format(orig))
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
            'sync_identical': sync_identical,
            'rsync_opts':  kw['ssh_rsync_opts'],
            'corig': corig,
            'cdest': cdest,
            'display_content_on_error': (
                display_content_on_error),
            'orig': orig,
            'dest': dest,
            'progress': progress,
            'orig_container': os.path.dirname(
                os.path.abspath(orig)),
            'container': os.path.dirname(
                os.path.abspath(dest)),
            'makedirs': makedirs,
            'user': user,
            'host': host,
            'port': port,
            'tmpfile': tmpfile,
            'ssh_args': ssh_args})
    ).replace('-p "22"', '').replace('-P "22"', '')
    try:
        ret = interactive_ssh(cmd, **kw)
    finally:
        try:
            if os.path.exists(tmpfile):
                os.remove(tmpfile)
        except Exception:
            pass
    return ret


def ssh(host, script, **kwargs):
    '''
    Executes a script command remotly via ssh
    Attention, if you use a gateway, only key auth is possible on the gw
    Please also look ssh_kwargs

    host
        host to execute the script on
    ssh_username/user (first win)
        user to connect as (default: root)
    ssh_port/port (first win)
        Port to connect onto (default: 22)
    tmpdir
        tempfile to upload script to (default to /tmp, this mountpoint
        must not have the -noexec mount flag)
    script
        script or command to execute:

            - if the script contains multiple lines
              We put the content in a temporary file, as-is before
              uploading it
            - If the script is a filepath
              we upload it as-is
            - In other cases
              we wrap it in a simple shell wrapper before uploading

    vt_loglevel
        loglevel to use for vt

    Even in case of a command, it will be wrapped before execution to ease
    shell quoting

    Any extra keywords parameters will by forwarded to:
        _get_ssh_args
            (see doc)
            to mangle connection details
        interactive_ssh(& ssh_interaction_class)
            (see doc)
            to interact during ssh session

    CLI Examples::

        salt-call mc_remote.ssh foo.net ssh_gateway=127.0.0.1 port=40007 \\
                "cat /etc/hostname" user=mytest password=secret

        salt-call mc_remote.ssh foo.net \\
                "cat /etc/hostname"

    '''
    kw = ssh_kwargs(kwargs)
    rand = _LETTERSDIGITS_RE.sub('_', salt.utils.pycrypto.secure_password(64))
    tmpdir = kw['ssh_tmpdir']
    dest = os.path.join(tmpdir, '{0}.sh'.format(rand))
    user = mc_states.saltapi.get_ssh_username(kw)
    port = kw['ssh_port']
    script_p, inline_script = script, False
    cret = _get_ret()
    msg = ('Running:\n'
           '{0}'.format(
               __salt__['mc_utils.magicstring'](script))).strip()
    dcoe = kw.setdefault('ssh_display_content_on_error', False)
    sh_wrapper_debug = kw.setdefault('sh_wrapper_debug', False)
    kw['script_path'] = script_p
    if '\n' in script:
        inline_script = True
    elif script and os.path.exists(script):
        inline_script = False
    else:
        inline_script = True
        skw = _mangle_kw_for_script(kw)
        if asbool(sh_wrapper_debug):
            skw['sh_wrapper_debug'] = '1'
        else:
            skw['sh_wrapper_debug'] = ''
        if asbool(dcoe):
            skw['display_content_on_error'] = '1'
        else:
            skw['display_content_on_error'] = '0'
        skw['script_content'] = script
        script = _SH_WRAPPER.format(**skw)
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
            args = (sssh_args, script_p, dest, user, host, port)
            cmd = 'ssh {0} "{3}@{4}"'.format(*args)
            if port not in [22, '22']:
                cmd += ' -p "{5}"'.format(*args)
            cmd += ' "chmod +x \\{2}\\"'.format(*args)
            cret = interactive_ssh(cmd, **copy.deepcopy(kw))
        # Exec the script, eventually
        if kw['ssh_show_running_cmd']:
            log.info(msg)
        args = (sssh_args, script_p, dest, user, host, port)
        cmd = 'ssh {0} "{3}@{4}"'.format(*args)
        if port not in [22, '22']:
            cmd += ' -p "{5}"'.format(*args)
        cmd += ' "{2}"'.format(*args)
        cret = interactive_ssh(cmd, **kw)
    except (_SSHExecError,) as exc:
        if not kw['ssh_no_error_log']:
            log.error("{0}".format(exc))
        cret = exc.exec_ret
    finally:
        if inline_script and script_p and os.path.exists(script_p):
            os.remove(script_p)
        # try to delete the remove pass
        if transfered:
            try:
                args = (sssh_args, script_p, dest, user, host, port)
                cmd = 'ssh {0} "{3}@{4}"'.format(*args)
                if port not in ['22', 22]:
                    cmd += ' -p "{5}" '
                cmd += '"'.format(*args)
                cmd += 'if [ -f\"{2}\" ];then rm -f \"{2}\";fi'.format(*args)
                cmd += '"'.format(*args)
                interactive_ssh(cmd, **copy.deepcopy(kw))
            except _SSHExecError:
                pass
    return cret


def delete_remote(host, filepath, mode="-f", level='info', **kw):
    '''
    Delete a remote file (or directory)
    '''
    getattr(log, level)('Delete on {0}: {1}'.format(host, filepath))
    rm_cmd = "rm {0} {1}".format(pipes.quote(mode), pipes.quote(filepath))
    ssh(host, rm_cmd, **kw)


def run(host, script, **kw):
    '''
    Wrapper to ssh but get only stdout

    kwargs are forwarded to ssh helper functions !

    returning only the code exist status
    '''
    return ssh(host, script, **kw)['stdout']


def ssh_retcode(host, script, **kw):
    '''
    Wrapper to ssh

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


def _consolidate_transformer_and_outputter(ret):
    ret['outputter'] = {'yaml': 'lyaml',
                        'lyaml': 'lyaml',
                        'json': 'json'}.get(ret.get('outputter', 'noop'),
                                            'noop')
    if ret.get('transformer', None) is None:
        ret['transformer'] = ret['outputter']
    ret['transformer'] = {'yaml': 'lyaml',
                          'lyaml': 'lyaml',
                          'highstate': 'highstate',
                          'nested': 'nested',
                          'json': 'json'}.get(
                              ret['transformer'], 'noop')
    return ret


def _consolidate_failure(ret):
    minion_id = ret.get('miinion_id', 'local')
    ret.setdefault('retcode', 0)
    ret.setdefault('result', None)
    if isinstance(ret, dict):
        if isinstance(ret['result'], dict):
            if [a for a in ret['result']] == [minion_id]:
                ret['result'] = ret['result'][minion_id]
        if ret.get('retcode'):
            ret.setdefault('raw_result', ret.pop('result', None))
            ret['result'] = _EXECUTION_FAILED
        if ret['result'] is _EXECUTION_FAILED:
            ret['retcode'] = 1
        if not ret['retcode']:
            ret['retcode'] = 0
    return ret


def _setup_grains(fun):
    def _call(*args, **kw):
        if not __opts__.get('grains'):
            __opts__['grains'] = __grains__
        restore_grains = False
        remove_grains = False
        old_grains = {}
        if ('grains' in __opts__) and not __opts__.get('grains'):
            restore_grains = True
            old_grains = __opts__.pop('grains', None)
        if 'grains' not in __opts__:
            remove_grains = True
        try:
            ret = fun(*args, **kw)
        finally:
            if remove_grains:
                __opts__.pop('grains', False)
            if restore_grains:
                __opts__['grains'] = old_grains
        return ret
    return _call


@_setup_grains
def _transform_ret_first_pass(ret):
    import yaml
    renderers = salt.loader.render(__opts__, __salt__)
    if (ret['outputter'] != 'noop') and ret.get('result', None):
        try:
            ret['result'] = renderers[ret['outputter']](ret['result'])
        except (ValueError, TypeError, yaml.YAMLError):
            try:
                # try to remove debugs from shell running with set -e
                cret = '\n'.join([a for a in ret['result'].splitlines()
                                  if not a.startswith('+ ')])
                ret['result'] = renderers[ret['outputter']](cret)
            except (ValueError, TypeError, yaml.YAMLError) as exc:
                ret['log_trace'] = traceback.format_exc()
                if ret['raw_result'].startswith('NO RETURN FROM'):
                    ret['result'] = _EXECUTION_FAILED
                else:
                    raise _RenderError(ret['log_trace'], ret=ret, original=exc)
    return ret


@_setup_grains
def _transform_ret_second_pass(ret):
    import yaml
    renderers = salt.loader.render(__opts__, __salt__)
    outputters = salt.loader.outputters(__opts__)
    if (
        ret['transformer'] != 'noop'
        and ret['transformer'] != ret['outputter']
        and ret.get('result', _EXECUTION_FAILED) is not _EXECUTION_FAILED
        and not ret['retcode']
    ):
        if ret['transformer'] in renderers:
            try:
                ret['result'] = renderers[ret['transformer']](ret['result'])
            except salt.exceptions.SaltRenderError:
                ret['log_trace'] = traceback.format_exc()
        elif ret['transformer'] in outputters:
            try:
                outputters = salt.loader.outputters(__opts__)
                ret['result'] = outputters[ret['transformer']](ret['result'])
            except (
                salt.exceptions.SaltRenderError,
                ValueError, TypeError, yaml.YAMLError
            ) as exc:
                ret['log_trace'] = traceback.format_exc()
                if ret['raw_result'].startswith('NO RETURN FROM'):
                    ret['result'] = _EXECUTION_FAILED
                else:
                    raise _TransformError(
                        ret['log_trace'], ret=ret, original=exc)
    return ret


def _unparse_ret(ret):
    ret = _consolidate_transformer_and_outputter(ret)
    # we can three layers of returns serilazations ...
    ret = _transform_ret_first_pass(ret)
    ret = _transform_ret_second_pass(ret)
    return ret


def run_salt_call(host,
                  use_vt,
                  remote,
                  fun,
                  arg,
                  kwarg,
                  kwargs,
                  outputter,
                  salt_call_bin,
                  salt_call_script,
                  loglevel,
                  masterless,
                  new_shell,
                  minion_id,
                  ttl=0):
    if isinstance(kwargs, dict):
        kwargs = copy.deepcopy(kwargs)
        for k in [a for a in kwargs]:
            if k.startswith('__pub_'):
                kwargs.pop(k, None)

    def _do(host,
            use_vt,
            remote,
            fun,
            arg,
            kwarg,
            kwargs,
            outputter,
            salt_call_bin,
            salt_call_script,
            loglevel,
            masterless,
            new_shell,
            minion_id):
        kw = ssh_kwargs(kwargs)
        sh_wrapper_debug = kw.get('sh_wrapper_debug', '')
        level = kw.setdefault('vt_loglevel', loglevel)
        rand = _LETTERSDIGITS_RE.sub(
            '_', salt.utils.pycrypto.secure_password(64))
        tmpdir = kw.get('tmpdir', tempfile.tempdir or '/tmp')
        outfile = os.path.join(tmpdir, '{0}.out'.format(rand))
        result_sep = RESULT_SEP.format(outfile)
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
        skwargs = _mangle_kw_for_script({
            'outputter': '--out="{0}"'.format(outputter),
            'local': bool(masterless) and '--local' or '',
            'sh_wrapper_debug': sh_wrapper_debug,
            'loglevel': '-l{0}'.format(loglevel),
            'vt_loglevel': '-l{0}'.format(level),
            'salt_call_bin': salt_call_bin,
            'salt_call_script': salt_call_script,
            'outfile': outfile,
            'quoted_outfile': pipes.quote(outfile),
            'result_sep': pipes.quote(result_sep),
            'fun': fun,
            'arg': arg,
            'kwarg': kwarg,
            'sarg': sarg})
        if not remote:
            # use to call:
            # or call mastersalt
            if new_shell:
                try:
                    script = salt_call_script.format(**skwargs)
                    ret = __salt__['cmd.run_all'](script,
                                                  python_shell=True,
                                                  runas=saltapi.get_ssh_username(kw),
                                                  use_vt=use_vt)
                finally:
                    if os.path.exists(skwargs['quoted_outfile']):
                        os.remove(skwargs['quoted_outfile'])
            # or a salt ommand from another shell
            else:
                fun = skwargs['fun']
                args = skwargs['arg']
                kwargs = skwargs['kwarg']
                try:
                    func = __salt__[fun]
                    if args is not None and kwargs is not None:
                        ret = func(*args, **kwargs)
                    elif args is not None and (kwargs is None):
                        ret = func(*args)
                    elif (args is None) and kwargs is not None:
                        ret = func(**kwargs)
                    else:
                        ret = func()
                    ret = {'raw_result': ret,
                           'result_sep': result_sep,
                           'result': ret}
                except Exception:
                    trace = traceback.format_exc()
                    ret = {'raw_result': trace, 'result': trace, 'retcode': 1}
        else:
            try:
                if level in ['trace', 'garbage']:
                    level = 'debug'
                if level in ['error', 'warning']:
                    level = 'info'
                try:
                    script = salt_call_script.format(**skwargs)
                    ret = ssh(host, script, **kw)
                except (Exception, SystemExit, KeyboardInterrupt) as exc:
                    typ, eargs, _trace = sys.exc_info()
                    _reraise(exc, trace=_trace)
                    level = "error"
            finally:
                delete_remote(
                    host, skwargs['quoted_outfile'], level=level, **kw)
        ret['sh_wrapper_debug'] = sh_wrapper_debug
        ret['result_sep'] = result_sep
        ret['outputter'] = outputter
        ret['minion_id'] = minion_id
        ret['log_trace'] = None
        for i in ('stdout', 'stderr'):
            ret.setdefault(i, '')
        ret['raw_result'] = (
            'NO RETURN inside temporary file: {0}'
            ''.format(outfile))
        return ret
    ret = __salt__['mc_macros.filecache_fun'](
        _do, args=[host,
                   use_vt,
                   remote,
                   fun,
                   arg,
                   kwarg,
                   kwargs,
                   outputter,
                   salt_call_bin,
                   salt_call_script,
                   loglevel,
                   masterless,
                   new_shell,
                   minion_id],
        ttl=ttl,
        prefix='mc_remote.run_salt_call')
    return ret


def get_saltcall_result(text,
                        result_sep=SIMPLE_RESULT_SEP,
                        sh_wrapper_debug=False):
    collect, result = False, ''
    for line in text.splitlines():
        skip_collect = False
        if collect:
            if sh_wrapper_debug:
                skip_collect = _SKIP_LINE_RE.search(line)
            if not skip_collect:
                result += line
                result += "\n"
        if line.startswith(result_sep):
            collect = True
    return result


def _mark_failed(ret):
    ret['result'] = None
    msg = "Salt call failed"
    try:
        msg = "Salt call failed:\n{0}".format(
            __salt__['mc_utils.magicstring'](pformat(ret)))
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            msg = "Salt call failed:\n{0}".format(
                __salt__['mc_utils.magicstring'](repr(ret)))
        except Exception:
            msg = "Salt call failed"
    if ret['log_trace'] and isinstance(ret['log_trace'], six.string_types):
        log.error(ret['log_trace'])
    return ret, msg


def _process_ret(ret, unparse=True, strip_out=False, hard_failure=False):
    _consolidate_failure(ret)
    ret.setdefault('log_trace', '')
    if unparse:
        try:
            ret['result'] = get_saltcall_result(
                ret.get('stdout', ''),
                result_sep=ret.get('result_sep', SIMPLE_RESULT_SEP),
                sh_wrapper_debug=ret.get('sh_wrapper_debug', False))
            ret['raw_result'] = copy.deepcopy(ret['result'])
            ret = _unparse_ret(ret)
        except (_RemoteResultProcessError,) as exc:
            ret = exc.ret
            if ret['retcode']:
                raise exc
    if strip_out and not ret['retcode']:
        ret['stdout'] = ret['stderr'] = ''
    ret = _consolidate_failure(ret)
    # consistent failure in all properties
    # prepare also for hard failure in case
    if ret.get('result', _EXECUTION_FAILED) is _EXECUTION_FAILED:
        ret, msg = _mark_failed(ret)
        if hard_failure:
            raise _SaltCallFailure(msg, exec_ret=ret)
    return ret


def salt_call(host,
              fun=None,
              arg=None,
              kwarg=None,
              outputter='json',
              transformer=None,
              unparse=True,
              loglevel='info',
              salt_call_bin='salt-call',
              masterless=None,
              minion_id='local',
              salt_call_script=None,
              strip_out=None,
              hard_failure=False,
              remote=None,
              use_vt=None,
              new_shell=None,
              ttl=0,
              *args,
              **kwargs):
    '''
    Executes a salt_call call remotely via ssh

    host
        host to execute on
    ssh_username/user (first win)
        user to connect as (default: root)
    ssh_port/port (first win)
        Port to connect onto (default: 22)
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
        (the "2nd pass")
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
    remote
        use salt locally (you must set host to None !
    new_shell
        if we execute locally, new_shell can be set to false to
        execute directly the salt function instead of calling a new shell
        to call the function, this can be used in conjunction with ttl
        to cache results easily, eg ::

             salt-call --local -lall mc_remote.salt_call fun=test.ping \\
                host=127.0.0.1 new_shell=False ttl=60

             salt-call --local mc_remote.mastersalt_call fun=mc_cl.settings \\
                host=127.0.0.1 new_shell=False ttl=60

    use_vt
        When ran locally, use use_vt to stream output
    args
        are appended to arg as arguments to the called salt function
    kwargs
        They are forwarded to ssh helper functions !
    ttl
       Use filecache based execution (the result will be cached for X seconds).
       If the cache is not expired, the result will be used and the function
       wont be executed.

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
    vt_lvl = kwargs.setdefault('vt_loglevel', 'warning')
    lvl = kwargs.setdefault('loglevel', __opts__.get('log_level', 'warning'))
    sc, dso = False, False
    if vt_lvl in ['info', 'debug', 'trace']:
        dso = True
    if lvl in ['info', 'debug', 'trace']:
        dso = True
    if lvl in ['debug', 'trace']:
        sc = True
    kwargs.setdefault('ssh_display_ssh_output', dso)
    kwargs.setdefault('ssh_show_running_cmd', sc)
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
    ret = salt.utils.args.parse_input(arg, condition=False)
    # make pylint happy
    arg, kwarg = ret[0], ret[1]
    if not HAS_ARGS:
        raise OSError('Missing salt.utils.args')
    if host in get_localhost():
        if 'mastersalt' in salt_call_bin:
            if __salt__['mc_controllers.mastersalt_mode']():
                new_shell = False
            else:
                new_shell = True
                if not __salt__['mc_controllers.has_mastersalt']():
                    raise mc_states.saltapi.MastersaltNotInstalled('Mastersalt is not installed')
                if not __salt__['mc_controllers.has_mastersalt_running']():
                    raise mc_states.saltapi.MastersaltNotRunning('Mastersalt is not running')
        if remote is None:
            remote = False
    if new_shell is None:
        new_shell = True
    if remote is None:
        remote = True
    if use_vt is None:
        if remote:
            use_vt = True
        else:
            use_vt = False
    if masterless is None:
        if 'mastersalt' in salt_call_bin:
            fun_ = 'mc_controllers.local_mastersalt_mode'
        else:
            fun_ = 'mc_controllers.local_salt_mode'
        masterless = __salt__[fun_]() == 'masterless'
    else:
        masterless = bool(masterless)
    # uglyness for caching a bit based on calling args
    if not remote and not new_shell:
        unparse = False
    ret = run_salt_call(host,
                        use_vt,
                        remote,
                        fun,
                        arg,
                        kwarg,
                        kwargs,
                        outputter,
                        salt_call_bin,
                        salt_call_script,
                        loglevel,
                        masterless,
                        new_shell,
                        minion_id,
                        ttl=ttl)
    return _process_ret(ret, unparse, strip_out, hard_failure)


def mastersalt_call(*a, **kw):
    '''
    Execute mastersalt-call remotely
    see salt-call
    '''
    kw.setdefault('salt_call_bin', 'mastersalt-call')
    return salt_call(*a, **kw)


def local_mastersalt_call(*a, **kw):
    '''
    Execute mastersalt-call locally, maybe in another shell
    see salt-call
    '''
    return mastersalt_call(None, *a, **kw)


def local_salt_call(*a, **kw):
    '''
    Execute salt-call locally, in another shell
    see salt-call
    '''
    kw.setdefault('remote', False)
    return mastersalt_call(None, *a, **kw)


def hardstop_salt_call(*args, **kw):
    if not kw:
        kw = {}
    kw['hard_failure'] = True
    return salt_call(*args, **kw)


def sls_(host,
         sls,
         outputter='json',
         transformer='highstate',
         strip_out=True,
         **kw):
    '''
    Run a state file on an host and fails on error
    kwargs are forwarded to ssh helper functions !

    host
        host to connect onto
    ssh_username/user (first win)
        user to connect as (default: root)
    ssh_port/port (first win)
        Port to connect onto (default: 22)
    sls
        sls to execute

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

    host
        host to connect onto
    ssh_username/user (first win)
        user to connect as (default: root)
    ssh_port/port (first win)
        Port to connect onto (default: 22)
    sls
        sls to execute

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
