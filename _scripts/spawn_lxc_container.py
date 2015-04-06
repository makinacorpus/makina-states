#!/usr/bin/env python
from __future__ import absolute_import, division,  print_function
__docformat__ = 'restructuredtext en'

import shutil
import os
import time
import urllib2
import hashlib
import difflib
import sys
import traceback
import re
import socket
import argparse
from subprocess import Popen, PIPE
socket.setdefaulttimeout(2)

DEFAULT_BR = 'lxcbr1'
DEFAULT_CONTAINER = 'makina-states-trusty'
DESCRIPTION = '''
Create a container from another container
If the IP address or the MAC address is not specified, it will be generated.

Examples:
{name} -n mytest
{name} -n mytest -s overlayfs
{name} -n mytest --ip=10.5.0.20
{name} -n mytest -o odoo
'''


def popen(cargs=None, shell=True, log=True):
    if log:
        print('Running: {0}'.format(cargs))
    if not cargs:
        cargs = []
    ret, ps = None, None
    if cargs:
        ps = Popen(cargs, shell=shell, stdout=PIPE, stderr=PIPE)
        ret = ps.communicate()
    return ret, ps


def check_md5(filep, md5=None):
    if not os.path.exists(filep):
        raise OSError('{0} does not exists'.format(filep))
    if md5:
        with open(filep, 'rb') as fic:
            cmd5 = hashlib.md5(fic.read()).hexdigest()
        if cmd5 != md5:
            raise ValueError(
                'md5sum failed({0}) current: {1} != {2}'
                ''.format(filep, cmd5, md5))
    else:
        print('WARNING: MD5 check skipped')


def system(cmd):
    return os.system(cmd)


def clone_template(origin, new, snapshot=None):
    args = ''
    if snapshot in ['overlayfs', 'aufs']:
            args += ' -s -B {0}'.format(snapshot)
    ret, ps = popen('lxc-clone -o "{0}" -n "{1}"'
                    '{2}'.format(origin, new, args))
    if ps.returncode:
        print(ret[0])
        print(ret[1])
        print('error while creating {0} from {1}'
              ''.format(new, origin))
        sys.exit(1)


def edit_config(lxc_config, bridge, ip, mac):
    with open(lxc_config) as fic:
        content = fic.read()
    ocontent = content
    configs = {'lxc.network.hwaddr': mac,
               'lxc.network.link': bridge,
               'lxc.network.ipv4': ip}
    for k in configs:
        val = configs[k]
        # REPLACE ONLY THE FIRST BRIDGE !
        ocontent = re.sub("{0} *=.*".format(k),
                          "{0} = {1}".format(k, val),
                          ocontent, count=1)
    if ocontent != content:
        print('\n'.join(difflib.unified_diff(content.splitlines(),
                                             ocontent.splitlines())))
        print('We overwrote lxc with those above new settings')
        print('A backup of the previous config exists in'
              ' {0}.bak'.format(lxc_config))
        with open(lxc_config+".bak", 'w') as fic:
            fic.write(content)
        with open(lxc_config, 'w') as fic:
            fic.write(ocontent)


def get_available_mac():
    '''.'''
    return '00:16:3e:aa:c0:57'


def get_available_ip():
    '''.'''
    return '10.5.0.6'


def main():
    parser = argparse.ArgumentParser(
        usage=DESCRIPTION.format(name='./restore_lxc_image.py'))
    parser.add_argument('-l', '--lxcdir',
                        dest='lxc_dir',
                        default='/var/lib/lxc',
                        action='store_true',
                        help='LXC top directory (default: /var/lib/lxc)')
    parser.add_argument('-m', '--mac',
                        dest='mac',
                        default=get_available_mac(),
                        help='mac of the new container')
    parser.add_argument('-f', '--force',
                        dest='force',
                        action='store_true',
                        default=False,
                        help=('Force redoing config edits & relink'
                              ' even if container already exists'))
    parser.add_argument('-i', '--ip',
                        dest='ip',
                        default=get_available_ip(),
                        help='ip of the new container')
    parser.add_argument('-o', '--origin',
                        dest='origin',
                        default=DEFAULT_CONTAINER,
                        help=('origin container (default:'
                              ' {0})').format(DEFAULT_CONTAINER))
    parser.add_argument('-b', '--bridge',
                        help=('default lxc bridge to use (default:'
                              ' {0})').format(DEFAULT_BR),
                        default=DEFAULT_BR)
    parser.add_argument('-n', '--name',
                        dest='name',
                        help='name of the new container')
    parser.add_argument('-s', '--snapshot-type',
                        dest='snapshot',
                        default=None,
                        help=('snapshot type (aufs|overlayfs)'
                              ' (default: None)'))
    args = parser.parse_args(sys.argv[1:])
    opts = vars(args)
    if os.getuid() not in [0]:
        raise ValueError('Must be run either as root or via sudo')
    if not opts['name']:
        raise ValueError('No container name')
    lxc_dir = opts['lxc_dir']
    odir = os.path.join(lxc_dir, opts['origin'])
    orootfs = os.path.join(odir, 'rootfs')
    oconfig = os.path.join(odir, 'config')
    adir = os.path.join(lxc_dir, opts['name'])
    arootfs = os.path.join(adir, 'rootfs')
    aconfig = os.path.join(adir, 'config')
    force = opts['force']
    if opts['snapshots'] not in [None, 'aufs', 'overlayfs']:
        raise ValueError('invalid snapshot type')
    if not os.path.exists(lxc_dir):
        raise ValueError('LXC top dir does not exists, did you installed lxc')
    if not (os.path.exists(orootfs) and os.path.exists(oconfig)):
        raise ValueError('Invalid origin container: {0}'.format(odir))
    if 'linux' not in sys.platform.lower():
        raise ValueError('This must be run on linux')
    if os.path.exists(arootfs) and not force:
        raise ValueError('{0} already created'.format(adir))
    if not os.path.exists(orootfs):
        clone_template(opts['origin'], opts['name'], snapshot=opts['snapshot'])
    if os.path.exists(arootfs) and not force:
        raise ValueError('{0} already created'.format(adir))
    edit_config(aconfig, opts['bridge'], opts['ip'], opts['mac'])


if __name__ == '__main__':
    main()
# vim:set et sts=4 ts=4 tw=80:
