#!/usr/bin/env bash
state='changed=no comment="already disabled"'
if [ -f /etc/rc.local.d/firewalld.sh ];then
    todo="x"
    state='changed=yes comment="disabled"'
else
    state='changed=no comment="already disabled"'
fi
if [ "x${@}" != "x" ];then
    todo="x"
fi
if [ "x${todo}" != "x" ];then
    for i in firewalld firewalld6;do
        update-rc.d -f firewalld remove || /bin/true
        if [ -e /etc/init/${i}.conf ];then
            echo manual>/etc/init/${i}.override
        fi
        # do not touch the rules !
        # too smelly on prod
        # ${i} stop || /bin/true
        # service ${i} stop || /bin/true
    done
    if [ -e /etc/rc.local.d/firewalld.sh ];then
        rm -f /etc/rc.local.d/firewalld.sh
    fi
fi
echo "${state}"
# vim:set et sts=4 ts=4 tw=80:
