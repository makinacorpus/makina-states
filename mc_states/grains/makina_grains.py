#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Makina custom grains
=====================

makina.upstart
    true if using upstart
makina.lxc
    true if inside an lxc container
makina.docker
    true if inside a docker container
makina.devhost_num
    devhost num if any
'''

import os
import subprocess


def is_docker():
    """
    Return true if we find a system or grain flag
    that explicitly shows us we are in a DOCKER context
    """
    docker = False
    try:
        docker = bool(__grains__.get('makina.docker'))
    except (ValueError, NameError, IndexError):
        pass
    if not docker:
        try:
            docker = 'docker' in open('/proc/1/environ').read()
        except (IOError, OSError):
            docker = False
    if not docker:
        if os.path.exists('.dockerinit'):
            docker = True
    return docker


def is_lxc():
    """
    Return true if we find a system or grain flag
    that explicitly shows us we are in a LXC context

    in case of a container, we have the container name in cgroups
    else, it is equal to /

    in lxc:
        ['11:name=systemd:/user/1000.user/1.session',
        '10:hugetlb:/thisname',
        '9:perf_event:/thisname',
        '8:blkio:/thisname',
        '7:freezer:/thisname',
        '6:devices:/thisname',
        '5:memory:/thisname',
        '4:cpuacct:/thisname',
        '3:cpu:/thisname',
        '2:cpuset:/thisname']

    in host:
        ['11:name=systemd:/',
        '10:hugetlb:/',
        '9:perf_event:/',
        '8:blkio:/',
        '7:freezer:/',
        '6:devices:/',
        '5:memory:/',
        '4:cpuacct:/',
        '3:cpu:/',
        '2:cpuset:/']
    """
    lxc = False
    try:
        lxc = bool(__grains__.get('makina.lxc'))
    except (ValueError, NameError, IndexError):
        pass
    if not lxc:
        try:
            cgroups = open('/proc/1/cgroup').read().splitlines()
            lxc = not '/' == [a.split(':')[-1]
                              for a in cgroups
                              if ':cpu:' in a or
                              ':cpuset:' in a][-1]
        except Exception:
            lxc = False
    return lxc


def _devhost_num():
    num = subprocess.Popen(
        'bash -c "if [ -f /root/vagrant/provision_settings.sh ];'
        'then . /root/vagrant/provision_settings.sh;'
        'echo \$DEVHOST_NUM;fi"',
        shell=True, stdout=subprocess.PIPE
    ).stdout.read().strip()
    return num


def _is_devhost():
    return _devhost_num() != ''


def get_makina_grains():
    '''
    '''
    grains = {
        'makina.upstart': False,
        'makina.lxc': False,
        'makina.docker': False,
        'makina.devhost_num': '0',
        'makina.default_route': {},
        'makina.routes': [],
    }
    grains['makina.lxc'] = is_lxc()
    grains['makina.docker'] = is_docker()
    if os.path.exists('/var/log/upstart'):
        grains['makina.upstart'] = True
    num = _devhost_num()
    routes = subprocess.Popen(
        'bash -c "netstat -nr"',
        shell=True, stdout=subprocess.PIPE
    ).stdout.read().strip()
    for route in routes.splitlines()[1:]:
        try:
            parts = route.split()
            if 'dest' in parts[0].lower():
                continue
            droute = {'iface': parts[-1],
                      'gateway': parts[1],
                      'genmask': parts[2],
                      'flags': parts[3],
                      'mss': parts[4],
                      'window': parts[5],
                      'irtt': parts[6]}
            if parts[0] == '0.0.0.0':
                grains.update({'makina.default_route': droute})
            grains['makina.routes'].append(droute)
        except Exception:
            continue
    if num:
        grains['makina.devhost_num'] = num
    return grains
# vim:set et sts=4 ts=4 tw=80:
