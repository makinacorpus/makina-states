#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import,
                        division,
                        print_function,
                        unicode_literals)
__docformat__ = 'restructuredtext en'

import sys
import glob
import re
import datetime
import gzip
import zlib
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
import traceback


def get_tdint(td):
    return int(
        (td.microseconds
            + (td.seconds + td.days * 24 * 3600) * 10**6) / 10.0**6)


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
    if '/lxc' in lxc:
        lxc = lxc.split('/lxc/', 1)[1]
    if lxc == 'MAIN_HOST' and os.path.isfile(envf):
        with open(envf) as fic:
            content = fic.read()
            if 'container=lxc' in content:
                lxc = socket.getfqdn()
    return lxc


class Check(object):
    def __init__(self):
        self._program = "check_burp_counters"
        self._author = "Mathieu Le Marec - Pasquet (kiorky)"
        self._nick = self._program.replace('check_', '')
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
        ddir = '/data/burp'
        if True or not HAS_ARGPARSE:
            parser = self.parser = optparse.OptionParser()
            parser.add_option('-d', '--data-dir',
                              default=ddir,
                              action='store', type='string',
                              dest='data',
                              help=('burp data dir'))
            (options, args) = parser.parse_args()
            self.args = vars(options)
        else:
            parser = self.parser = argparse.ArgumentParser(
                prog=self._program,
                description=("Get Perfdata around burp metrics"))
            parser.add_argument('-t', '--track-threshold',
                                default=ddir, const=ddir,
                                type=str, nargs='?',
                                dest='ddir',
                                help='burp data dir')
            self.args = vars(parser.parse_args())
        if not os.path.exists(self.args['data']):
            self.unknown(
                ('Warning data dir {data}'
                 ' does not exists').format(**self.args))

    def get_burp_times(self):
        counters = {}
        time_counters = {}
        size_counters = {}
        for ficp in glob.glob('{0}/*/current/log.gz'.format(self.args['data'])):
            try:
                with gzip.open(ficp) as fic:
                    host = ficp.replace(
                        '//', '/').split(
                            self.args['data'])[1].split('/')[1]
                    content = fic.read()
                    if hasattr(content, 'decode'):
                        content = content.decode()
                    lines = content.split('\n')
                    bib = 'Bytes in backup'
                    line = [a for a in lines if bib in a]
                    # backup size
                    if line:
                        line = line[0]
                        try:
                            ibib = int(
                                re.sub(
                                    '.*{0}:\s+([0-9]+)\s+.*'.format(bib), '\\1',
                                    line))
                        except ValueError:
                            ibib = 0
                        if ibib:
                            size_counters['size_{0}'.format(host)] = ibib
                    # backup time
                    bib = 'Start time:'
                    sline = [a for a in lines if bib in a]
                    bib = ' End time:'
                    eline = [a for a in lines if bib in a]
                    if sline and eline:
                        try:
                            sline = sline[0].split(':', 1)[1].strip()
                            eline = eline[0].split(':', 1)[1].strip()
                            start = datetime.datetime.strptime(
                                sline, '%Y-%m-%d %H:%M:%S')
                            end = datetime.datetime.strptime(
                                eline, '%Y-%m-%d %H:%M:%S')
                            diff = abs(end - start)
                        except (ValueError, IndexError) as exc:
                            diff = None
                        if diff:
                            ms = get_tdint(diff)
                            time_counters['time_{0}'.format(host)] = ms
            except (IOError, OSError) as exc:
                continue
        counters.update(size_counters)
        counters.update(time_counters)
        vt_counters = [a for a in time_counters.items()]
        vt_counters.sort(key=lambda x: int(1000*x[1]))
        st_counters = [a for a in size_counters.items()]
        st_counters.sort(key=lambda x: int(x[1]))
        return counters

    def get_watch_instances_counters(self):
        data = self.get_watch_instances()
        sumd = sum([a[1] for a in data])
        return {'watch_instances': sumd}

    def run(self):
        self.opt_parser()
        perfdata = ''
        counters = {}
        for cbk in [self.get_burp_times,
                   ]:
            counters.update(cbk())
        for i, val in counters.items():
            perfdata += ' {0}={1}'.format(i, val)
        wi = counters.get('watch_instances', '')
        if counters:
            self.ok(perfdata=perfdata)
        self.unknown('No exit made before end of check, this is not normal.')


def main():
    try:
        check = Check()
        check.run()
    except (Exception,) as e:
        trace = traceback.format_exc()
        print('Unknown error UNKNOW - {0}'.format(e))
        print(trace)
        sys.exit(3)


if __name__ == "__main__":
    main()

# vim:set et sts=4 ts=4 tw=80:
