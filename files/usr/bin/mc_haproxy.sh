#!/usr/bin/env bash
if [ "x${DEBUG}" = "x" ];then
    set -x
fi
if [ -f /etc/default/haproxy ];then
    . /etc/default/haproxy
fi
if [ "x${1}" = "xcheck" ];then
    exec /usr/sbin/haproxy -c -f "${CONFIG}" ${EXTRAOPTS}
elif [ "x${1}" = "xstart" ];then
    exec /usr/sbin/haproxy-systemd-wrapper -f "${CONFIG}" ${EXTRAOPTS} -p /run/haproxy.pid
fi
exit ${?}
# vim:set et sts=4 ts=4 tw=80:
