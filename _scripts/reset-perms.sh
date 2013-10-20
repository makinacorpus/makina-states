#!/usr/bin/env bash
# Reset all directories/files perms in subdirectories
python <<EOF
import os
import grp
import stat
import pwd

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

def reset(p):
    print "Path: %s" % p
    print "Directories: %s" % dmode
    print "Files: %s" % fmode
    print "User:Group: %s:%s\n\n" % (user, group)
    if not os.path.exists(p):
        print "\n\nWARNING: %s does not exist\n\n" % p
        return
    for root, dirs, files in os.walk(p):
        i = root
        stop = False
        for p in pexcludes:
            if p in i:
                stop = True
                break
        if stop:
            continue
        st = os.stat(i)
        if eval(dmode) != stat.S_IMODE(st.st_mode):
            eval('os.chmod(i, %s)' % dmode)
        if st.st_uid != uid or st.st_gid != gid:
            os.chown(i, uid, gid)
        for item in files:
            i = os.path.join(root, item)
            stop = False
            for p in pexcludes:
                if p in i:
                    stop = True
                    break
            if stop:
                continue
            st = os.stat(i)
            if eval(fmode) != stat.S_IMODE(st.st_mode):
                eval('os.chmod(i, %s)' % fmode)
            if st.st_uid != uid or st.st_gid != gid:
                os.chown(i, uid, gid)

{% for pt in reset_paths %}
reset('{{pt}}')
{% endfor %}
EOF
exit $?
