#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import,
                        division,
                        print_function)
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

__checks__ = []


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
    return lxc


def is_lxc():
    container = get_container(1)
    if container not in ['MAIN_HOST']:
        return True
    return False


def filter_host_pids(pids):
    thishost = get_container(1)
    return [a for a in pids if get_container(a) == thishost]


class BaseCheck(object):
    def __init__(self):
        self._program = self.__class__.__name__
        self._author = "Mathieu Le Marec - Pasquet (kiorky)"
        self._nick = self._program.replace('check_', '')
        self._ok = 0
        self._warning = 1
        self._critical = 2
        self._unknown = 3
        self._pending = 4
        self._default_status = "ok"
        self.parser = None
        self.args = None
        self.options = None
        self._tagmap = {self._warning: "warning",
                        self._critical: "critical",
                        self._ok: "ok",
                        self._pending: "pending",
                        self._unknown: "unknown"}

    def exit(self, code, tag=None, msg=None, perfdata=None, exit=True):
        try:
            code = int(code)
            if code not in self._tagmap:
                code = self._unknown
        except (ValueError, TypeError):
            code = self._unknown
        if not tag:
            tag = self._tagmap.get(code, "unknown")
        if not msg:
            msg = ''
        if not perfdata:
            perfdata = ''
        tag = tag.upper()
        if msg:
            msg = msg.strip()
            if not msg.startswith('- '):
                msg = ' - {0}'.format(msg)
        if perfdata and not perfdata.startswith('|'):
            perfdata = '|{0}'.format(perfdata.strip())
        print ("{0}{1}{2}".format(tag, msg, perfdata))
        if exit:
            sys.exit(code)

    def _exit_(self, tag, msg, perfdata):
        msg = '{0} {2} {1}'.format(self._nick, msg, tag.upper())

    def critical(self, msg='', perfdata=None):
        self.exit(self._critical, msg=msg, perfdata=perfdata)

    def warning(self, msg='', perfdata=None):
        self.exit(self._warning, msg=msg, perfdata=perfdata)

    def unknown(self, msg='', perfdata=None):
        self.exit(self._unknown, msg=msg, perfdata=perfdata)

    def ok(self, msg='', perfdata=None):
        self.exit(self._ok, msg=msg, perfdata=perfdata)

    def opt_parser(self):
        ddir = '/data/burp'
        if True or not HAS_ARGPARSE:
            parser = self.parser = optparse.OptionParser()
            #parser.add_option('-d', '--data-dir',
            #                  default=ddir,
            #                  action='store', type='string',
            #                  dest='data',
            #                  help=('burp data dir'))
            (options, args) = parser.parse_args()
            self.args = vars(options)
        else:
            parser = self.parser = argparse.ArgumentParser(
                prog=self._program,
                description=("Get Perfdata around burp metrics"))
            #parser.add_argument('-t', '--track-threshold',
            #                    default=ddir, const=ddir,
            #                    type=str, nargs='?',
            #                    dest='ddir',
            #                    help='burp data dir')
            self.args = vars(parser.parse_args())
        #if not os.path.exists(self.args['data']):
        #    self.unknown(
        #        ('Warning data dir {data}'
        #         ' does not exists').format(**self.args))

    def selftest(self, status=None):
        '''
        Return a string for the status

        one of unkown/ok/warning/critical
        '''
        msg = ""
        if not status:
            status = self._default_status
        return status, msg

    def counters(self, status=None):
        '''
        Return a dict of perfdata
        '''
        if not status:
            status = self._default_status
        return {}

    def mangle_perfdata(self, status="ok", counters=None):
        perfdata = ''
        if not status:
            status = self._default_status
        if not counters:
            counters = {}
        if counters:
            for i, val in counters.items():
                perfdata += ' {0}={1}'.format(i, val)
        return perfdata

    def run(self):
        self.opt_parser()
        status, msg = self.selftest()
        counters = self.counters(status=status)
        perfdata = self.mangle_perfdata(status=status, counters=counters)
        getattr(self, status)(msg, perfdata=perfdata)
        self.unknown('No exit made before end of check, this is not normal.')


class dummy_check(BaseCheck):

    def selftest(self, status="ok"):
        return "critical", ""

    def counters(self, status="ok"):
        return {"a": 1}

for i in [
    # add your checks here
    dummy_check
]:
    __checks__.append(i)


def main():
    try:
        for Check in __checks__:
            check = Check()
            check.run()
    except Exception, e:
        trace = traceback.format_exc()
        print('Unknown error UNKNOW - {0}'.format(e))
        print(trace)
        sys.exit(3)


if __name__ == '__main__':
    main()

# vim:set et sts=4 ts=4 tw=80:
