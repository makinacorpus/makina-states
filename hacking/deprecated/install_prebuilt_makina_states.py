#!/usr/bin/env python
from __future__ import absolute_import, division,  print_function
__docformat__ = 'restructuredtext en'

import glob
import shutil
import time
import os
import socket
import pprint
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
DEFAULT_DIST = 'trusty'
DEFAULT_FLAVOR = 'standalone'
DEFAULT_VER = '14'
DEFAULT_MD5 = "7be985a7965d0228178aad06f6ad0a4c"
DEFAULT_BRANCH = 'stable'
DESCRIPTION = '''
Install a prebuilt version of makina-states directly on the system

WARNING: for now only ubuntu-trusty is supported
DONT INSTALL ON ANYTHING ELSE THAN TRUSTY UNLESS YOU KNOW WHAT's YOU ARE
DOING

Prerequisites:
    apt-get install python

usage:
    {name}
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


def get_ver(ver=DEFAULT_VER,
            dist=DEFAULT_DIST,
            flavor=DEFAULT_FLAVOR,
            offline=False):
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
                VER_SLUG.format(flavor=flavor, dist=dist)
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
            flavor=DEFAULT_FLAVOR,
            offline=False):
    res, trace = md5, ''
    if not md5 and not offline:
        try:
            res = "{0}".format(urllib2.urlopen(
                MD5_URL.format(dist=dist, flavor=flavor)
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
                MD5_SLUG.format(flavor=flavor, dist=dist)
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
    aclflag = os.path.join(adir, ".{0}aclsdone".format(tar))
    if (
        (not os.path.exists(aclflag) and
         os.path.exists(os.path.join(adir, 'acls.txt')) and
         os.path.exists(adir)) or
        force
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


def get_dist(default_dist=DEFAULT_DIST):
    cmd = 'lsb_release -c -s'
    ret, ps = popen(cmd)
    if ret[0]:
        if ret[0].lower().strip() in [
            'precise', 'trusty', 'utopic', 'vivid'
        ]:
            return ret[0].lower().strip()
    return default_dist


def setup_prereqs(offline=False):
    apt = False
    cmd = 'lsb_release -i -s'
    ret, ps = popen(cmd)
    if ret[0]:
        if ret[0].lower().strip() in ['ubuntu', 'debian']:
            apt = True
    if apt and not offline:
        cmd = 'apt-get update'
        ret, ps = popen(cmd)
        if ps.returncode:
            print(ret[0])
            print(ret[1])
            raise ValueError('Cant update apt')
        cmd = 'apt-get install -y --force-yes xz-utils python rsync acl'
        ret, ps = popen(cmd)
        if ps.returncode:
            print(ret[0])
            print(ret[1])
            raise ValueError('Cant install prereqs')


def unpack_template(adir, ftar, md5=None, force=False):
    adir = os.path.normpath(os.path.abspath(adir))
    adirtmp = os.path.join(os.getcwd(), "makina-states.tmp")
    tar = os.path.basename(ftar)
    if not os.path.exists('/etc/makina-states'):
        os.makedirs('/etc/makina-states')
    unflag = os.path.join("/etc/makina-states/prebuilt.{0}".format(tar))
    if force or (
        not os.path.exists(unflag) and
        not os.path.exists("/srv/makina-states/")
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
                 offline=None,
                 update=None,
                 branch=DEFAULT_BRANCH):
    if update is None:
        update = False
    cmd = (
        'test -e /srv/makina-states/_scripts/boot-salt.sh'
    )
    ret, ps = popen(cmd)
    if ps.returncode:
        return
    cmd = (
        '/srv/makina-states/_scripts/boot-salt.sh'
        ' -C'
        ' -b {1}'
        ' -m {0}'
    ).format(
        fqdn, branch)
    if update:
        cmd2 = cmd + ' --refresh-modules'
        if not offline:
            ret, ps = popen(cmd2, stream=True)
            if ps.returncode:
                raise ValueError('Cant update salt')
    ret, ps = popen(cmd, stream=True)
    if ps.returncode:
        raise ValueError('Cant reset salt')


def fix_hosts(fqdn):
    host = fqdn.split('.')[0]
    cmd = "echo '{0}'>/etc/hostname".format(host)
    ret, ps = popen(cmd)
    if ps.returncode:
        raise ValueError('Cant set host')
    cmd = "hostname {0}".format(host)
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
        cmd = "echo \"{0}\"|tee /etc/hosts".format(container_hosts)
        ret, ps = popen(cmd)
        if ps.returncode:
            raise ValueError('Cant set hosts')


def get_fqdn(fqdn=None):
    if fqdn is None:
        fqdn = socket.getfqdn()
    return fqdn


def main():
    default_dist = get_dist(DEFAULT_DIST)
    parser = argparse.ArgumentParser(
        usage=DESCRIPTION.format(ver=DEFAULT_VER,
                                 name='./install_prebuild_makina_states.py',
                                 md5=DEFAULT_MD5,
                                 flavor=DEFAULT_FLAVOR,
                                 releases=RELEASES_URL,
                                 dist=default_dist))
    parser.add_argument('--fqdn',
                        default=None,
                        help='fqdn of this host')
    parser.add_argument('--dist',
                        default=default_dist,
                        help='dist ({0})'.format(default_dist))
    parser.add_argument('--flavor',
                        dest='flavor',
                        default=DEFAULT_FLAVOR,
                        help='flavor ({0})'.format(DEFAULT_FLAVOR))
    parser.add_argument('--ver',
                        default=None,
                        help='version ({0}'.format(DEFAULT_VER))
    parser.add_argument('-m', '--mirror',
                        dest='mirror',
                        default=RELEASES_URL,
                        help='mirror url ({0})'.format(RELEASES_URL))
    parser.add_argument('-a', '--dest',
                        default="/",
                        dest="adir",
                        help='destination dir (/)')
    parser.add_argument('-o', '--offline',
                        default=False,
                        action='store_true',
                        help='Run offline and assume tar is already there')
    parser.add_argument('-u', '--update',
                        default=False,
                        action='store_true',
                        help='Run a git pull in salt dirs prior to install')
    parser.add_argument('-f', '--force',
                        default=False,
                        action='store_true',
                        help='Force unpack again')
    parser.add_argument('--branch',
                        help='default branch ({0})'.format(DEFAULT_BRANCH),
                        default=DEFAULT_BRANCH)
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
    parser.add_argument('--skip-prereqs',
                        default=False,
                        action='store_true',
                        help='skip prereqs')
    parser.add_argument('--skip-salt',
                        default=False,
                        action='store_true',
                        help='skip salt')
    args = parser.parse_args(sys.argv[1:])
    opts = vars(args)
    opts['fqdn'] = get_fqdn(opts['fqdn'])
    opts['ver'] = get_ver(
        ver=opts['ver'],
        dist=opts['dist'],
        flavor=opts['flavor'],
        offline=opts['offline'])
    if (
        opts['md5'] and
        opts['md5'].lower().strip().replace(
            '"', '').replace("'", '') == 'no'
    ):
        opts['md5'] = None
    else:
        opts['md5'] = get_md5(
            md5=opts['md5'],
            ver=opts['ver'],
            flavor=opts['flavor'],
            dist=opts['dist'],
            offline=opts['offline'])
    tar = "makina-states-{dist}-{flavor}-{ver}.tar.xz".format(**opts)
    url = os.path.join(opts['mirror'], tar)
    adir = os.path.abspath(opts['adir'])
    ftar = os.path.abspath(os.path.join(os.getcwd(), tar))
    if os.getuid() not in [0]:
        raise ValueError('Must be run either as root or via sudo')
    if (
        (
            os.path.exists('/srv/makina-states')
        ) and (
            os.path.exists('/usr/bin/salt-call') and
            os.path.exists('/etc/makina-states')
        )
    ) and not opts['force']:
        raise ValueError('Makina-States is already installed')
    if not opts['skip_hosts']:
        fix_hosts(opts['fqdn'])
    if not opts['skip_prereqs']:
        setup_prereqs(offline=opts['offline'])
    if not opts['skip_download']:
        download_template(url, ftar, md5=opts['md5'], offline=opts['offline'])
    if not opts['skip_unpack']:
        unpack_template(adir, ftar, md5=opts['md5'], force=opts['force'])
    if not opts['skip_acls']:
        restore_acls(adir, ftar)
    if not opts['skip_salt']:
        install_salt(opts['fqdn'],
                     update=opts['update'],
                     branch=opts['branch'],
                     offline=opts['offline'])


if __name__ == '__main__':
    main()
# vim:set et sts=4 ts=4 tw=80:
