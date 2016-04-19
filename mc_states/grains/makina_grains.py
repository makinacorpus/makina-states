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


def init_environ():
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


def _is_travis():
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
    if _o is None:
        try:
            _o = __opts__
        except NameError:
            _o = {}
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
    if _o is None:
        try:
            _o = __opts__
        except NameError:
            _o = {}
    lxc = None
    if _is_docker():
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
    if not lxc:
        try:
            content = open('/proc/1/environ').read()
            lxc = 'container=lxc' in content
        except Exception:
            lxc = False
    return lxc and not _is_docker(_o=_o)


def _is_container():
    return _is_docker() or _is_lxc()


def _devhost_num():
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


def _routes():
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


def _is_vm():
    ret = False
    if _is_container():
        ret = True
    return ret


def _is_devhost():
    return _devhost_num() != ''


def _get_msconf(param):
    try:
        with open(
            os.path.join('/etc/makina-states', param)
        ) as fic:
            content = fic.read().strip()
    except (OSError, IOError):
        content = ''
    return content


def _nodetype():
    return _get_msconf('nodetype')


def _is_vagrantvm():
    return _get_msconf('nodetype') in ['vagrantvm']


def _is_kvm():
    return _get_msconf('nodetype') in ['kvm']


def _bootsalt_mode():
    return _get_msconf('bootsalt_mode')


def _is_upstart():
    if os.path.exists('/var/log/upstart'):
        return True
    return False


def _is_systemd():
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


def _pgsql_vers():
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


def get_makina_grains():
    '''
    '''
    routes, default_route, gw = _routes()
    grains = {'makina.upstart': _is_upstart(),
              'makina.systemd': _is_systemd(),
              'makina.bootsalt_mode': _bootsalt_mode(),
              'makina.nodetype': _nodetype(),
              'makina.container': _is_container(),
              'makina.vm': _is_vm(),
              'makina.travis': _is_travis(),
              'makina.lxc': _is_lxc(),
              'makina.docker': _is_docker(),
              'makina.kvm': _is_kvm(),
              'makina.vagrantvm': _is_vagrantvm(),
              'makina.devhost': _is_devhost(),
              'makina.devhost_num': _devhost_num(),
              'makina.pgsql_vers': _pgsql_vers(),
              'makina.default_route': default_route,
              'makina.default_gw': gw,
              'makina.routes': routes}
    return grains
# vim:set et sts=4 ts=4 tw=80:
