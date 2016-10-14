#!/usr/bin/env bash
# MANAGED VIA SALT - DO NOT EDIT
if [ "x${DEBUG}" != "x" ];then
    set -x
fi
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/sbin:/sbin:/bin:${PATH}
is_lxc() {
    echo  "$(cat -e /proc/1/environ |grep container=lxc|wc -l|sed -e "s/ //g")"
}

filter_host_pids() {
    pids=""
    if [ "x$(is_lxc)" != "x0" ];then
        pids="${pids} $(echo "${@}")"
    else
        for pid in ${@};do
            if [ "x$(grep -q lxc /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ];then
                pids="${pids} $(echo "${pid}")"
             fi
         done
    fi
    echo "${pids}" | sed -e "s/\(^ \+\)\|\( \+$\)//g"
}
if [ -e /etc/default/ntpdate ];then
    . /etc/default/ntpdate
fi
if which service 1>/dev/null 2>&1;then
    svc="service "
else
    svc="/etc/init.d"
fi
pids=$(filter_host_pids $(ps aux|grep 'sbin/ntpd'|grep -v grep|awk '{print $2}'))
if [ "x${pids}" != "x" ];then
    ${svc}ntp stop 2>&1
    pids=$(filter_host_pids $(ps aux|grep 'sbin/ntpd'|grep -v grep|awk '{print $2}'))
    for pid in ${pids};do
        kill -9 ${pid}
    done
fi
echo "changed=false"
# vim:set et sts=4 ts=4 tw=80:
