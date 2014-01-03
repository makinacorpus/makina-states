#!/usr/bin/env bash
# Reset all directories/files perms in subdirectories
python <<EOF
import os
import grp
import stat
import pwd
import sys
import traceback

ACLS = {}

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
    raise IOError('Program not fond: %s in %s ' % (program, PATH))


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


{% if reset_user is defined %}
user = "{{reset_user}}"
{% else %}
user = "{{user}}"
{% endif %}
try:
    uid = int(user)
except Exception:
    uid = int(pwd.getpwnam(user).pw_uid)

{% if reset_group is defined %}
group = "{{reset_group}}"
{% else %}
group = "{{group}}"
{% endif %}
try:
    gid = int(group)
except Exception:
    gid = int(grp.getgrnam(group).gr_gid)

fmode = "0%s" % int("{{fmode}}")
dmode = "0%s" % int("{{dmode}}")


def permissions_to_unix_name(mode):
    usertypes = {'USR': '', 'GRP': '', 'OTH': ''}
    omode = int(mode, 8)
    for usertype in [a for a in usertypes]:
        permstr = ''
        perm_types = ['R', 'W', 'X']
        for permtype in perm_types:
            perm = getattr(stat, 'S_I%s%s' % (permtype, usertype))
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
        for chunk in splitList(paths):
            paths = ' '.join(["'{0}'".format(p) for p in chunk])
        cmd = "{2} -m '{0}' {1}".format(*(acl, paths, setfacl))
        #print cmd
        os.system(cmd)


def lazy_chmod_path(path, mode):
    try:
        st = os.stat(path)
        if eval(mode) != stat.S_IMODE(st.st_mode):
            try:
                eval('os.chmod(path, %s)' % mode)
            except Exception:
                print 'Reset failed for %s (%s)' % (path, mode)
                print traceback.format_exc()
    except Exception:
        print 'Reset(o) failed for %s (%s)' % (path, mode)
        print traceback.format_exc()


def lazy_chown_path(path, uid, gid):
    try:
        st = os.stat(path)
        if st.st_uid != uid or st.st_gid != gid:
            try:
                os.chown(path, uid, gid)
            except:
                print 'Reset failed for %s, %s, %s' % (path, uid, gid)
                print traceback.format_exc()
    except Exception:
        print 'Reset(o) failed for %s, %s, %s' % (path, uid, gid)
        print traceback.format_exc()

def lazy_chmod_chown(path, mode, uid, gid, is_dir=False):
    if not ONLY_ACLS:
        lazy_chmod_path(path, mode)
        lazy_chown_path(path, uid, gid)
    if HAS_SETFACL:
        try:
            collect_acl(path, uid, gid, mode, is_dir=is_dir)
        except Exception:
             print 'Reset(acl) failed for %s (%s)' % (path, mode)
             print traceback.format_exc()


def to_skip(i):
    stop = False
    if os.path.islink(i):
        # inner dir and files will be excluded too
        pexcludes.append(i)
        stop=True
    else:
        for p in pexcludes:
            if p in i:
                stop = True
                break
    return stop


def reset(p):
    print "Path: %s" % p
    print "Directories: %s" % dmode
    print "Files: %s" % fmode
    print "User:Group: %s:%s\n\n" % (user, group)
    if not os.path.exists(p):
        print "\n\nWARNING: %s does not exist\n\n" % p
        return
    for root, dirs, files in os.walk(p):
        curdir = root
        if to_skip(curdir):
            continue
        try:
            lazy_chmod_chown(curdir, dmode, uid, gid, is_dir=True)
            for item in files:
                i = os.path.join(root, item)
                if to_skip(i): continue
                lazy_chmod_chown(i, fmode, uid, gid)
        except Exception:
            print traceback.format_exc()
            print 'reset failed for %s' % curdir
    if HAS_SETFACL:
        apply_acls()

{% for pt in reset_paths %}
reset('{{pt}}')
{% endfor %}
EOF
exit $?
