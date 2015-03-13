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

__docformat__ = 'restructuredtext en'
import os
import subprocess

from mc_states.modules.mc_lxc import (
    is_lxc)


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
    if os.path.exists('.dockerinit'):
        grains['makina.docker'] = True
    grains['makina.lxc'] = is_lxc()
    if os.path.exists('/.dockerinit'):
        grains['makina.docker'] = True
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
