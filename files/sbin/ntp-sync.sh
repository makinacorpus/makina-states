#!/usr/bin/env bash
NTPSERVERS="${NTPSERVERS:-ntp.org}"
if [ -f /etc/default/ntpdate ];then
     . /etc/default/ntpdate
fi
if [ "x${DEBUG}" != "x" ];then
    set -x
fi
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/sbin:/sbin:/bin:${PATH}

is_container() {
    if cat -e /proc/1/cgroup 2>/dev/null|egrep -q 'docker|lxc'; then
        return 0
    else
        return 1
    fi
}
filter_host_pids() {
    pids=""
    if is_container;then
        pids="${pids} $(echo "${@}")"
    else
        for pid in ${@};do
            if ! egrep -q "/(docker|lxc)/" /proc/${pid}/cgroup 2>/dev/null;then
                pids="${pids} $(echo "${pid}")"
            fi
         done
    fi
    echo "${pids}" | sed -e "s/\(^ \+\)\|\( \+$\)//g"
}

if which service 1>/dev/null 2>&1;then
    svc="service "
else
    svc="/etc/init.d"
fi

pids=$(filter_host_pids $(ps aux|grep ntpd|grep -v grep|awk '{print $2}'))
if [ "x${NTPSYNC}" != "xno" ] && [ "x$(is_container)" = "x0" ] && [ "x${pids}" != "x" ];then
    ${svc}ntp stop 2>&1
    ntpdate "${NTPSERVERS}" 2>&1
    ${svc}ntp start 2>&1
fi
# vim:set et sts=4 ts=4 tw=80:
