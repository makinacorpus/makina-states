#!/usr/bin/env python
from __future__ import absolute_import, division,  print_function
__docformat__ = 'restructuredtext en'

import glob
import shutil
import time
import os
import socket
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

GITHUB = "https://raw.githubusercontent.com/makinacorpus/makina-states/stable/"
RELEASES_URL = (
    'http://sourceforge.net/projects/makinacorpus/files/makina-states')
VER_SLUG = "versions/makina-states-{dist}-{flavor}_version.txt"
MD5_SLUG = "{0}.md5".format(VER_SLUG)
VER_URL = GITHUB + VER_SLUG
MD5_URL = GITHUB + MD5_SLUG
DEFAULT_DIST = "trusty"
DEFAULT_FLAVOR = "standalone"
DEFAULT_VER = "14"
DEFAULT_MD5 = "7be985a7965d0228178aad06f6ad0a4c"
DESCRIPTION = ''''''


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


def get_ver(ver=DEFAULT_VER, dist=DEFAULT_DIST, offline=False):
    res, trace = ver, ''
    if not ver and not offline:
        try:
            res = "{0}".format(int(urllib2.urlopen(
                VER_URL.format(dist=dist)
            ).read().strip()))
        except Exception:
            trace = traceback.format_exc()
    if not ver and not res:
        try:
            # try to get local ver from a git checkout
            # of makina-states if available
            with open(os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(sys.argv[0]))),
                VER_SLUG.format(dist=dist)
            )) as fic:
                res = fic.read().strip()
        except IOError:
            res = DEFAULT_VER
    if not res:
        if trace:
            print(trace)
        raise ValueError('No default version')
    return res


def get_md5(md5=DEFAULT_MD5,
            ver=DEFAULT_VER,
            dist=DEFAULT_DIST,
            offline=False):
    res, trace = md5, ''
    if not md5 and not offline:
        try:
            res = "{0}".format(urllib2.urlopen(
                MD5_URL.format(dist=dist)
            ).read().strip())
            if 'not found' in res.lower():
                res = ''
        except Exception:
            trace = traceback.format_exc()
    if not md5 and not res:
        try:
            # try to get local ver from a git checkout
            # of makina-states if available
            with open(os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(sys.argv[0]))),
                MD5_SLUG.format(dist=dist)
            )) as fic:
                res = fic.read().strip()
        except IOError:
            res = DEFAULT_MD5
    if trace:
        print(trace)
    return res


def system(cmd):
    return os.system(cmd)


def restore_acls(adir, ftar=None, force=False):
    tar = os.path.basename(ftar)
    aclflag = os.path.join(adir, ".{0}{1}aclsdone".format(
        tar, socket.getfqdn()))
    if (
        (not os.path.exists(aclflag)
         and os.path.exists(os.path.join(adir, 'acls.txt'))
         and os.path.exists(adir))
        or force
    ):
        print('Restoring acls in {0}'.format(adir))
        ret, ps = popen(
            '/usr/bin/setfacl --restore=acls.txt'
            ''.format(adir))
        if ps.returncode:
            # exit always on error as there were sockets while creating acl
            # files
            if 'config' in ret[1]:
                pass
            else:
                print(ret[0])
                print(ret[1])
                print('error while restoring acls in {0}'.format(adir))
                sys.exit(1)
        with open(aclflag, 'w') as fic:
            fic.write('')


def download_template(url, tar, md5=None, offline=False):
    try:
        # if we already have the file, early exit this func.
        check_md5(tar, md5)
        print('Already downloaded: {0}'.format(tar))
        return
    except (IOError,) as exc:
        if offline:
            raise exc
    except (OSError,) as exc:
        # not downloaded
        pass
    except (ValueError,) as exc:
        # failed md5
        if offline:
            raise exc
        else:
            dtar = '{0}.{1}.sav'.format(tar, time.time())
            print('MD5 FAILED: Moving {0} -> {1}'.format(tar, dtar))
            os.rename(tar, dtar)
    print('Downloading {0}'.format(url))
    print(' in {0}'.format(tar))
    with open(tar, 'wb') as fp:
        req = urllib2.urlopen(url)
        CHUNK = 16 * 1024
        while True:
            chunk = req.read(CHUNK)
            if not chunk:
                break
            fp.write(chunk)
    check_md5(tar, md5)
    print('Downloaded: {0}'.format(tar))


def unpack_template(adir, ftar, md5=None, force=False):
    adir = os.path.normpath(os.path.abspath(adir))
    adirtmp = os.path.join(os.getcwd(), "makina-states.tmp")
    tar = os.path.basename(ftar)
    unflag = os.path.join("/etc/makina-states/prebuilt".format(tar))
    if force or (
        not os.path.exists(unflag)
        and not os.path.exists("/srv/salt/makina-states/")
        and not os.path.exists("/srv/mastersalt/makina-states/")
    ):
        if os.path.exists(adirtmp):
            shutil.rmtree(adirtmp)
        if not os.path.exists(adirtmp):
            os.makedirs(adirtmp)
        print('Unpacking {0} in {1}'.format(ftar, adirtmp))
        ret, ps = popen('tar xJf "{tar}" -C "{adirtmp}"'.format(
            tar=ftar, adirtmp=adirtmp))
        if ps.returncode:
            print(ret[0])
            print(ret[1])
            print('error while untaring')
            sys.exit(1)
        print('Syncing {0} <- {1}'.format(adir, adirtmp))
        ret, ps = popen('rsync -aA  "{adirtmp}/" "{adir}/"'.format(
            adir=adir, adirtmp=adirtmp))
        if ps.returncode:
            print(ret[0])
            print(ret[1])
            print('error while syncing')
            sys.exit(1)
        with open(unflag, 'w') as f:
            f.write('')
    if os.path.exists(adirtmp):
        shutil.rmtree(adirtmp)


def install_salt(fqdn,
                 mastersalt=None,
                 local_salt_mode='masterless',
                 local_mastersalt_mode='masterless'):
    if not mastersalt:
        mastersalt = fqdn
    cmd = (
        'test -e /srv/mastersalt/makina-states/_scripts/boot-salt.sh'
    )
    ret, ps = popen(cmd)
    if ps.returncode:
        return
    cmd = (
        '/srv/mastersalt/makina-states/_scripts/boot-salt.sh'
        ' --local-salt-mode {1}'
        ' --local-mastersalt-mode {2}'
        ' -m {0}'
        ' --mastersalt {4}'
        ' --salt-master-dns {0};'
    ).format(fqdn, local_salt_mode, local_mastersalt_mode, mastersalt)
    ret, ps = popen(cmd)
    if ps.returncode:
        print(ret[0])
        print(ret[1])
        raise ValueError('Cant reset salt')


def fix_hosts(fqdn):
    host = fqdn.split('.')[0]
    cmd = "echo '{0}'>/etc/hostname".format(host)
    ret, ps = popen(cmd)
    if ps.returncode:
        raise ValueError('Cant set host')
    cmd = "hostname {1}".format(host)
    ret, ps = popen(cmd)
    if ps.returncode:
        raise ValueError('Cant affect host')
    container_hosts = popen('cat /etc/hosts')[0][0]
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
        cmd = "echo \"{1}\"|tee /etc/hosts".format(container_hosts)
        ret, ps = popen(cmd)
        if ps.returncode:
            raise ValueError('Cant set hosts')


def main():
    parser = argparse.ArgumentParser(
        usage=DESCRIPTION.format(ver=DEFAULT_VER,
                                 name='./install_prebuild_makina_states.py',
                                 md5=DEFAULT_MD5,
                                 flavor=DEFAULT_FLAVOR,
                                 releases=RELEASES_URL,
                                 dist=DEFAULT_DIST))
    parser.add_argument('--fqdn',
                        default=socket.getfqdn(),
                        help='fqdn')
    parser.add_argument('--dist',
                        default=DEFAULT_DIST,
                        help='dist')
    parser.add_argument('--flavor',
                        default=DEFAULT_FLAVOR,
                        help='flavor')
    parser.add_argument('--ver',
                        default=DEFAULT_VER,
                        help='version')
    parser.add_argument('-m', '--mirror',
                        dest='mirror',
                        default=RELEASES_URL,
                        help='mirror url')
    parser.add_argument('-a', '--dest',
                        default="/",
                        dest="adir",
                        help='destination dir')
    parser.add_argument('-o', '--offline',
                        default=False,
                        action='store_true',
                        help='Run offline and assume tar is already there')
    parser.add_argument('-f', '--force',
                        default=False,
                        action='store_true',
                        help='Force unpack again')
    parser.add_argument('-s', '--md5',
                        help=('MD5 of the tarball of version to use '
                              ' (latest version will be '
                              'fetched from internet if not offline.'
                              ' set to \'no\' for no md5sum check'
                              '').format(DEFAULT_MD5),
                        default=None)
    parser.add_argument('--skip-hosts',
                        default=False,
                        action='store_true',
                        help='skip hosts')
    parser.add_argument('--skip-download',
                        default=False,
                        action='store_true',
                        help='skip download')
    parser.add_argument('--skip-acls',
                        default=False,
                        action='store_true',
                        help='skip acls')
    parser.add_argument('--skip-unpack',
                        default=False,
                        action='store_true',
                        help='skip unpack')
    parser.add_argument('--skip-salt',
                        default=False,
                        action='store_true',
                        help='skip salt')
    args = parser.parse_args(sys.argv[1:])
    opts = vars(args)
    tar = "makina-states-{dist}-{flavor}-{ver}.tar.xz".format(**opts)
    url = os.path.join(opts['mirror'], tar)
    adir = os.path.abspath(opts['adir'])
    ftar = os.path.abspath(os.path.join(os.getcwd(), tar))
    if os.getuid() not in [0]:
        raise ValueError('Must be run either as root or via sudo')
    if not opts['skip_hosts']:
        fix_hosts(opts['fqdn'])
    if not opts['skip_download']:
        download_template(url, ftar, md5=opts['md5'], offline=opts['offline'])
    if not opts['skip_unpack']:
        unpack_template(adir, ftar, md5=opts['md5'], force=opts['force'])
    if not opts['skip_acls']:
        restore_acls(adir, ftar)
    if not opts['skip_salt']:
        install_salt(opts['fqdn'])


if __name__ == '__main__':
    main()
# vim:set et sts=4 ts=4 tw=80:
