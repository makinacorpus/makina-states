#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemples:

Set mode to 770 for root:root and set acls from user vagrant & group editor
reset-perms.py --fmode 770 --paths bin/ --users vagrant:r-x --groups editor:r--

Set mode to 770 but skip acls sets
reset-perms.py --fmode 770 --paths bin/ --no-acl

Do only acls (so only set acl for vagrant
reset-perms.py --paths bin/ --users vagrant:r-x --only-acls

Remove any setted acls else than vagrant
reset-perms.py --paths bin/ --reset --only-acls --users vagrant:r-x
"""

from __future__ import (print_function,
                        division,
                        absolute_import,
                        unicode_literals)
import os
import grp
import re
import stat
import pwd
import shutil
import sys
import traceback
import pprint
from optparse import OptionParser

parser = OptionParser()
parser.add_option(
    "--users",
    default=[],
    action="append",
    dest="users",
    help="set acl for another user (GROUP[:UNIX_PERM]) eg: root:r-- "
    "(can be called multiple times; perm default to fmode)")
parser.add_option(
    "--groups",
    action="append",
    default=[],
    dest="groups",
    help="set acl for another group (GROUP[:UNIX_PERM(]) eg: root:r-x ("
    "can be called multiple times; perm default to fmode)")
parser.add_option("-r", "--reset",
                  action="store_true",
                  dest="reset",
                  help="reset acl prior to set it again")
parser.add_option("--fmode",
                  default="770",
                  action="store",
                  dest="fmode")
parser.add_option("--dmode",
                  default="770",
                  action="store",
                  dest="dmode")
parser.add_option("-u", "--user",
                  default="root",
                  action="store",
                  dest="user")
parser.add_option("-n", "--no-acls",
                  action="store_true",
                  dest="no_acl")
parser.add_option("-o",
                  "--only-acls",
                  action="store_true",
                  dest="only_acl")
parser.add_option("-p",
                  "--paths",
                  default=[],
                  action="append",
                  dest="paths")
parser.add_option(
    "-e", "--excludes", default=[], action="append", dest="excludes")
parser.add_option("--debug", action="store_true", dest="debug")
parser.add_option(
    "-g", "--group", default="root", action="store", dest="group")

(options, args) = parser.parse_args()


if options.debug:
    # copy debug script for later manual debugging on debug mode
    shutil.copy2(sys.argv[0],
                 "/tmp/.resetperms.{0}".format(
                     os.path.basename(sys.argv[0])))

re_f = re.M | re.U | re.S

ACLS = {}
SKIPPED = []
DEBUG = os.environ.get('RESETPERMS_DEBUG', options.debug)


def which(program, environ=None, key='PATH', split=':'):
    if not environ:
        environ = os.environ
    PATH = environ.get(key, '').split(split)
    for entry in PATH:
        fp = os.path.abspath(os.path.join(entry, program))
        if os.path.exists(fp):
            return fp
        if (
            (sys.platform.startswith('win')
             or sys.platform.startswith('cyg'))
            and os.path.exists(fp + '.exe')
        ):
            return fp + '.exe'
    raise IOError('Program not fond: {0} in {1} '.format(
        program, PATH))


try:
    setfacl = which('setfacl')
    HAS_SETFACL = True
except IOError:
    HAS_SETFACL = False

ONLY_ACLS = options.only_acl
NO_ACLS = options.no_acl

for i in os.environ:
    if 'travis' in i.lower():
        # no acl on travis
        NO_ACLS = True


excludes = []
pexcludes = options.excludes
pexcludes = [re.compile(i, re_f)
             for i in pexcludes]
if options.user:
    user = options.user
else:
    user = 'root'
try:
    uid = int(user)
except Exception:
    uid = int(pwd.getpwnam(user).pw_uid)

if options.group:
    group = options.group
else:
    group = 'root'
try:
    gid = int(group)
except Exception:
    gid = int(grp.getgrnam(group).gr_gid)


fmode = "0{0}".format(int(options.fmode))
dmode = "0{0}".format(int(options.dmode))


def permissions_to_unix_name(mode):
    usertypes = {'USR': '', 'GRP': '', 'OTH': ''}
    omode = int(mode, 8)
    for usertype in [a for a in usertypes]:
        permstr = ''
        perm_types = ['R', 'W', 'X']
        for permtype in perm_types:
            perm = getattr(stat, 'S_I{0}{1}'.format(permtype, usertype))
            if omode & perm:
                permstr += permtype.lower()
            else:
                permstr += '-'
            usertypes[usertype] = permstr
    return usertypes


def collect_acl(path, uid, gid, mode, is_dir=False):
    perms = permissions_to_unix_name(mode)
    uacl = u'u:{0}:{1}'.format(*(uid, perms['USR']))
    gacl = u'g:{0}:{1}'.format(*(gid, perms['GRP']))
    acl = uacl
    acl += ",{0}".format(gacl)
    if is_dir:
        acl += u',d:{0}'.format(uacl)
        acl += u',d:{0}'.format(gacl)
    for user in options.users:
        aclmode = perms['USR']
        if ':' in user:
            user, aclmode = user.split(':')
        acl += ",u:{0}:{1}".format(user, aclmode)
        if is_dir:
            acl += ",d:u:{0}:{1}".format(user, aclmode)
    for group in options.groups:
        aclmode = perms['USR']
        if ':' in group:
            group, aclmode = group.split(':')
        acl += ",g:{0}:{1}".format(group, aclmode)
        if is_dir:
            acl += ",d:g:{0}:{1}".format(group, aclmode)
    if not acl in ACLS:
        ACLS[acl] = []
    if not path in ACLS[acl]:
        ACLS[acl].append(path)


def splitList(L, chunksize=50):
    return[L[i:i + chunksize] for i in range(0, len(L), chunksize)]


def uniquify(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


def apply_acls():
    if options.reset:
        resets = []
        for acl, paths in ACLS.items():
            resets.extend(paths)
        resets = uniquify(resets)
        for chunk in splitList(resets):
            paths = ' '.join(["'{0}'".format(p) for p in chunk])
            cmd = "{1} -b {0}".format(*(paths, setfacl))
            os.system(cmd)
    for acl, paths in ACLS.items():
        # print acl, paths
        for chunk in splitList(paths):
            paths = ' '.join(["'{0}'".format(p) for p in chunk])
            cmd = "{2} -m '{0}' {1}".format(*(acl, paths, setfacl))
            # print cmd
            os.system(cmd)


def lazy_chmod_path(path, mode):
    try:
        st = os.stat(path)
        if eval(mode) != stat.S_IMODE(st.st_mode):
            try:
                eval('os.chmod(path, {0})'.format(mode))
            except Exception:
                print('Reset failed for {0} ({1})'.format(
                    path, mode))
                print(traceback.format_exc())
    except Exception:
        print('Reset(o) failed for {0} ({1})'.format(
            path, mode))
        print(traceback.format_exc())


def lazy_chown_path(path, uid, gid):
    try:
        st = os.stat(path)
        if st.st_uid != uid or st.st_gid != gid:
            try:
                os.chown(path, uid, gid)
            except:
                print('Reset failed for {0}, {1}, {2}'.format(
                    path, uid, gid))
                print(traceback.format_exc())
    except Exception:
        print('Reset(o) failed for {0}, {1}, {2}'.format(
            path, uid, gid))
        print(traceback.format_exc())


def lazy_chmod_chown(path, mode, uid, gid, is_dir=False):
    if not ONLY_ACLS:
        lazy_chmod_path(path, mode)
        lazy_chown_path(path, uid, gid)
    if HAS_SETFACL and not NO_ACLS:
        try:
            collect_acl(path, uid, gid, mode, is_dir=is_dir)
        except Exception:
            print('Reset(acl) failed for {0} ({1})'.format(
                path, mode))
            print(traceback.format_exc())


def to_skip(i):
    stop = False
    if os.path.islink(i):
        # inner dir and files will be excluded too
        pexcludes.append(re.compile(i, re_f))
        stop = True
    else:
        for p in pexcludes:
            if p.pattern in i:
                stop = True
                break
            if p.search(i):
                stop = True
                break
    return stop


def reset(p):
    print("Path: {0} ({1}:{2}, dmode: {3}, fmode: {4})".format(
        p, user, group, dmode, fmode))
    if not os.path.exists(p):
        print("\n\nWARNING: {0} does not exist\n\n".format(p))
        return
    for root, dirs, files in os.walk(p):
        curdir = root
        if to_skip(curdir):
            if not curdir in SKIPPED:
                SKIPPED.append(curdir)
                continue
        try:
            lazy_chmod_chown(curdir, dmode, uid, gid, is_dir=True)
            for item in files:
                i = os.path.join(root, item)
                if to_skip(i):
                    if not i in SKIPPED:
                        SKIPPED.append(i)
                        continue
                lazy_chmod_chown(i, fmode, uid, gid)
        except Exception:
            print(traceback.format_exc())
            print('reset failed for {0}'.format(curdir))
    if HAS_SETFACL and not NO_ACLS:
        apply_acls()
    if DEBUG and SKIPPED:
        SKIPPED.sort()
        print('Skipped content:')
        pprint.pprint(SKIPPED)

for pt in options.paths:
    reset(pt)
