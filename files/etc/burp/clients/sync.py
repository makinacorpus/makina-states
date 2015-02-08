#!/usr/bin/env python
# -*- coding: utf-8 -*-
{% set data = salt['mc_burp.settings']() %}
__docformat__ = 'restructuredtext en'
import subprocess
import sys
import os
import time
ret = 0
timeout = 60 * 2
timeout = 15
batch = 20
done = {}
clients = [{% for client in data['clients'] %}"{{client}}", {%endfor%}]


def async_backup(cmd):
    print "lauching in background: {0}".format(cmd)
    process = subprocess.Popen(cmd,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    return process
todo = []
missed = []
# init & launch
for i in clients:
    if os.path.isdir("{{data.server_conf.directory}}/"+i):
        if not os.path.exists("{{data.server_conf.directory}}/"+i):
            os.makedirs("{{data.server_conf.directory}}/"+i)
        if not os.path.exists("{{data.server_conf.directory}}/"+i+"/current"):
            with open(
                "{{data.server_conf.directory}}/{0}/backup".format(i), 'w'
            ) as fic:
                fic.write('\n')
        todo.append("/etc/burp/clients/{0}/sync.sh".format(i))


def check_timeout(will_timeout):
    t = time.time()
    if t >= will_timeout:
        raise ValueError('Timeout !')


while todo:
    # poll per 10
    now = time.time()
    doing = []
    for i in range(batch):
        try:
            doing.append(todo.pop())
        except:
            pass
    if not doing:
        todo = False
    else:
        will_timeout = now + timeout
        syncs = {}
        for cmd in doing:
            syncs[cmd] = async_backup(cmd)
        try:
            while syncs:
                check_timeout(will_timeout)
                for cmd in [a for a in syncs]:
                    if syncs[cmd].poll() is not None:
                        done[cmd] = syncs.pop(cmd)
            check_timeout(will_timeout)
        except ValueError:
            for i in [a for a in syncs]:
                missed.append("Missed {0}".format(i))
            pr = syncs.pop(i)
            pr.kill()

for a, p in done.items():
    if p.returncode:
        print "Missed {0} (1)".format(a, p.returncode)
        print p.stdout.read()
        print p.stderr.read()
        ret = 1
        missed.append(a)

if missed:
    print "Missed:"
    for i in missed:
        print "    - {0}".format(i)
sys.exit(ret)
# vim:set et sts=4 ts=4 tw=80:
