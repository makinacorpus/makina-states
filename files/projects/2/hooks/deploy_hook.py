#!/usr/bin/env python
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
'''
corpus Deploy hook
===================

This will call the mc_project_<API>.deploy function in turn

Once a deployment has been triggered:

    - nothing can kill it except a kill -9
    - main loop (and not main program!)  can maybe kill it after a timeout
    - Neither terminal closure or keyboard interrupt (SIGINT)
      can stop the deployment
    - the deploy function is anyway executed in background while output
      is given in realtime to the connected terminal


'''
import traceback
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

from Queue import Empty, Queue
import logging
from subprocess import Popen, PIPE
from threading import Thread


logger = logging.getLogger('deploy-main')
worker_logger = logging.getLogger('deploy-worker')
to_logger = logging.getLogger('timeout-watcher')
rawlogger = logging.getLogger('rawlogger')
rawlogger.propagate = False


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
        self.dup = dup
        self.orig = orig
        self.output = output
        self.file_output = file_output

    def write(self, s=''):
        if isinstance(s, unicode):
            s = s.encode('utf-8')
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
    e do not ignore sigterm and even do it.
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
                if isinstance(line, unicode):
                    line = str(line.encode('utf-8'))
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


def stream_watcher(io_q, p_q, identifier, stream):
    for line in stream:
        io_q.put((identifier, line))
    if not stream.closed:
        stream.close()
    p_q.put('d')


def deploy(name, loglevel, logfile, lock, **kwargs):
    '''
    The real deploy work is done here !
    '''
    # think to remove locks in subshell
    # if main program has aborted before end of deployment
    worker_logger.info('start - deploy')
    logflush()
    with open(lock, 'w') as fic:
        fic.write('locked')
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
        cmds = [
            ['salt-call', '--local', '--retcode-passthrough',
                '-l{0}'.format(loglevel), 'mc_project.deploy', name]
        ]
        for cmd in cmds:
            try:
                io_q = Queue()
                p_q = Queue()
                if isinstance(cmd, list):
                    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
                else:
                    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
                # we are already daemonized multiprocess
                # so the only option now is to thread out to
                # parrallelize
                threads = []
                threads.append(
                    Thread(target=stream_watcher, name='stderr-watcher',
                           args=(io_q, p_q, 'STDERR', proc.stderr)).start()
                )
                threads.append(
                    Thread(target=stream_watcher, name='stdout-watcher',
                           args=(io_q, p_q, 'STDOUT', proc.stdout)).start()
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
                if proc.returncode:
                    raise Exception('stopped due to non zero return code')
            except Exception, ex:
                worker_logger.error('{0} failed'.format(cmd))
                worker_logger.error("{0}".format(ex))
                logflush()
                exitcode = 1
                break
        if not exitcode:
            worker_logger.info('Worker has deployed sucessfully')
            logflush()
        else:
            worker_logger.error('Worker has failed the deployment')
            logflush()
    finally:
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
        except TimeoutError, ex:
            blind_send(messages_queue, ex.message, logfile=logfile)
            blind_send(protocol_queue, 'TIMEOUT', logfile=logfile)
            resume_signals()
            trace = traceback.format_exc()
        except Exception, ex:
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
                   timeout=None):
    '''Manage a multiprocessing pool

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


def test_deploy(deploy_lock, log):
    if os.path.exists(deploy_lock):
        logger.info(
            "A deployment seems already in progress\n"
            "If something did go wrong, please "
            "delete the {DEPLOY_LOCK} file".format(
                DEPLOY_LOCK=deploy_lock))
        logger.info(
            "You can attach to and read the log file with:\n"
            "   tail -f {0}".format(log))
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
            except Exception, ex:
                logger.ingo('problem while removing {0}\n{1}'.format(
                    lock, ex))


def main():
    parser = OptionParser()
    tmpdir = os.environ.get('TMPDIR', '/tmp')
    parser.add_option("-l", dest="loglevel",
                      help="debug|error|info|all|quiet", default="info")
    parser.add_option("--async", dest="async", action="store_false", default=True)
    parser.add_option("-p", dest="project_name")
    parser.add_option("-r", dest="project_root",
                      default="/srv/projects/{0}/project")
    parser.add_option("--tmpdir", dest="tmpdir", default=tmpdir)
    parser.add_option("-t", '--timeout', type="int",
                      dest='timeout', default=5 * 60 * 60)
    parser.add_option("--deploy-log", dest="deploy_log",
                      default="{0}/makina-states.{1}-deploy.log")
    parser.add_option("--deploy-lock", dest="deploy_lock",
                      default="{0}/.makina-states.{1}-deploy.lock")
    options, args = parser.parse_args()
    if not options.loglevel in ['debug', 'quiet', 'error', 'info', 'all']:
        raise ValueError('invalid loglevel')
    lvl = logging.getLevelName(
        {'all': 'debug',
         'quiet': 'error'}.get(options.loglevel, options.loglevel).upper())
    options.project_root = options.project_root.format(options.project_name)
    if os.path.exists(options.project_root):
        options.tmpdir = options.project_root
    options.deploy_lock = options.deploy_lock.format(options.tmpdir,
                                                     options.project_name)
    options.deploy_log = options.deploy_log.format(options.tmpdir,
                                                   options.project_name)
    init_file_logging(options.deploy_log, lvl)
    Tee(sys.stdout, sys.__stdout__)
    Tee(sys.stderr, sys.__stderr__)
    test_deploy(options.deploy_lock, options.deploy_log)
    logger.info('start')
    try:
        args = [options.project_name,
                options.loglevel,
                options.deploy_log,
                options.deploy_lock]
        if not options.async:
            exitcode = deploy(*args)
        else:
            exitcode = enter_mainloop(_run_deploy, args=args,
                                      lockfile=options.deploy_lock,
                                      logfile=options.deploy_log,
                                      timeout=options.timeout)
    except ProcessError:
        logger.error('processerror')
        exitcode = 128
    except TimeoutError, ex:
        exitcode = 127
        logger.error('Deployment has been killed after a timeout')
    except Exception, ex:
        trace = traceback.format_exc()
        logger.error("Unknown error")
        logger.error('{0}'.format(ex))
        logger.error(trace)
        exitcode = 126
    if exitcode != -1 and is_locked(options.deploy_lock):
        while(is_locked(options.deploy_lock)):
            print("o")
            pass
    if exitcode == -1:
        exitcode = 0
        logger.info('Deployment is continued in background')
    elif exitcode:
        logger.error('Deployment failed')
    else:
        logger.info('Deployment sucess')
    # from now, every child log goes to a file
    toggle_log(False, True)
    # remove multiprocess handlers
    # as we completly biased the behavior
    rorder = range(len(atexit._exithandlers))
    rorder.reverse()
    for i in rorder:
        if 'multiprocessing' in atexit._exithandlers[i][0].__module__:
            atexit._exithandlers.pop(i)
    sys.exit(exitcode)


if __name__ == '__main__':
    main()

#
