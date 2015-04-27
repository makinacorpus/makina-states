#!/usr/bin/env bash
#{% set data = salt['mc_circus.settings']() %}

PIDFILE="/var/run/circud.pid"
VENV="/srv/apps/circus/venv"
ACTIVATE="/srv/apps/circus/venv/bin/activate"
DAEMON="${VENV}/bin/circusd"
CONF="/etc/circus/circusd.ini"

. /etc/profile || /bin/true
if [ -f /etc/default/circusd ];then
    . /etc/default/circusd
fi
if [ -f "${ACTIVATE}" ];then
    . "${ACTIVATE}"
fi

is_lxc() {
    echo  "$(cat -e /proc/1/environ |grep container=lxc|wc -l|sed -e "s/ //g")"
}
filter_host_pids() {
    if [ "x$(is_lxc)" != "x0" ];then
        echo "${@}"
    else
        for pid in ${@};do
            if [ "x$(grep -q lxc /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ];then
                 echo ${pid}
             fi
         done
    fi
}
if [ "x${a}" = "xstart" ];then
    exec su -c "${VENV}/bin/circusd ${CONF}"
elif [ "x${a}" = "xstop" ];then
    pids=$(filter_host_pids $(ps aux|grep "from circus import stats"|awk '{print $2}'))
    if [ "x${pids}" != "x" ];then
      for pid in ${pids};do kill -9 "${pid}" || /bin/true;done
    fi
    pids=$(filter_host_pids $(ps aux|grep "from circusweb import"|awk '{print $2}'))
    if [ "x${pids}" != "x" ];then
      for pid in ${pids};do kill -9 "${pid}" || /bin/true;done
    fi
fi
# vim:set et sts=4 ts=4 tw=80:
