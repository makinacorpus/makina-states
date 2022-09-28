#!/usr/bin/env python
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
'''
Singleton executor
===================

This will call the 'CMDS' an allow only one execution at a time
system wide.

Once an execution has been triggered:

    - nothing can kill it except a kill -9
    - main loop (and not main program!) can maybe kill it after a timeout
    - Neither terminal closure or keyboard interrupt (SIGINT)
      can stop the execution
    - the commands are always executed in background while their output
      is given in realtime to the connected terminal

The behavior can be changed by tweaking:

    - one of the main threads
    - custom_communicate
    - get_callback_args
    - prepare_parser
    - do_custom_parser
    - get_worker_pids
    - get_deployer_pids
    - get_running_pids

'''
import re
import traceback
import copy
import datetime
import time
import atexit
import os
import sys
from optparse import OptionParser
from multiprocessing import (
    Process,
    Pool,
    Manager
)
import signal

try:
    from Queue import Empty, Queue
except ImportError:
    from queue import Empty, Queue
import logging
from subprocess import Popen, PIPE
from threading import Thread
import socket


# this match the log ! :)
basestring = str
_name = 'deploy'
logger = logging.getLogger('{0}-main'.format(_name))
worker_logger = logging.getLogger('{0}-worker'.format(_name))
to_logger = logging.getLogger('{0}-timeout-watcher'.format(_name))
rawlogger = logging.getLogger('{0}-rawlogger'.format(_name))
rawlogger.propagate = False
LOG = "{tmpdir}/makina-states.{project_name}-deploy.log"
LOCK = "{tmpdir}/.makina-states.{project_name}-deploy.lock"
DEFAULT_TIMEOUT = 5 * 60 * 60
DEFAULT_DELAY = None
CMDS = ['salt-call --local --retcode-passthrough'
        ' -l{loglevel} "{salt_function}" "{project_name}"']
OPTIONS = {
    'delay': DEFAULT_DELAY,
}


def get_container(pid):
    lxc = 'MAIN_HOST'
    envf = '/proc/1/environ'.format(pid)
    cg = '/proc/{0}/cgroup'.format(pid)
    # lxc ?
    if os.path.isfile(cg):
        with open(cg) as fic:
            content = fic.read()
            if 'lxc' in content:
                # 9:blkio:NAME
                lxc = content.split('\n')[0].split(':')[-1]
    if '/lxc' in lxc:
        lxc = lxc.split('/lxc/', 1)[1]
    if lxc == 'MAIN_HOST' and os.path.isfile(envf):
        with open(envf) as fic:
            content = fic.read()
            if 'container=lxc' in content:
                lxc = socket.getfqdn()
    return lxc


def is_lxc():
    container = get_container(1)
    if container not in ['MAIN_HOST']:
        return True
    return False


def filter_host_pids(pids):
    thishost = get_container(1)
    return [a for a in pids if get_container(a) == thishost]


def popen(cargs=None, shell=True):
    if not cargs:
        cargs = []
    ret, ps = None, None
    if cargs:
        ps = Popen(cargs, shell=shell, stdout=PIPE, stderr=PIPE)
        ret = ps.communicate()
    return ret, ps


def _decode(s):
    if hasattr(s, 'decode'):
        s = s.decode()
    return s


def get_worker_pids(*args, **kwargs):
    '''
    Search worker process
    '''
    ops = popen(
        'ps aux'
        '|grep {o[salt_function]}'
        '|grep {k[project_name]}'
        '|grep -v vimdiff'
        '|grep -v grep'
        '|awk \'{{print $2}}\''.format(o=OPTIONS, k=kwargs))[0]
    return _decode(ops[0]) + _decode(ops[1]) + "\n"


def get_deployer_pids(*args, **kwargs):
    '''
    Search program process
    '''
    prog = sys.argv[0]
    pps = popen(
        'ps aux|grep \'{0}\'|grep -Ev "grep|vimdiff"'
        '|awk \'{{print $2}}\''.format(prog))[0]
    return _decode(pps[0]) + _decode(pps[1]) + "\n"


def get_running_pids(*args, **kwargs):
    ps = []
    filtered = ["{0}".format(os.getpid())]
    for pids in[
        get_worker_pids(*args, **kwargs),
        get_deployer_pids(*args, **kwargs)
    ]:
        if not isinstance(pids, list):
            pids = [
                item for item in [pidl.strip()
                               for pidl in pids.split()
                               if pidl.strip()
                               and pidl not in filtered]]
        for item in pids:
            if item not in ps:
                ps.append(item)
    return filter_host_pids(ps)


def logflush():
    for lg in [rawlogger, worker_logger, logger]:
        for handler in lg.handlers:
            handler.flush()


def init_file_logging(logfile, lvl=0):
    l_format = logging.Formatter(
        "%(asctime)s [%(levelname)-5.5s] <%(name)s> %(message)s")
    r_format = logging.Formatter("%(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(l_format)
    rconsole_handler = logging.StreamHandler()
    rconsole_handler.setFormatter(r_format)
    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(l_format)
    rfile_handler = logging.FileHandler(logfile)
    rfile_handler.setFormatter(r_format)
    rawlogger.addHandler(rfile_handler)
    rawlogger.addHandler(rconsole_handler)
    root = logging.getLogger()
    root.addHandler(console_handler)
    root.addHandler(file_handler)
    rawlogger.setLevel(0)
    root.setLevel(lvl)


class Tee(object):

    def __init__(self, dup, orig, output=True, file_output=True):
        self.buffer = ''
        self.dup = dup
        self.orig = orig
        self.output = output
        self.file_output = file_output

    def write(self, s=''):
        if sys.version[0] < "3":
            if isinstance(s, unicode):
                s = s.encode('utf-8')
        s = _decode(s)
        self.buffer += s
        if self.output:
            self.orig.write(s)
        if self.file_output:
            logger.info(s)
        self.flush()

    def flush(self):
        if self.output:
            logflush()
            self.orig.flush()


def init_worker(lockfile=None):
    '''
    only and only if lockfile is not there anymore,
    do not ignore sigterm and even do it.
    '''
    def handle_sigs():
        def handle_sigterm(signum, frame):
            if not os.path.exists(lockfile):
                worker_logger.debug('Worker has received sigterm !')
                resume_signals()
                os.kill(os.getpid(), signal.SIGTERM)
        signal.signal(signal.SIGTERM, handle_sigterm)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    return handle_sigs


def resume_signals():
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)


class ProcessError(Exception):
    '''.'''


class TimeoutError(Exception):
    '''.'''


class InterruptError(ProcessError, KeyboardInterrupt):
    '''.'''


def printer(io_q, p_q, logfile, proc):
    while True:
        line = ''
        try:
            try:
                # Block for 1 second.
                identifier, line = io_q.get(True, 1)
                if identifier == 'STDERR':
                    meth = rawlogger.error
                    e = 'E: '
                else:
                    meth = rawlogger.info
                    e = 'S: '
                if sys.version[0] < '3':
                    if isinstance(line, unicode):
                        line = str(line.encode('utf-8'))
                line = _decode(line)
                meth(e + line.strip())
                logflush()
            except Empty:
                # No output in either streams for a second. Are we done?
                if proc.poll() is not None:
                    break
        except Exception:
            # dont fail because of encode errors on output
            pass
    p_q.put('d')


def stream_watcher(io_q, p_q, identifier, stream_queue, stream):
    for line in stream:
        stream_queue.put(line)
        io_q.put((identifier, line))
    if not stream.closed:
        stream.close()
    p_q.put('d')


def custom_communicate(proc, stdout=None, stderr=None, delay=None):
    retry_loop = False
    if proc.returncode and not retry_loop:
        raise Exception('stopped due to non zero return code')
    return retry_loop, delay, stdout, stderr


def deploy(callback_args, loglevel, logfile, lock, **kwargs):
    '''
    The real deploy work is done here !
    '''
    # think to remove locks in subshell
    # if main program has aborted before end of deployment
    worker_logger.info('start - deploy')
    if not kwargs:
        kwargs = {}
    delay = kwargs.get('delay', None)
    kwargs['loglevel'] = loglevel
    kwargs['logfile'] = logfile
    kwargs['lock'] = lock
    logflush()
    # we need early py26
    fic = open(lock, 'w')
    fic.write('locked')
    fic.flush()
    fic.close()
    pids = [os.getpid()]

    def handle_sigusr2(signum, frame):
        pids.reverse()
        clean_locks(lock)
        worker_logger.debug('Worker has received termination request !')
        logflush()
        for pid in pids:
            try:
                logger.error('killing pid: {0}'.format(pid))
                os.kill(pid, signal.SIGKILL)
            except:
                continue
    signal.signal(signal.SIGUSR2, handle_sigusr2)
    exitcode = 0
    try:
        do_loop = True
        while do_loop:
            for cmd in CMDS:
                try:
                    io_q = Queue()
                    p_q = Queue()
                    streamout_queue = Queue()
                    streamerr_queue = Queue()
                    if isinstance(cmd, list):
                        cmd = [a.format(*callback_args, **kwargs)
                               for a in cmd]
                        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
                    else:
                        cmd = cmd.format(*callback_args, **kwargs)
                        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
                    # we are already daemonized multiprocess
                    # so the only option now is to thread out to
                    # parrallelize
                    threads = []
                    threads.append(
                        Thread(
                            target=stream_watcher, name='stderr-watcher',
                            args=(io_q, p_q, 'STDERR',
                                  streamerr_queue, proc.stderr)
                        ).start()
                    )
                    threads.append(
                        Thread(
                            target=stream_watcher, name='stdout-watcher',
                            args=(io_q, p_q, 'STDOUT',
                                  streamout_queue, proc.stdout)
                        ).start()
                    )
                    threads.append(
                        Thread(target=printer, name='printer',
                               args=[io_q, p_q, logfile, proc]).start()
                    )
                    proc.wait()
                    for t in threads:
                        ret = p_q.get()
                        if t and ret in ['d']:
                            t.join()
                    stdout = ''
                    buf = ''
                    while True:
                        try:
                            content = streamout_queue.get_nowait()
                            if buf:
                                content = buf + content
                                buf = ''
                            try:
                                stdout += content
                            except UnicodeDecodeError:
                                buf = content
                        except Empty:
                            break
                    stderr = ''
                    buf = ''
                    while True:
                        try:
                            content = streamerr_queue.get_nowait()
                            if buf:
                                content = buf + content
                                buf = ''
                            try:
                                stderr += _decode(content)
                            except UnicodeDecodeError:
                                # handle 2codes chars
                                buf = content
                        except Empty:
                            break
                    (do_loop, delay, stdout, stderr) = custom_communicate(
                        proc, stdout, stderr, delay)
                    if do_loop and delay:
                        print('Looping again in {0}s'.format(delay))
                        if delay:
                            time.sleep(delay)
                except (Exception,) as ex:
                    worker_logger.error('{0} failed'.format(cmd))
                    worker_logger.error("{0}".format(ex))
                    # XXX: do we really need the trace ?
                    try:
                        worker_logger.error(
                            "{0}".format(traceback.format_exc()))
                    except Exception:
                        pass
                    logflush()
                    do_loop = False
                    exitcode = 1
                    break
        if not exitcode:
            worker_logger.info('Worker has deployed successfully')
            logflush()
        else:
            worker_logger.error('Worker has failed the deployment')
            logflush()
    finally:
        for i in ['loglevel', 'logfile', 'lock']:
            kwargs.pop(i, None)
        clean_locks(lock)
    # be sure to be killed
    return exitcode


def toggle_log(output=True, file_output=True):
    for std in sys.stderr, sys.stdout:
        if isinstance(std, Tee):
            std.output = output
            std.file_output = file_output


def blind_send(que, msg, logfile=None):
    try:
        return que.put(msg)
    except Exception:
        # oups, parent is dead
        toggle_log(False, True)
        msg = '{0}: {1}'.format('Detached worker', msg)
        logger.info(msg)
        # from now multiprocessing will fail to contact
        # parent and kill the process, we should not output
        # anything
        toggle_log(False, False)


def communicator(func, logfile=None):
    '''Warning, this is a picklable decorator !'''
    def _call(protocol_queue, messages_queue, args, kwargs):
        '''called with [queue, args, kwargs] as first optionnal arg'''
        logger.debug('start - worker')
        kwargs['multiprocess_protocol_queue'] = protocol_queue
        kwargs['multiprocess_messages_queue'] = messages_queue
        ret = None
        try:
            protocol_queue.put('pid:{0}'.format(os.getpid()))
            ret = func(*args, **kwargs)
            resume_signals()
            blind_send(protocol_queue, 'END', logfile=logfile)
        except (TimeoutError,) as ex:
            blind_send(messages_queue, ex.message, logfile=logfile)
            blind_send(protocol_queue, 'TIMEOUT', logfile=logfile)
            resume_signals()
            trace = traceback.format_exc()
        except (Exception,) as ex:
            resume_signals()
            trace = traceback.format_exc()
            blind_send(messages_queue,
                       'An unmanaged exception has been raised:',
                       logfile=logfile)
            blind_send(messages_queue, '{0}\n{1}'.format(ex, trace),
                       logfile=logfile)
            blind_send(protocol_queue, 'ERROR', logfile=logfile)
        resume_signals()
        logger.info('end - worker')
        toggle_log(False, False)
        return ret
    return _call


# for pickle and multiprocessing, we cant use directly decorators
def _run_deploy(*args, **kwargs):
    return communicator(deploy, logfile=args[2][1])(*args, **kwargs)


def in_time(endto):
    return time.time() <= endto


def terminate(pools):
    if not isinstance(pools, list):
        pools = [pools]
    # wait for timeout watcher cycle
    for pool in pools:
        if pool is not None:
            pool.terminate()
            pool.join()


def is_locked(lockfile):
    ret = False
    if lockfile and os.path.exists(lockfile):
        ret = True
    return ret


def timer_terminator(timeout, pid, logfile, lockfile, **kwargs):
    snow = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    to_msg = (
        'Process {0} started at {1} did not finished '
        ' after a timeout of {2}s under and was killed'
    ).format(pid, snow, timeout)
    snow = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    to_msg.format(snow, timeout)
    now = time.time()
    endto = now + timeout
    while is_locked(lockfile):
        if is_locked(lockfile):
            if in_time(endto):
                time.sleep(0.01)
            else:
                try:
                    os.kill(pid, signal.SIGUSR2)
                    to_logger.error(to_msg)
                    raise TimeoutError(to_msg)
                except OSError:
                    pass  # already terminated
        else:
            break
    # be sure to be killed
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    os.kill(os.getpid(), signal.SIGTERM)


def _run_timer_terminator(*args, **kwargs):
    return communicator(timer_terminator, logfile=args[2][1])(*args, **kwargs)


def enter_mainloop(target,
                   args=None,
                   kwargs=None,
                   pool=None,
                   pool_size=None,
                   protocol_queue=None,
                   messages_queue=None,
                   callback=None,
                   exit_callback=None,
                   lockfile=None,
                   logfile=None,
                   timeout=None,
                   delay=None,
                   stdout_tee=None,
                   stderr_tee=None):
    '''
    Manage a multiprocessing pool

    - If the protocol queue does not output anything, the pool runs
      indefinitly

    - If the protocol queue returns KEYBOARDINT or ERROR, this will kill the
      pool totally calling terminate & join and ands with a ProcessError
      exception notifying callers from the abnormal termination

    - If the protocol queue returns END or callback is defined and returns
      True, it just join the process and return the data.

    - If the process expires the timeout, it will throw a TimeoutError

    target
        the function you want to execute in multiproccessing
    timeout
        process will be terminated if not done until timeout
    pool
        pool object can be None if you want a default pool, but you ll
        have then to define pool_size instead
    pool_size
        pool size if you did not provide yourself a pool
    callback
        any callback that returns a boolean and takes a string in argument
        which returns True to signal that 'target' is finished
        and we need to join the pool
    exit_callback
        a callcack taking the result of the function being processed
        and return it after eventual post processing
    delay
        if the main loop is retried, sleep a litte time (seconds)
    stdout_tee
        Tee tee object tied to stdout of the execution
    stderr_tee
        Tee tee object tied to stdin of the execution
    args
        positionnal arguments to call the function with
        if you dont want to use pool.map
    kwargs
        kwargs to give to the function in case of process
    Attention, the function must have the following signature:

            target(protocol_queue, message_queue, args, kwargs)

    You may use the 'communicator' decorator to generate such a function
    (see end of this file) but your final function must accept kwargs.
    '''
    if not kwargs:
        kwargs = {}
    if not pool_size:
        pool_size = 1
    if not pool:
        pool = Pool(pool_size, init_worker(lockfile))
    manager = Manager()
    if not protocol_queue:
        protocol_queue = manager.Queue()
    if not messages_queue:
        messages_queue = manager.Queue()

    to_m_queue = manager.Queue()
    to_p_queue = manager.Queue()
    ret = {'return': None}

    if exit_callback is None:
        def exit_callback(fret):
            ret['return'] = fret
    finished = False
    pools = [pool]
    try:
        pool.apply_async(target, [protocol_queue, messages_queue,
                                  args, kwargs],
                         callback=exit_callback)
        to_pool = None
        pid = ''
        while not finished:
            try:
                test = protocol_queue.get_nowait()
            except Empty:
                test = 'NO_PROTOCOL_CLUE'
            msgs = []
            while True:
                try:
                    msgs.append(messages_queue.get_nowait())
                except Empty:
                    break
            if test.startswith('pid:'):
                try:
                    pid = int(test.split('pid:')[1])
                except:
                    pass
            # start a timeout  killer at soon as we get the worker pid
            if pid and timeout and not to_pool:
                to_pool = Pool(pool_size, init_worker(lockfile))
                pools.append(to_pool)
                to_pool.apply_async(_run_timer_terminator,
                                    [to_p_queue, to_m_queue,
                                     [timeout, pid, logfile, lockfile], {}])
            timeout_test = None
            to_msgs = []
            if to_pool:
                while not timeout_test:
                    try:
                        timeout_test = to_p_queue.get_nowait()
                    except Empty:
                        break
                while True:
                    try:
                        to_msgs.append(to_m_queue.get_nowait())
                    except Empty:
                        break
            if timeout_test in ['TIMEOUT']:
                terminate(pools)
                to_msgs = '\n'.join(to_msgs)
                print(to_msgs)
                raise TimeoutError(to_msgs)
            if msgs:
                msgs = '\n'.join(msgs)
                print(msgs)
            if test in ['KEYBOARDINT']:
                logger.error('User interrupt, we will continue deployment')
                finished = True
                ret['return'] = -1
            elif test in ['ERROR']:
                logger.error('Aborting due to errors')
                terminate(pools)
                raise ProcessError('process did not finished correctly')
            elif test in ['END'] or (callback and callback(test)):
                terminate(pools)
                finished = True
                break
            else:
                time.sleep(0.125)
    except (KeyboardInterrupt, SystemExit):
        ret['return'] = -1
        logger.info(
            'User issued keyboard or interrupt '
            'from main program, we continue the deployment in background')
    return ret['return']


def test_deploy(*args, **kwargs):
    deploy_lock = kwargs['deploy_lock']
    deploy_log = kwargs['deploy_log']
    pids = get_running_pids(*args, **kwargs)
    if pids or os.path.exists(deploy_lock):
        if not pids:
            logger.info(
                "Stale lock, interrupted program?\n"
                "We will delete the {DEPLOY_LOCK} file".format(
                    DEPLOY_LOCK=deploy_lock))
            os.remove(deploy_lock)
        else:
            logger.info(
                "Already in progress (pids: {0})\n"
                "If something did go wrong, please"
                " delete the {DEPLOY_LOCK} file.\n"
                "This program run multiple proceses, so multiple pids"
                " is normal".format(
                    pids,
                    DEPLOY_LOCK=deploy_lock))
            os.system('ps aufx -C4|egrep \'{0}\'|grep -v grep'.format(
                "|".join(pids)))
            logger.info(
                "You can attach to and read the log file with:\n"
                "   tail -f {0}".format(deploy_log))
            sys.exit(128)


def clean_locks(locks=None):
    if not locks:
        locks = []
    if isinstance(locks, basestring):
        locks = [locks]
    for lock in locks:
        if os.path.exists(lock):
            try:
                os.unlink(lock)
            except (Exception,) as ex:
                logger.ingo('problem while removing {0}\n{1}'.format(
                    lock, ex))


def prepare_parser(parser):
    parser.add_option("-p", dest="project_name")
    parser.add_option("-r", dest="project_root",
                      default="/srv/projects/{project_name}/project")
    parser.add_option("--only", dest="project_only", default="")
    parser.add_option("--only-steps", dest="project_only_steps", default="")
    parser.add_option("--extra-args", dest="project_extra_args", default="")
    parser.add_option("--task",
                      dest="project_task", action="store", default="")
    return parser


def do_custom_parse(parser, options, args):
    options.project_root = options.project_root.format(**vars(options))
    if os.path.exists(options.project_root):
        options.tmpdir = options.project_root
    return parser, options, args


def get_callback_args(parser, options, args):
    OPTIONS['salt_function'] = 'mc_project.deploy'
    if options.project_task:
        OPTIONS['salt_function'] = 'mc_project.run_task'
    if not options.project_name:
        options.project_name = os.path.abspath(__file__).split(os.path.sep)[-5]
    OPTIONS['project_name'] = options.project_name
    args = [options.project_name]
    if (
        options.project_task
        and (options.project_only_steps or options.project_only)
    ):
        raise ValueError('task / (only/only_steps*) are mutually exclusive')
    if options.project_task:
        CMDS[0] += ' "{0}"'.format(options.project_task)
    if options.project_only:
        CMDS[0] += ' only="{0}"'.format(options.project_only)
    if options.project_only_steps:
        CMDS[0] += ' only_steps="{0}"'.format(options.project_only_steps)
    if options.project_extra_args:
        CMDS[0] += ' {0}'.format(options.project_extra_args)
    return args


def main():
    parser = OptionParser()
    tmpdir = os.environ.get('TMPDIR', '/tmp')
    parser.add_option("-l", dest="loglevel",
                      help="debug|error|info|all|quiet", default="info")
    parser.add_option("--async",
                      dest="async", action="store_false", default=True)
    parser.add_option("--retry-delay",
                      dest="delay", action="store", default=DEFAULT_DELAY)
    parser.add_option("--tmpdir", dest="tmpdir", default=tmpdir)
    parser.add_option("-t", '--timeout', type="int",
                      dest='timeout', default=DEFAULT_TIMEOUT)
    parser.add_option("--deploy-log", dest="deploy_log", default=LOG)
    parser.add_option("--deploy-lock", dest="deploy_lock", default=LOCK)
    parser = prepare_parser(parser)
    options, args = parser.parse_args()
    if options.loglevel not in ['debug', 'quiet', 'error', 'info', 'all']:
        raise ValueError('invalid loglevel')
    lvl = logging.getLevelName(
        {'all': 'debug',
         'quiet': 'error'}.get(options.loglevel, options.loglevel).upper())
    parser, options, args = do_custom_parse(parser, options, args)
    options.deploy_lock = options.deploy_lock.format(**vars(options))
    options.deploy_log = options.deploy_log.format(**vars(options))
    init_file_logging(options.deploy_log, lvl)
    stdout_tee = Tee(sys.stdout, sys.__stdout__)
    stderr_tee = Tee(sys.stderr, sys.__stderr__)
    logger.info('start')
    OPTIONS.update({'delay': options.delay})
    callback_args = get_callback_args(parser, options, args)
    test_deploy(callback_args=callback_args, **vars(options))
    try:
        args = [callback_args,
                options.loglevel,
                options.deploy_log,
                options.deploy_lock]
        ckwargs = copy.deepcopy(OPTIONS)
        if not getattr(options, 'async'):
            exitcode = deploy(*args, **ckwargs)
        else:
            exitcode = enter_mainloop(_run_deploy,
                                      args=args,
                                      kwargs=ckwargs,
                                      lockfile=options.deploy_lock,
                                      logfile=options.deploy_log,
                                      timeout=options.timeout,
                                      delay=options.delay,
                                      stderr_tee=stderr_tee,
                                      stdout_tee=stdout_tee)
    except ProcessError:
        logger.error('processerror')
        logger.error(traceback.format_exc())
        exitcode = 128
    except (TimeoutError,) as ex:
        exitcode = 127
        logger.error('Deployment has been killed after a timeout')
    except (Exception,) as ex:
        trace = traceback.format_exc()
        logger.error("Unknown error")
        logger.error('{0}'.format(ex))
        logger.error(trace)
        exitcode = 126
    if exitcode != -1 and is_locked(options.deploy_lock):
        while(is_locked(options.deploy_lock)):
            print("still locked")
            time.sleep(0.5)
    if exitcode == -1:
        exitcode = 0
        logger.info('Deployment is continued in background')
    elif exitcode:
        logger.error('Deployment failed')
    else:
        logger.info('Deployment success')
    # from now, every child log goes to a file
    toggle_log(False, True)
    # remove multiprocess handlers
    # as we completly biased the behavior
    if hasattr(atexit, '_exithandlers'):
        rorder = range(len(atexit._exithandlers))
        rorder.reverse()
        for i in rorder:
            if 'multiprocessing' in atexit._exithandlers[i][0].__module__:
                atexit._exithandlers.pop(i)
    sys.exit(exitcode)


if __name__ == '__main__':
    main()
