#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import time
import os
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
DEFAULT_BRANCH = 'v2'
DESCRIPTION = '''
Create a container from another container
If the IP address or the MAC address is not specified, it will be generated.

It will add your default ssh_keys inside the container for you to log inside
with ssh.
No password will be used by default.

Examples:
{name} -n mytest
{name} -n mytest -s overlayfs
{name} -n mytest --ip=10.5.0.20
{name} -n mytest -o odoo
'''


def popen(cargs=None, shell=True, log=True, stream=None):
    if stream is None:
        stream = False
    if log:
        print('Running: {0}'.format(cargs))
    if not cargs:
        cargs = []
    ret, ps = None, None
    if cargs:
        if stream:
            ps = Popen(cargs, shell=shell)
        else:
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


def container_cat(container, filep):
    cmd = ("lxc-attach -n '{0}' --"
           " cat '{1}'").format(container, filep)
    ret, ps = popen(cmd)
    if ps.returncode:
        print(ret[0])
        print(ret[1])
        raise IOError('error while cating {1}'
                      ' in {0}'.format(container, filep))
    return ret[0]


def edit_config(lxc_config, bridge, ip, mac, nm):
    with open(lxc_config) as fic:
        content = fic.read()
    ocontent = content
    configs = {'lxc.network.hwaddr': mac,
               'lxc.network.link': bridge,
               'lxc.network.ipv4': '{0}/{1}'.format(ip, nm)}
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


def get_available_mac(lxc_dir='/var/lib/lxc'):
    '''.'''
    cmacs = []
    base = '00:16:{0}:{1}:{2}:{3}'
    pattern = 'lxc.network.hwaddr = '
    for i in glob.glob('{0}/*/config'.format(lxc_dir)):
        with open(i) as fic:
            lines = fic.readlines()
            cmacs.extend([a.split(pattern, 1)[1].strip()
                          for a in lines
                          if a.startswith('{0}'.format(pattern))])
    cmacs = [re.sub('/.*', '', c) for c in cmacs]
    mac = None
    for i in xrange(int('1', 16), int('FF', 16)):
        for j in xrange(int('1', 16), int('FF', 16)):
            for k in xrange(int('1', 16), int('FF', 16)):
                for l in xrange(int('1', 16), int('FF', 16)):
                    cmac = base.format(i, j,  k, l)
                    if cmac not in cmacs:
                        mac = cmac
                    if mac is not None:
                        break
                if mac is not None:
                    break
            if mac is not None:
                break
        if mac is not None:
            break
    if mac is None:
        raise ValueError('No mac !')
    return mac


def get_available_ip(lxc_dir='/var/lib/lxc'):
    '''.'''
    cipv4s = []
    pattern = 'lxc.network.ipv4 = '
    for i in glob.glob('{0}/*/config'.format(lxc_dir)):
        with open(i) as fic:
            lines = fic.readlines()
            cipv4s.extend([a.split(pattern, 1)[1].strip()
                           for a in lines
                           if a.startswith('{0}'.format(pattern))])
    cipv4s = [re.sub('/.*', '', c) for c in cipv4s]
    ip = None
    for i in range(0, 253):
        for j in range(2, 252):
            cip = '10.5.{0}.{1}'.format(i, j)
            if cip not in cipv4s:
                ip = cip
            if ip is not None:
                break
        if ip is not None:
            break
    if ip is None:
        raise ValueError('No ip !')
    return ip


def get_container_status(container):
    ret, ps = popen('lxc-ls --fancy')
    if ps.returncode:
        print(ret[0])
        print(ret[1])
        print('error while getting lxcls')
        raise ValueError('lxc ls for {0}'.format(container))
    out = ret[0] + ret[1]
    status = None
    for i in out.splitlines()[2:]:
        parts = i.split()
        if parts[0] == container:
            status = parts[1]
            break
    return status


def is_stopped(container):
    return get_container_status(container) == 'STOPPED'


def is_started(container):
    return get_container_status(container) == 'RUNNING'


def stop_container(container):
    if not is_stopped(container):
        popen('lxc-stop -k -n {0}'.format(container))
        if not is_stopped(container):
            raise ValueError('{0} wont stop'.format(container))


def start_container(container):
    if not is_started(container):
        popen('lxc-start -d -n {0}'.format(container))
    if not is_started(container):
        raise ValueError('{0} wont start'.format(container))


def regen_sshconfig(container):
    cmd = ("lxc-attach -n '{0}' --"
           " rm -f /etc/ssh/ssh_host_*{{key,pub}}").format(container)
    ret, ps = popen(cmd)
    if ps.returncode:
        print(ret[0])
        print(ret[1])
        raise ValueError('error while removing old ssh key in'
                         ' {0}'.format(container))
    cmd = ("lxc-attach -n '{0}' --"
           " dpkg-reconfigure openssh-server").format(container)
    ret, ps = popen(cmd)
    if ps.returncode:
        print(ret[0])
        print(ret[1])
        raise ValueError('error while reconfiguring ssh'
                         ' in {0}'.format(container))
    cmd = ("lxc-attach -n '{0}' --"
           " service ssh restart").format(container)
    ret, ps = popen(cmd)
    if ps.returncode:
        print(ret[0])
        print(ret[1])
        raise ValueError('error while restarting ssh'
                         ' in {0}'.format(container))


def restart_container(container):
    stop_container(container)
    start_container(container)


def allow_user_and_root(container):
    users = ['root']
    sudoer = os.environ.get('SUDO_USER', '')
    if sudoer:
        users.append(sudoer)
    ssh_keys = []
    for user in users:
        home = os.path.expanduser('~{0}'.format(user))
        for i in glob.glob(home + '/.ssh/id_*.pub'):
            with open(i) as fic:
                content = fic.read().strip()
                if content not in ssh_keys:
                    ssh_keys.append(content)
    if not ssh_keys:
        raise ValueError('Please gen an sshkey with ssh-keygen')
    cmd = ("lxc-attach -n '{0}' --"
           " test -e /root/.ssh").format(container)
    ret, ps = popen(cmd)
    if ps.returncode:
        cmd = ("lxc-attach -n '{0}' --"
               " mkdir -p /root/.ssh").format(container)
        ret, ps = popen(cmd)
        if ps.returncode:
            print(ret[0])
            print(ret[1])
            raise ValueError('Cant create /root/.ssh in container')
    cmd = ("lxc-attach -n '{0}' --"
           " chmod 700 /root/.ssh").format(container)
    ret, ps = popen(cmd)
    if ps.returncode:
        raise ValueError('Cant chmod /root/.ssh in container')
    cmd = ("lxc-attach -n '{0}' --"
           " touch /root/.ssh/authorized_keys").format(container)
    ret, ps = popen(cmd)
    if ps.returncode:
        raise ValueError('Cant touch /root/.ssh/authorized_keys in container'
                         ' {0}'.format(container))
    cmd = ("lxc-attach -n '{0}' --"
           " chmod 700 /root/.ssh/authorized_keys").format(container)
    ret, ps = popen(cmd)
    if ps.returncode:
        raise ValueError('Cant touch /root/.ssh/authorized_keys in container'
                         ' {0}'.format(container))
    cmd = ("lxc-attach -n '{0}' --"
           " chmod 700 /root/").format(container)
    ret, ps = popen(cmd)
    if ps.returncode:
        raise ValueError('Cant chmod /root/ in container'
                         ' {0}'.format(container))
    container_keys = container_cat(container, '/root/.ssh/authorized_keys')
    for k in ssh_keys:
        if k not in container_keys:
            cmd = ("echo '{1}' | lxc-attach -n '{0}' --"
                   " tee -a /root/.ssh/authorized_keys"
                   "").format(container, k)
            ret, ps = popen(cmd)
            if ps.returncode:
                raise ValueError('Cant add {1} in '
                                 ' {0}'.format(container, k))


def install_salt(container,
                 fqdn,
                 offline=None,
                 update=None,
                 branch=DEFAULT_BRANCH):
    if update is None:
        update = False
    cmd = (
        "lxc-attach -n '{0}' --"
        ' test -e /srv/makina-states/_scripts/boot-salt.sh'
    ).format(container)
    ret, ps = popen(cmd)
    if ps.returncode:
        return
    # keep old opts for retro compat
    cmd = (
        "lxc-attach -n '{1}' --"
        ' /srv/makina-states/_scripts/boot-salt.sh'
        ' -C'
        ' -m {0}'
        ' -b {2}'
        '').format(fqdn,
                   container,
                   branch)
    if update:
        cmd2 = cmd + ' --refresh-modules'
        if not offline:
            ret, ps = popen(cmd2, stream=True)
            if ps.returncode:
                raise ValueError('Cant update salt')
    ret, ps = popen(cmd+";")
    if ps.returncode:
        print(ret[0])
        print(ret[1])
        raise ValueError('Cant reset salt in  {0}'.format(container))


def fix_hosts(container, fqdn):
    host = fqdn.split('.')[0]
    cmd = ("echo '{1}' | lxc-attach -n '{0}' --"
           " tee /etc/hostname"
           "").format(container, host)
    ret, ps = popen(cmd)
    if ps.returncode:
        raise ValueError('Cant set host in '
                         ' {0}'.format(container))
    cmd = ("lxc-attach -n '{0}' --"
           " hostname {1}"
           "").format(container, host)
    ret, ps = popen(cmd)
    if ps.returncode:
        raise ValueError('Cant affect host in '
                         ' {0}'.format(container))
    container_hosts = container_cat(container, '/etc/hosts')
    to_add = []
    for ip in ['127.0.0.1', '127.0.0.1']:
        h = ' '.join([fqdn, host])
        if not re.search(
            '{0}( |\t).*{1}(\t| |$)'.format(ip, h),
            container_hosts,
            flags=re.M
        ):
            to_add.append('{0} {1}'.format(ip, h))
    if to_add:
        container_hosts = ('\n'.join(to_add) +
                           '\n' + container_hosts +
                           '\n'.join(to_add))
        cmd = ("echo \"{1}\"|lxc-attach -n '{0}' --"
               " tee /etc/hosts"
               "").format(container, container_hosts)
        ret, ps = popen(cmd)
        if ps.returncode:
            raise ValueError('Cant set hosts in '
                             ' {0}'.format(container))


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
                        default=None,
                        help='mac of the new container')
    parser.add_argument('-n', '--network-mask',
                        dest='nm',
                        default='16',
                        help='network mask of the new container')
    parser.add_argument('-f', '--force',
                        dest='force',
                        action='store_true',
                        default=False,
                        help=('Force redoing config edits & relink'
                              ' even if container already exists'))
    parser.add_argument('-i', '--ip',
                        dest='ip',
                        default=None,
                        help='ip of the new container')
    parser.add_argument('-o', '--origin',
                        dest='origin',
                        default=DEFAULT_CONTAINER,
                        help=('origin container (default:'
                              ' {0})').format(DEFAULT_CONTAINER))
    parser.add_argument('--branch',
                        help='default branch ({0})'.format(DEFAULT_BRANCH),
                        default=DEFAULT_BRANCH)
    parser.add_argument('-u', '--update',
                        default=False,
                        action='store_true',
                        help='Run a git pull in salt dirs prior to install')
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
    parser.add_argument('--skip-hosts',
                        default=False,
                        action='store_true',
                        help='skip hosts')
    parser.add_argument('--skip-salt',
                        default=False,
                        action='store_true',
                        help='skip salt')
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
    aconfig = os.path.join(adir, 'config')
    fqdn = opts['name']
    if '.' not in opts['name']:
        fqdn = '{0}.lxc.local'.format(opts['name'])
    force = opts['force']
    if opts['snapshot'] not in [None, 'aufs', 'overlayfs']:
        raise ValueError('invalid snapshot type')
    if not os.path.exists(lxc_dir):
        raise ValueError('LXC top dir does not exists, '
                         'did you installed lxc')
    if not opts['ip']:
        opts['ip'] = get_available_ip(lxc_dir)
    if not opts['mac']:
        opts['mac'] = get_available_mac(lxc_dir)
    if not (os.path.exists(orootfs) and os.path.exists(oconfig)):
        raise ValueError('Invalid origin container: {0}'.format(odir))
    if 'linux' not in sys.platform.lower():
        raise ValueError('This must be run on linux')
    if os.path.exists(adir) and not force:
        raise ValueError('{0} already created'.format(adir))
    if not os.path.exists(adir):
        clone_template(
            opts['origin'], opts['name'], snapshot=opts['snapshot'])
    if not os.path.exists(adir):
        raise ValueError('{0} does not exists'.format(adir))
    edit_config(aconfig, opts['bridge'], opts['ip'], opts['mac'], opts['nm'])
    restart_container(opts['name'])
    tries = [a for a in range(10)]
    ssh_done = False
    traces = []
    while tries:
        tries.pop()
        try:
            regen_sshconfig(opts['name'])
            ssh_done = True
            break
        except:
            print('retrying ssh config if it is first boot')
            traces.append(traceback.format_exc())
            time.sleep(1)
    if not ssh_done:
        print('\n'.join(traces))
        raise ValueError('Cant reset ssh in {0}'.format(opts['name']))
    allow_user_and_root(opts['name'])
    if not opts['skip_hosts']:
        fix_hosts(opts['name'], fqdn)
    if not opts['skip_salt']:
        install_salt(opts['name'],
                     fqdn,
                     branch=opts['branch'],
                     update=opts['update'],
                     offline=opts['offline'])
    print('--')
    print('Your container is in {0}'.format(adir))
    print('   config: {0}'.format(aconfig))
    print('   IP: {0}'.format(opts['ip']))


if __name__ == '__main__':
    main()
# vim:set et sts=4 ts=4 tw=80:
