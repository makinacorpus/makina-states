#!/usr/bin/env bash
{% if debug is not defined %}
{% set debug = false %}
{% endif %}
# Reset all directories/files perms in subdirectories
{% if debug %}
# copy debug script for later manual debugging on debug mode
cp "$0" "/tmp/.resetperms.$(basename $0)"
{% endif %}
python <<EOF
from __future__ import (print_function,
                        division,
                        absolute_import,
                        unicode_literals)
import os
import grp
import re
import stat
import pwd
import sys
import traceback
import pprint




re_f = re.M | re.U | re.S

ACLS = {}
SKIPPED = []

DEBUG = os.environ.get('RESETPERMS_DEBUG', {{debug}})

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
    raise IOError('Program not fond: {0} in {1} '.format (
        program, PATH))


try:
    setfacl = which('setfacl')
    HAS_SETFACL = True

except IOError:
    HAS_SETFACL = False

{% if only_acls is defined %}
ONLY_ACLS = {{only_acls}}
{% else %}
ONLY_ACLS =  False
{% endif %}


{% if only_acls is defined %}
ONLY_ACLS = {{only_acls}}
{% else %}
ONLY_ACLS =  False
{% endif %}

{% if no_acls is defined %}
NO_ACLS = {{no_acls}}
{% else %}
NO_ACLS =  False
{% endif %}

for i in os.environ:
    if 'travis' in i.lower():
        # no acl on travis
        NO_ACLS = True


{% if msr is defined %}
m = '{{msr}}'
{% else %}
m = '/srv/salt/makina-states'
{% endif %}
excludes = [
    '.git',
    os.path.join(m , 'lib'),
    os.path.join(m , 'bin'),
    os.path.join(m , 'eggs'),
    os.path.join(m , 'develop-eggs'),
    os.path.join(m , 'parts'),
]
pexcludes = [
{% if excludes is defined %}
{% for i in excludes %}
    '{{i}}',
{% endfor %}
{% endif %}
]

pexcludes = [re.compile(i, re_f)
             for i in pexcludes]

{% if reset_user is defined %}
user = "{{reset_user}}"
{% else %}
user = "{{user if user else 'root'}}"
{% endif %}
try:
    uid = int(user)
except Exception:
    uid = int(pwd.getpwnam(user).pw_uid)

{% if reset_group is defined %}
group = "{{reset_group}}"
{% else %}
group = "{{group if group else 'root'}}"
{% endif %}
try:
    gid = int(group)
except Exception:
    gid = int(grp.getgrnam(group).gr_gid)

fmode = "0{0}".format(int("{{fmode}}"))
dmode = "0{0}".format(int("{{dmode}}"))


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
    if not acl in ACLS:
        ACLS[acl] = []
    if not path in ACLS[acl]:
        ACLS[acl].append(path)


def splitList(L, chunksize=50):
    return[L[i:i+chunksize] for i in range(0, len(L), chunksize)]


def apply_acls():
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
        stop=True
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
            if not i in SKIPPED:
                SKIPPED.append(i)
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

{% for pt in reset_paths %}
reset('{{pt}}')
{% endfor %}
EOF
exit $?
