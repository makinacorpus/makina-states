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
import copy
import subprocess


_cache = {}


def init_environ(_o=None):
    key = 'init_environ'
    try:
        return _cache[key]
    except KeyError:
        try:
            with open('/proc/1/environ') as fic:
                _cache[key] = fic.read()
        except (IOError, OSError):
            _cache[key] = ''
    return _cache[key]


def _is_travis(_o=None):
    is_nodetype = None
    val = "{0}".format(os.environ.get('TRAVIS', 'false')).lower()
    if val in ['y', 't', 'o', 'true', '1']:
        is_nodetype = True
    elif val:
        is_nodetype = False
    return is_nodetype


def _is_docker(_o=None):
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
        docker = 'docker' in init_environ()
    if not docker:
        for i in ['.dockerinit', '/.dockerinit']:
            if os.path.exists(i):
                docker = True
    return docker


def _is_lxc(_o=None):
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
    lxc = None
    if _is_docker(_o=_o):
        lxc = False
    if lxc is None:
        try:
            lxc = __grains__.get('makina.lxc', None)
        except (ValueError, NameError, IndexError):
            pass
    if lxc is None:
        try:
            cgroups = open('/proc/1/cgroup').read().splitlines()
            lxc = not '/' == [a.split(':')[-1]
                              for a in cgroups
                              if ':cpu:' in a or
                              ':cpuset:' in a][-1]
        except Exception:
            lxc = False
    return lxc and not _is_docker(_o=_o)


def _is_container(_o=None):
    return _is_docker() or _is_lxc(_o=_o)


def _devhost_num(_o=None):
    return ''
    # devhost will be removed from makina-states sooner or later
    # if os.path.exists('/root/vagrant/provision_settings.sh'):
    #     num = subprocess.Popen(
    #         'bash -c "'
    #         '. /root/vagrant/provision_settings.sh;'
    #         'echo \$DEVHOST_NUM"',
    #         shell=True, stdout=subprocess.PIPE
    #     ).stdout.read().strip()
    # if not num:
    #     num = '0'
    # return num


def _routes(_o=None):
    routes, default_route = [], {}
    troutes = subprocess.Popen(
        'bash -c "netstat -nr"',
        shell=True, stdout=subprocess.PIPE
    ).stdout.read().strip()
    for route in troutes.splitlines()[1:]:
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
                default_route = copy.deepcopy(droute)
            routes.append(droute)
        except Exception:
            continue
    return routes, default_route, default_route.get('gateway', None)


def _is_vm(_o=None):
    ret = False
    if _is_container(_o=_o):
        ret = True
    return ret


def _is_devhost(_o=None):
    return _devhost_num(_o=_o) != ''


def _get_msconf(param, _o=None):
    if _o is None:
        _o = __opts__
    nd = os.path.join(
        _o.get('config_dir', '/etc/salt'), 'makina-states')
    try:
        with open(os.path.join(nd, param)) as fic:
            content = fic.read().strip()
    except (OSError, IOError):
        content = ''
    return content


def _nodetype(_o=None):
    return _get_msconf('nodetype', _o=_o)


def _is_vagrantvm(_o=None):
    return _nodetype(_o=_o) in ['vagrantvm']


def _is_kvm(_o=None):
    return _nodetype(_o=_o) in ['kvm']


def _is_server(_o=None):
    return _nodetype(_o=_o) in ['server']


def _is_laptop(_o=None):
    return _nodetype(_o=_o) in ['laptop']


def _is_upstart(_o=None):
    if os.path.exists('/var/log/upstart'):
        return True
    return False


def _is_systemd(_o=None):
    try:
        is_ = os.readlink('/proc/1/exe') == '/lib/systemd/systemd'
    except (IOError, OSError):
        is_ = False
    rd = '/run/systemd'
    try:
        # ubuntu trusty has a light systemd running ...
        if os.path.exists(rd) and len(os.listdir(rd)) > 4:
            is_ = True
    except (IOError, OSError):
        is_ = False
    return is_


def _pgsql_vers(_o=None):
    vers = {'details': {}, 'global': {}}
    for i in ['9.0', '9.1', '9.3', '9.4', '10.0', '10.1']:
        pid = (
            '/var/lib/postgresql/{0}'
            '/main/postmaster.pid'.format(i))
        dbase = (
            '/var/lib/postgresql/{0}'
            '/main/base'.format(i))
        dglobal = (
            '/var/lib/postgresql/{0}'
            '/main/global'.format(i))
        running = False
        has_data = False
        if os.path.exists(pid):
            running = True
        for d in [dbase, dglobal]:
            if not os.path.exists(d):
                continue
            if os.listdir(d) > 2:
                has_data = True
        if running or has_data:
            vers['global'][i] = True
            vers['details'][i] = {'running': running,
                                  'has_data': has_data}
    return vers


def get_makina_grains(_o=None):
    '''
    '''
    routes, default_route, gw = _routes(_o=_o)
    grains = {'makina.upstart': _is_upstart(_o=_o),
              'makina.systemd': _is_systemd(_o=_o),
              'makina.nodetype': _nodetype(_o=_o),
              'makina.container': _is_container(_o=_o),
              'makina.server': _is_server(_o=_o),
              'makina.vm': _is_vm(_o=_o),
              'makina.laptop': _is_laptop(_o=_o),
              'makina.travis': _is_travis(_o=_o),
              'makina.lxc': _is_lxc(_o=_o),
              'makina.docker': _is_docker(_o=_o),
              'makina.kvm': _is_kvm(_o=_o),
              'makina.vagrantvm': _is_vagrantvm(_o=_o),
              'makina.devhost': _is_devhost(_o=_o),
              'makina.devhost_num': _devhost_num(_o=_o),
              'makina.pgsql_vers': _pgsql_vers(_o=_o),
              'makina.default_route': default_route,
              'makina.default_gw': gw,
              'makina.routes': routes}
    return grains
# vim:set et sts=4 ts=4 tw=80:
