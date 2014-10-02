#!/usr/bin/env python
"""
Wrapper for check_mysql_health to autoconnect on debian
this also ensure to execute one check at a time as
we had some issues with too much check_mysql_health concurrent (even different)
checks
"""
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import os
import re
import time
import pprint
import sys
import subprocess

t = time.time()
lock = os.environ.get('TMPLOCK', "/tmp/mysqlautoconnect.lock")
CONFDIR = os.environ.get('CONFDIR', '/etc/mysql')
CNF = os.environ.get('CNF', CONFDIR + '/debian.cnf')


def find_val(content, val):
    for i in [a for a in content.splitlines() if '=' in a]:
        if i.startswith(val):
            return re.split(' +', i)[2]
    return ''


def main():
    ret = 124
    try:
        os.chdir(os.path.dirname(__file__))
        while True:
            if os.path.exists(lock):
                cst = int(os.stat(lock).st_ctime)
                if abs(t-cst) > 60:
                    os.unlink(lock)
            else:
                break
        argv = sys.argv[:]
        args = []
        if os.path.exists(CNF):
            try:
                fic = open(CNF)
                content = fic.read()
                fic.close()
                if '--hostname' not in argv:
                    args += ['--hostname', find_val(content, 'host')]
                if '--socket' not in argv:
                    args += ['--socket', find_val(content, 'socket')]
                if '--username' not in argv:
                    args += ['--username', find_val(content, 'user')]
                if '--password' not in argv:
                    args += ['--password', find_val(content, 'password')]
            except IOError:
                pass
        if '--mode' not in argv:
            args += ['--mode', 'connection-time']
        args = [a.strip() for a in args]
        args.extend(argv[1:])
        p = subprocess.Popen(["./check_mysql_health"] + args[1:],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        ret = p.wait()
        sys.stdout.write(p.stdout.read())
        sys.stderr.write(p.stderr.read())
    finally:
        if os.path.exists(lock):
            os.unlink(lock)
    sys.exit(ret)

if __name__ == '__main__':
    main()
# vim:set et sts=4 ts=4 tw=80: 
