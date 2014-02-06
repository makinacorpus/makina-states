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
import subprocess
import pwd
import shutil
import sys
import traceback
import pprint
from optparse import OptionParser

try:
    from collections import OrderedDict
except ImportError:
    try:
        from orderreddict import OrderedDict
    except ImportError:
        OrderedDict = dict

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
parser.add_option("-k", "--reset-acls",
                  action="store_true",
                  dest="reset",
                  help="reset ALL acls prior to set it again")
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
parser.add_option("-R",
                  "--no-recursive",
                  default=True,
                  action="store_false",
                  help="Do not run recursivly (default)",
                  dest="recursive")
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

DEBUG = os.environ.get('RESETPERMS_DEBUG', options.debug)
ACLS = {}
SKIPPED = {}
ALL_PATHS = {}
# OWNERSHIPS: files & directories to apply ownership grouped by ownership (uid/gid)
# UNIX_PERMS: files & directories to apply ownership grouped by perm
# SKIPPED: skipped paths
# ACLS: all couples ACL type, [paths to apply]
# ALL_PATHS:  all paths to apply perms, combined
OWNERSHIPS = {}
UNIX_PERMS = {}


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
    SETFACL = unicode(which('setfacl'))
    HAS_SETFACL = True
except IOError:
    HAS_SETFACL = False

ONLY_ACLS = options.only_acl
NO_ACLS = options.no_acl
CHOWN = which('chown')
CHMOD = which('chmod')

for i in os.environ:
    if 'travis' in i.lower():
        # no acl on travis
        NO_ACLS = True


excludes = []
pexcludes = options.excludes
pexcludes = [re.compile(i, re_f)
             for i in pexcludes]
if options.user:
    USER = options.user
else:
    USER = 'root'
try:
    UID = int(USER)
except Exception:
    UID = int(pwd.getpwnam(USER).pw_uid)

if options.group:
    GROUP = options.group
else:
    GROUP = 'root'
try:
    GID = int(GROUP)
except Exception:
    GID = int(grp.getgrnam(GROUP).gr_gid)


FMODE = u"0{0}".format(int(options.fmode))
DMODE = u"0{0}".format(int(options.dmode))


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


def splitList(L, chunksize=50):
    return[L[i:i + chunksize] for i in range(0, len(L), chunksize)]


def uniquify(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


def usplitList(seq):
    seq.sort()
    return splitList(uniquify(seq))


def encode_str(p):
    if isinstance(p, unicode):
        p = p.encode('utf-8')
    return p


def quote_paths(paths):
    return ["'{0}'".format(encode_str(p)) for p in paths]


def shell_exec(cmd, shell=False):
    scmd = ' '.join([encode_str(a) for a in cmd])
    try:
        if options.debug:
            print('Executing {0}'.format(scmd))
        ret = subprocess.check_output(
            cmd, stderr=sys.stdout, shell=shell)
        if ret:
            print(ret)
    except Exception:
        print(u'Reset failed for {0}'.format(scmd))
        print(traceback.format_exc())


def collect_acl(path, mode, uid=UID, gid=GID, is_dir=False):
    '''
    Idea is to regroup all the files/dirs with
    the same acl to reduce the number of setfacl calls
    '''
    perms = permissions_to_unix_name(mode)
    #mask = permissions_to_unix_name(mode[-2])['OTH']
    mask = 'rwx'
    uacl = 'mask:{2},u:{0}:{1}'.format(*(uid, perms['USR'], mask))
    gacl = 'mask:{2},g:{0}:{1}'.format(*(gid, perms['GRP'], mask))
    acl = uacl
    acl += ",{0}".format(gacl)
    if is_dir:
        acl += ',d:{0}'.format(uacl)
        acl += ',d:{0}'.format(gacl)
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


def apply_acls():
    if NO_ACLS or not HAS_SETFACL:
        return
    if options.reset:
        resets = []
        for acl, paths in ACLS.items():
            resets.extend(paths)
        for chunk in usplitList(resets):
            cmd = [SETFACL, "-b"] + chunk
            shell_exec(cmd)
    for acl, paths in ACLS.items():
        # print acl, paths
        for chunk in usplitList(paths):
            cmd = [SETFACL, "--mask", "-n", "-m", acl] + chunk
            cmd = [SETFACL, "-m", acl] + chunk
            shell_exec(cmd)


def chmod_paths(paths, mode):
    if not isinstance(paths, list):
        paths = [paths]
    for path in paths:
        pref = ''
        if mode < 1000:
            pref = '0'
        try:
            eval('os.chmod(path, 0{1}{0})'.format(mode, pref))
        except:
            continue
    # in fact, the python impl. wasnt the bottleneck
    #for chunk in usplitList(paths):
    #    mode = int(mode)
    #    pref = ''
    #    if mode < 1000:
    #        pref = '0'
    #    cmd = [CHMOD, '{0}{1}'.format(pref, mode)] + chunk
    #    if options.debug:
    #        cmd.insert(1, '-v')
    #    shell_exec(cmd)


def chown_paths(paths, uid=UID, gid=GID):
    if not isinstance(paths, list):
        paths = [paths]
    for path in paths:
        try:
            os.chown(path, uid, gid)
        except:
            continue
    # in fact python impl wasnt the bottleneck
    #for chunk in usplitList(paths):
    #    cmd = [CHOWN, '{0}:{1}'.format(uid, gid)] + chunk
    #    if options.debug:
    #        cmd.insert(1, '-v')
    #    shell_exec(cmd)


def to_skip(path):
    stop = False
    if path in SKIPPED:
        return True
    elif os.path.islink(path):
        # inner dir and files will be excluded too
        pexcludes.append(re.compile(path, re_f))
        stop = True
    else:
        for p in pexcludes:
            if p.pattern in path:
                stop = True
                break
            if not stop:
                # do only if no stop, optimization.
                if p.search(path):
                    stop = True
                    break
    if stop:
        SKIPPED[path] = path
    return stop


def reset_permissions():
    if not ONLY_ACLS:
        for mode, paths in UNIX_PERMS.items():
            chmod_paths(paths, mode)
        for ownership, paths in OWNERSHIPS.items():
            chown_paths(paths, uid=ownership[0], gid=ownership[1])
    apply_acls()


def collect_paths(path,
                  uid=UID,
                  gid=GID,
                  dmode=DMODE,
                  fmode=FMODE,
                  recursive=options.recursive):
    if not path in ALL_PATHS:
        ALL_PATHS[path] = path
        is_file, is_dir, skipped = (
            os.path.isfile(path),
            os.path.isdir(path),
            to_skip(path))
        if skipped or not (is_dir or is_file):
            return
        mode = is_dir and dmode or fmode
        if HAS_SETFACL and not NO_ACLS:
            collect_acl(path,
                        mode=(is_dir and dmode or fmode),
                        is_dir=is_dir)
        st = os.stat(path)
        if st.st_uid != uid or st.st_gid != gid:
            if not (uid, gid) in OWNERSHIPS:
                OWNERSHIPS[(uid, gid)] = []
            OWNERSHIPS[(uid, gid)].append(path)
        if eval(mode) != stat.S_IMODE(st.st_mode):
            if not mode in UNIX_PERMS:
                UNIX_PERMS[mode] = []
            UNIX_PERMS[mode].append(path)
        if is_dir and recursive:
            for root, dirs, files in os.walk(path):
                for subpaths in [files, dirs]:
                    for subpath in subpaths:
                        if DEBUG:
                            print(os.path.join(root, subpath))
                        collect_paths(
                            os.path.join(root, subpath),
                            recursive=False)


def reset(path):
    print("Path: {0} ({1}:{2}, dmode: {3}, fmode: {4})".format(
        path, USER, GROUP, DMODE, FMODE))
    if not os.path.exists(path):
        print("\n\nWARNING: {0} does not exist\n\n".format(path))
        return
    collect_paths(path)
    reset_permissions()
    if DEBUG and SKIPPED:
        skipped = list(SKIPPED)
        skipped.sort()
        print('Skipped content:')
        pprint.pprint(skipped)

for pt in options.paths:
    reset(pt)

"""
Profiled optimization was done with zope example::

    python -m cProfile -o output_file1\
            /srv/salt/makina-states/_scripts/reset-perms.py\
            --dmode '0770' --fmode '0770'\
            --paths "/srv/projects/guadeloupe-eau/project"\
            --user zope --group editor
    pyprof2calltree -i output_file1 -o output_file1.pstat
    kcachegrind output_file1.pstat&

    real    4m5.527s
Phase2
    real    2m25.547s
Phase3
    real    1m56.581s
Phase4
    real    1m49.341s
"""
