#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division,  print_function
__docformat__ = 'restructuredtext en'

import shutil
import os
import urllib
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
VER_SLUG = "versions/makina-states-{dist}-lxc_version.txt"
MD5_SLUG = "{0}.md5".format(VER_SLUG)
VER_URL = GITHUB + VER_SLUG
MD5_URL = GITHUB + MD5_SLUG
DEFAULT_DIST = "trusty"
DEFAULT_VER = "11"
DEFAULT_MD5 = "94c796b5c31a6eb121417d0fd210f646"


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


def get_ver(ver=DEFAULT_VER, dist=DEFAULT_DIST, offline=False):
    res, trace = ver, ''
    if not ver and not offline:
        try:
            res = "{0}".format(int(urllib.urlopen(
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
            res = "{0}".format(urllib.urlopen(
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


def restore_acls(adir, tar=None, force=False):
    aclflag = os.path.join(adir, ".{0}{1}aclsdone".format(
        tar, socket.getfqdn()))
    cwd = os.getcwd()
    if (
        (not os.path.exists(aclflag)
         and os.path.exists(os.path.join(adir, 'acls.txt'))
         and os.path.exists(os.path.join(adir, 'rootfs')))
        or force
    ):
        with open(os.path.join(adir, 'acls.txt')) as fic:
            with open(os.path.join(adir, 'rootfs/acls.txt'), 'w') as fic2:
                fic2.write(fic.read())
        if os.path.exists('rootfs') and os.path.islink('rootfs'):
            os.unlink('rootfs')
        try:
            os.symlink('.', 'rootfs')
            print('Restoring acls in {0}'.format(adir))
            ret, ps = popen('chroot . /usr/bin/setfacl --restore=acls.txt')
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
        finally:
            os.unlink('rootfs')
            os.chdir(cwd)


def unpack_lxc_template(adir, tar, md5=None, force=False):
    adirtmp = adir + ".dl.tmp"
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
        print('Unpacking {0} in {1}'.format(tar, adirtmp))
        ret, ps = popen('tar xJf "{tar}" -C "{adirtmp}"'.format(
            tar=tar, adirtmp=adirtmp))
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


DESCRIPTION = '''
Maybe download and install an ubuntu makina-states compliant lxc template.
Makina-States is a layer upon Salstack  to install, and manage bare
infrastructure and projects.

By default, it will download the latest official archive but it can also
download the file from another mirror.

The awaitened tarfile filename has this mandatory naming scheme:

        makina-states-${{DIST}}-lxc-${{VER}}.tar.xz
        eg: makina-states-{dist}-lxc-{ver}.tar.xz

The used url will be:

        ${{MIRROR}}/${{TARFILE}}
        eg: {releases}/makina-states-{dist}-lxc-{ver}.tar.xz

As you see, the archive should be a tar file compressed with XZ (lzma
compression)

Run online (download, uncompress & prepare the image):
 $ restore_lxc_image.py # use defaults opts and latest image
 $ restore_lxc_image.py -v {ver}
 $ restore_lxc_image.py -d {dist} -v {ver}
To use a different mirror
 $ restore_lxc_image.py -m http://foo
To use a custom md5
 $ restore_lxc_image.py -d {dist} -v {ver} -s {md5}
To skip md5 checking
 $ restore_lxc_image.py -d {dist} -v {ver} -s no


Run offline (uncompress & prepare a previously downloaded image:
the image must be placed in LXCDIR: (/var/lib/lxc)
 $ restore_lxc_image.py # use defaults opts and latest image
 $ restore_lxc_image.py -o -v {ver}
 $ restore_lxc_image.py -o -d {dist} -v {ver}
To use a custom md5
 $ restore_lxc_image.py -o -d {dist} -v {ver} -s {md5}
To skip md5 checking
 $ restore_lxc_image.py -o -d {dist} -v {ver} -s no
'''


def main():
    parser = argparse.ArgumentParser(
        usage=DESCRIPTION.format(ver=DEFAULT_VER,
                                 md5=DEFAULT_MD5,
                                 releases=RELEASES_URL,
                                 dist=DEFAULT_DIST))
    parser.add_argument('-l', '--lxcdir',
                        dest='lxc_dir',
                        default='/var/lib/lxc',
                        action='store_true',
                        help='LXC top directory')
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
                        default='lxcbr1')
    parser.add_argument('-s', '--md5',
                        help=('MD5 of the tarball of version to use '
                              ' (latest version will be '
                              'fetched from internet if not offline.'
                              'set to no for no md5sum check'
                              '').format(DEFAULT_MD5),
                        default=None)
    args = parser.parse_args(sys.argv[1:])
    opts = vars(args)
    lxc_dir = opts['lxc_dir']
    opts['ver'] = get_ver(
        ver=opts['ver'], dist=opts['dist'], offline=opts['offline'])
    if opts['md5'] and opts['md5'].lower().strip() == 'no':
        opts['md5'] = None
    else:
        opts['md5'] = get_md5(
            md5=opts['md5'],
            ver=opts['ver'],
            dist=opts['dist'],
            offline=opts['offline'])
    if 'linux' not in sys.platform.lower():
        raise ValueError('This must be run on linux')
    if not os.path.exists(lxc_dir):
        raise ValueError(
            "{0} does not exists, please install lxc".format(lxc_dir))
    tar = "makina-states-{dist}-lxc-{ver}.tar.xz".format(**opts)
    bdir = re.sub('(-lxc-[^-]*)*$', '', tar.split(".tar.xz", 1)[0])
    adir = os.path.join(lxc_dir, bdir)
    if os.path.normpath(lxc_dir) == os.path.normpath(adir):
        raise ValueError('something went wrong when getting tar filename')
    download_lxc_template(adir, tar, md5=opts['md5'], force=opts['force'])
    unpack_lxc_template(adir, tar, md5=opts['md5'], force=opts['force'])
    restore_acls(adir, tar)
    relink_configs(adir, bridge=opts['bridge'])
    print('Your lxc template has been installed in {0}'.format(adir))
    print('It\'s name is {0}'.format(os.path.basename(adir)))


if __name__ == '__main__':
    main()
# vim:set et sts=4 ts=4 tw=80:
