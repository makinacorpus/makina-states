#!/usr/bin/env bash
# Reset all directories/files perms in subdirectories
python <<EOF
import os
import grp
import stat
import pwd
import traceback

m = '{{msr}}'
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


user = "{{user}}"
try:
    uid = int(user)
except:
    uid = int(pwd.getpwnam('{{user}}').pw_uid)

group = "{{group}}"
try:
    gid = int(group)
except:
    gid = int(grp.getgrnam(group).gr_gid)

fmode = "0%s" % int("{{fmode}}")
dmode = "0%s" % int("{{dmode}}")


def lazy_chmod_path(path, mode):
    try:
        st = os.stat(path)
        if eval(fmode) != stat.S_IMODE(st.st_mode):
            try:
                eval('os.chmod(path, %s)' % fmode)
            except:
                print traceback.format_exc()
                print 'reset failed for %s' % path
    except:
        print traceback.format_exc()
        print 'reset failed for %s' % path


def lazy_chown_path(path, uid, gid):
    try:
        st = os.stat(path)
        if st.st_uid != uid or st.st_gid != gid:
            try:
                os.chown(path, uid, gid)
            except:
                print traceback.format_exc()
                print 'reset failed for %s' % path
    except:
        print traceback.format_exc()
        print 'reset failed for %s' % path

def lazy_chmod_chown(path, mode, uid, gid):
    lazy_chmod_path(path, dmode)
    lazy_chown_path(path, uid, gid)


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
            st = os.stat(curdir)
            lazy_chmod_chown(curdir, dmode, uid, gid)
            for item in files:
                i = os.path.join(root, item)
                if to_skip(i): continue
                lazy_chmod_chown(i, fmode, uid, gid)
        except:
            print traceback.format_exc()
            print 'reset failed for %s' % curdir

{% for pt in reset_paths %}
reset('{{pt}}')
{% endfor %}
EOF
exit $?
