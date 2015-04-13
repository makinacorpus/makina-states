#!/usr/bin/env python
# -*- coding: utf-8 -*-
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


GITHUB = "https://raw.githubusercontent.com/makinacorpus/makina-states/stable/"
RELEASES_URL = (
    'http://sourceforge.net/projects/makinacorpus/files/makina-states')
VER_SLUG = "versions/makina-states-{dist}-{flavor}_version.txt"
MD5_SLUG = "{0}.md5".format(VER_SLUG)
VER_URL = GITHUB + VER_SLUG
MD5_URL = GITHUB + MD5_SLUG
DEFAULT_DIST = "trusty"
DEFAULT_FLAVOR = "lxc"
DEFAULT_BR = 'lxcbr1'
DEFAULT_VER = '14'
DEFAULT_MD5 = '7be985a7965d0228178aad06f6ad0a4c'
DESCRIPTION = '''
Maybe download and install an ubuntu makina-states compliant lxc template.
Makina-States is a layer upon SaltStack to install, and manage bare metal
infrastructure and projects.


By default, this script  will:
    - download the latest official archive (fetch infos from internet)
    - uncompress and prepare the download tarbball
But it can also be run offline or use different version/dist/md5.

The Makina-States LXC Template needs:
    - a filesystem with acls support (99pct the case nowadays).
    - a network bridge for networking, by default it will
      use the bridge: {bridge}
    - At least 5GB free space on /var/lib/lxc (if you won't have this space,
      use bind mounts to mount a directory from a partition where you have more
      space)

This LXC template is a tar file compressed with XZ and
it's filename has this mandatory naming scheme:
 makina-states-${{DIST}}-{flavor}-${{VER}}.tar.xz\
 / eg: makina-states-{dist}-{flavor}-{ver}.tar.xz

The used url will then maybe be:
 ${{MIRROR}}/${{TARFILE}}\
 / eg: {releases}/makina-states-{dist}-{flavor}-{ver}.tar.xz

To run online with default options: {name}
 * To change dist / version: {name} [-d {dist}] [-v {ver}]
 * To use a different mirror: {name} -m http://foo
 * To use a custom md5: {name} -s {md5}
 * To skip md5 checking: {name} -s no

To run offline: {name} -o
This will uncompress & prepare a previously downloaded image that
must be placed in LXCDIR: (eg: /var/lib/lxc)

All modifiers can obviously be combined.
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


def get_ver(ver=DEFAULT_VER,
            dist=DEFAULT_DIST,
            flavor=DEFAULT_FLAVOR,
            offline=False):
    res, trace = ver, ''
    if not ver and not offline:
        try:
            res = "{0}".format(int(urllib2.urlopen(
                VER_URL.format(dist=dist, flavor=flavor)
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
    aclflag = os.path.join(adir, ".{0}{1}aclsdone".format(
        tar, socket.getfqdn()))
    rootfs = os.path.join(adir, 'rootfs')
    sub_rootfs = os.path.join(rootfs, 'rootfs')
    if (
        (not os.path.exists(aclflag)
         and os.path.exists(os.path.join(adir, 'acls.txt'))
         and os.path.exists(rootfs))
        or force
    ):
        with open(os.path.join(adir, 'acls.txt')) as fic:
            with open(os.path.join(rootfs, 'acls.txt'), 'w') as fic2:
                fic2.write(fic.read())
        if os.path.exists(sub_rootfs) and os.path.islink(sub_rootfs):
            os.unlink(sub_rootfs)
        try:
            os.symlink('.', sub_rootfs)
            print('Restoring acls in {0}'.format(adir))
            print(os.getcwd())
            ret, ps = popen(
                'chroot "{0}" /usr/bin/setfacl --restore=acls.txt'
                ''.format(rootfs))
            if ps.returncode:
                # exit always on error as there were sockets while creating acl
                # files
                if 'config' in ret[1]:
                    pass
                else:
                    print(ret[0])
                    print(ret[1])
                    print('error while restoring acls in {0}'.format(rootfs))
                    sys.exit(1)
            with open(aclflag, 'w') as fic:
                fic.write('')
        finally:
            os.unlink(sub_rootfs)


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
    adirtmp = adir + ".dl.tmp"
    tar = os.path.basename(ftar)
    unflag = os.path.join(adir, ".{0}unpacked".format(tar))
    if (
        not os.path.exists(os.path.join(adir, 'rootfs/root'))
        or not os.path.exists(unflag)
        or force
    ):
        if not os.path.exists(adir):
            os.makedirs(adir)
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
        ret, ps = popen('rsync -a --delete "{adirtmp}/" "{adir}/"'.format(
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


def relink_configs(adir, bridge=None):
    fstab = os.path.join(adir, "fstab")
    rootfs = os.path.join(adir, "rootfs")
    lxc_config = os.path.join(adir, "config")
    if not os.path.exists(fstab):
        with open(fstab, 'w') as fic:
            fic.write('\n')
    with open(lxc_config) as fic:
        content = fic.read()
    ocontent = re.sub("lxc.utsname.*",
                      "lxc.utsname = " + os.path.basename(adir),
                      content)
    ocontent = re.sub("lxc.rootfs.*",
                      "lxc.rootfs = {rootfs}".format(rootfs=rootfs),
                      ocontent)
    ocontent = re.sub("lxc.mount.*fstab[ \t]*",
                      "lxc.mount = {adir}/fstab".format(adir=adir),
                      ocontent)
    if bridge:
        # REPLACE ONLY THE FIRST BRIDGE !
        ocontent = re.sub("lxc.network.link.*",
                          "lxc.network.link = {0}".format(bridge),
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


def main():
    parser = argparse.ArgumentParser(
        usage=DESCRIPTION.format(ver=DEFAULT_VER,
                                 name='./restore_lxc_image.py',
                                 md5=DEFAULT_MD5,
                                 flavor=DEFAULT_FLAVOR,
                                 bridge=DEFAULT_BR,
                                 releases=RELEASES_URL,
                                 dist=DEFAULT_DIST))
    parser.add_argument('-m', '--mirror',
                        dest='mirror',
                        default=RELEASES_URL,
                        help='mirror url ({0})'.format(RELEASES_URL))
    parser.add_argument('-l', '--lxcdir',
                        dest='lxc_dir',
                        default='/var/lib/lxc',
                        action='store_true',
                        help='LXC top directory')
    parser.add_argument('--flavor',
                        dest='flavor',
                        default=DEFAULT_FLAVOR,
                        help='flavor ({0})'.format(DEFAULT_FLAVOR))
    parser.add_argument('-o', '--offline',
                        default=False,
                        action='store_true',
                        help='Run offline and assume tar is already there')
    parser.add_argument('-f', '--force',
                        default=False,
                        action='store_true',
                        help='Force unpack again')
    parser.add_argument('-d', '--dist',
                        help=('dist to install'
                              ' (default: {0})').format(DEFAULT_DIST),
                        default=DEFAULT_DIST)
    parser.add_argument('-v', '--ver',
                        help=('version to use (eg: {0}) (latest version will'
                              ' be fetched from internet if not offline'
                              '').format(DEFAULT_VER),
                        default=None)
    parser.add_argument('-b', '--bridge',
                        help='default lxc bridge to use',
                        default=DEFAULT_BR)
    parser.add_argument('--skip-download',
                        default=False,
                        action='store_true',
                        help='skip download')
    parser.add_argument('--skip-unpack',
                        default=False,
                        action='store_true',
                        help='skip unpack')
    parser.add_argument('--skip-relink',
                        default=False,
                        action='store_true',
                        help='skip relink')
    parser.add_argument('-s', '--md5',
                        help=('MD5 of the tarball of version to use '
                              ' (latest version will be '
                              'fetched from internet if not offline.'
                              ' set to \'no\' for no md5sum check'
                              '').format(DEFAULT_MD5),
                        default=None)
    args = parser.parse_args(sys.argv[1:])
    opts = vars(args)
    lxc_dir = opts['lxc_dir']
    opts['ver'] = get_ver(
        ver=opts['ver'],
        dist=opts['dist'],
        flavor=opts['flavor'],
        offline=opts['offline'])
    if (
        opts['md5']
        and opts['md5'].lower().strip().replace(
            '"', '').replace("'", '') == 'no'
    ):
        opts['md5'] = None
    else:
        opts['md5'] = get_md5(
            md5=opts['md5'],
            ver=opts['ver'],
            dist=opts['dist'],
            flavor=opts['flavor'],
            offline=opts['offline'])
    if 'linux' not in sys.platform.lower():
        raise ValueError('This must be run on linux')
    if not os.path.exists(lxc_dir):
        raise ValueError(
            "{0} does not exists, please install lxc".format(lxc_dir))
    tar = "makina-states-{dist}-{flavor}-{ver}.tar.xz".format(**opts)
    bdir = re.sub('(-{flavor}-[^-]*)*$'.format(**opts),
                  '',
                  tar.split(".tar.xz", 1)[0])
    adir = os.path.join(lxc_dir, bdir)
    ftar = os.path.join(lxc_dir, tar)
    if os.path.normpath(lxc_dir) == os.path.normpath(adir):
        raise ValueError('something went wrong when getting tar filename')
    url = os.path.join(opts['mirror'], tar)
    done = False
    if not opts['skip_download']:
        download_template(
            url, ftar, md5=opts['md5'], offline=opts['offline'])
    if not opts['skip_unpack']:
        unpack_template(adir, ftar, md5=opts['md5'], force=opts['force'])
        restore_acls(adir, ftar)
        done = True
    if not opts['skip_relink']:
        relink_configs(adir, bridge=opts['bridge'])
        done = True
    if done:
        print('Your lxc template has been installed in {0}'.format(adir))
        print('It\'s name is {0}'.format(os.path.basename(adir)))


if __name__ == '__main__':
    main()
# vim:set et sts=4 ts=4 tw=80:
