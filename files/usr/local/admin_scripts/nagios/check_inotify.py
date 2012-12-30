#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import,
                        division,
                        print_function,
                        unicode_literals)
__docformat__ = 'restructuredtext en'

import glob
import os
try:
    import argparse
    HAS_ARGPARSE = True
except ImportError:
    HAS_ARGPARSE = False
try:
    import optparse
    HAS_OPTPARSE = True
except ImportError:
    HAS_OPTPARSE = False
from subprocess import Popen, PIPE

import sys
import traceback
import socket


def popen(cargs=None, shell=True):
    if not cargs:
        cargs = []
    ret, ps = None, None
    if cargs:
        ps = Popen(cargs, shell=shell, stdout=PIPE, stderr=PIPE)
        ret = ps.communicate()
    return ret, ps


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
    if '/lxc/' in lxc:
        lxc = lxc.split('/lxc/', 1)[1]
    if lxc == 'MAIN_HOST' and os.path.isfile(envf):
        with open(envf) as fic:
            content = fic.read()
            if 'container=lxc' in content:
                lxc = socket.getfqdn()
    return lxc


class Check(object):
    def __init__(self):
        self._program = "check_inofiy"
        self._author = "Mathieu Le Marec - Pasquet (kiorky)"
        self._nick = "INOTIFY COUNTERS"
        self._ok = 0
        self._warning = 1
        self._critical = 2
        self._unknown = 3
        self._pending = 4
        self.parser = None
        self.args = None
        self.options = None

    def compute_perfdata(self, force=True):
        if force or not self._perfdata:
            self._perfdata += 'test=1'
        return self._perfdata

    def exit(self, code, msg='', perfdata=None):
        if perfdata:
            msg += '|{0}'.format(perfdata.strip())
        if msg:
            print (msg)
        sys.exit(code)

    def critical(self, msg='', perfdata=None):
        msg = '{0} CRITICAL - {1}'.format(self._nick, msg)
        self.exit(self._critical, msg=msg, perfdata=perfdata)

    def warning(self, msg='', perfdata=None):
        msg = '{0} WARNING - {1}'.format(self._nick, msg)
        self.exit(self._warning, msg=msg, perfdata=perfdata)

    def unknown(self, msg='', perfdata=None):
        msg = '{0} UNKNOWN - {1}'.format(self._nick, msg)
        self.exit(self._unknown, msg=msg, perfdata=perfdata)

    def ok(self, msg='', perfdata=None):
        msg = '{0} OK - {1}'.format(self._nick, msg)
        self.exit(self._ok, msg=msg, perfdata=perfdata)

    def opt_parser(self):
        default_ts = 128
        try:
            # try to get it from sysctls
            default_ts = int(popen(
                'sysctl fs.inotify.max_user_instances'
            )[0][0].split()[-1])
        except Exception:
            pass
        warning_ts = round(default_ts * 90 / 100)
        if True or not HAS_ARGPARSE:
            parser = self.parser = optparse.OptionParser()
            parser.add_option('-t', '--track-threshold',
                              default=500,
                              action='store', type='int',
                              dest='track',
                              help=('Warning watch instances threshold,'
                                    ' %(default)s]'))
            parser.add_option('-w', '--warning',
                              default=warning_ts,
                              action='store', type='int',
                              dest='warning',
                              help=('Warning watch instance threshold,'
                                    ' %(default)s]'))
            parser.add_option('-c', '--critical',
                              default=default_ts,
                              action='store', type='int',
                              dest='critical',
                              help=('Critical watch instance threshold,'
                                    ' %(default)s]'))
            (options, args) = parser.parse_args()
            self.args = vars(options)
            if self.args['warning'] >= self.args['critical']:
                self.unknown(
                    ('Warning thresold ({0}) should be lower than the '
                     'critical one ({1})').format(self.args['warning'],
                                                  self.args['critical']))

        else:
            parser = self.parser = argparse.ArgumentParser(
                prog=self._program,
                description=("Get Perfdata around inotify metrics"))
            parser.add_argument('-t', '--track-threshold',
                                default=500, const=500,
                                type=int, nargs='?',
                                dest='track',
                                help=('Warning watch instances threshold,'
                                      ' %(default)s]'))
            parser.add_argument('-w', '--warning',
                                default=warning_ts, const=warning_ts,
                                type=int, nargs='?',
                                dest='warning',
                                help=('Warning watch instance threshold,'
                                      ' %(default)s]'))
            parser.add_argument('-c', '--critical',
                                default=default_ts, const=default_ts,
                                type=int, nargs='?',
                                dest='critical',
                                help=('Critical watch instance threshold,'
                                      ' %(default)s]'))
            self.args = vars(parser.parse_args())
            if self.args['warning'] >= self.args['critical']:
                unknown_ret = ('Warning thresold ({0}) should be '
                               'lower than the '
                               'critical one ({1})')
                self.unknown(unknown_ret.format(self.args['warning'],
                                                self.args['critical']))

    def get_file_consumers(self):
        ret, ps = popen('lsof')
        lret = ret[0].split('\n')
        lret.sort()
        counters = {}
        for ix, i in enumerate(lret):
            parts = i.split()
            if not parts:
                continue
            process = parts[0].strip()
            pid = parts[1].strip()
            process = '{0}_{1}'.format(get_container(pid), process)
            counters[process] = counters.setdefault(process, 0) + 1
        data = []
        for i, val in counters.items():
            if val >= self.args['track']:
                data.append((i, val))
        data.sort(key=lambda x: (x[1], x[0]))
        data.reverse()
        return data

    def get_openfiles_counters(self):
        fs_enc = sys.getfilesystemencoding()
        ret, ps = popen('lsof')
        lines = ret[0].decode(fs_enc).splitlines()
        open_files = len(lines) - 1
        inot_files = len([line for line in lines  if 'anon_inode' in line])
        return {'open_files': open_files,
                'inotify_openfiles': inot_files}

    def get_watch_instances(self):
        data = []
        for fic in glob.glob('/proc/*/fd/*'):
            try:
                lnk = os.readlink(fic)
                if 'inotify' not in lnk:
                    continue
                data.append(fic)
            except Exception:
                continue
        counters = {}
        for ix, p in enumerate(data):
            pid = p.split('/fd/')[0].split('/')[-1]
            try:
                with open('/proc/{0}/cmdline'.format(pid)) as fic:
                    process = fic.read()
                    process = '{0}_{1}'.format(get_container(pid),
                                               fic.read().strip())
                    counters[process] = counters.setdefault(process, 0) + 1
            except (IOError, OSError):
                continue
        data = []
        for i, val in counters.items():
            data.append((i, val))
        data.sort(key=lambda x: (x[1], x[0]))
        data.reverse()
        return data

    def get_watch_instances_counters(self):
        data = self.get_watch_instances()
        sumd = sum([a[1] for a in data])
        return {'watch_instances': sumd}

    def run(self):
        self.opt_parser()
        perfdata = ''
        counters = {}
        for cbk in [self.get_watch_instances_counters,
                    self.get_openfiles_counters]:
            counters.update(cbk())
        for i, val in counters.items():
            perfdata += ' {0}={1}'.format(i, val)
        wi = counters.get('watch_instances', '')
        if wi:
            if wi > self.args['critical']:
                self.critical("{0} > {1}".format(wi, self.args['critical']),
                              perfdata=perfdata)
            elif wi > self.args['warning']:
                self.warning("{0} > {1}".format(wi, self.args['warning']),
                             perfdata=perfdata)
            elif wi < self.args['warning']:
                self.ok(perfdata=perfdata)
        self.unknown('No exit made before end of check, this is not normal.')


def main():
    try:
        check = Check()
        check.run()
    except Exception, e:
        trace = traceback.format_exc()
        print('Unknown error UNKNOW - {0}'.format(e))
        print(trace)
        sys.exit(3)


if __name__ == "__main__":
    main()

# vim:set et sts=4 ts=4 tw=80:
