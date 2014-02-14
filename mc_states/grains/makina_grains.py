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

def get_makina_grains():
    '''
    '''
    grains = {
        'makina.upstart': False,
        'makina.lxc': False,
        'makina.docker': False,
        'makina.devhost_num': '0',
    }
    if os.path.exists('.dockerinit'):
        grains['makina.docker'] = True
    grains['makina.lxc'] = is_lxc()
    if os.path.exists('/.dockerinit'):
        grains['makina.docker'] = True
    if os.path.exists('/var/log/upstart'):
        grains['makina.upstart'] = True
    num = subprocess.Popen(
        'bash -c "if [ -f /root/vagrant/provision_settings.sh ];then . /root/vagrant/provision_settings.sh;echo \$DEVHOST_NUM;fi"',
        shell=True, stdout=subprocess.PIPE
    ).stdout.read().strip()

    if num:
        grains['makina.devhost_num'] = num
    return grains


# vim:set et sts=4 ts=4 tw=80:
