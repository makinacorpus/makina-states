#!/usr/bin/env bash
if [ "x${DEBUG}" != "x" ];then set -x;fi
DNS_SERVERS="${DNS_SERVERS-${1:-"127.0.0.1 8.8.8.8 4.4.4.4"}}"
DNS_SEARCH="${DNS_SEARCH-${2:-$(hostname -f|sed -re "s/[^.]+\.(.*)/\1/g")}}"
gen_resolvconf() {
    echo '# dnsservers setted by makina-states'
    for i in ${DNS_SERVERS};do
        echo "nameserver ${i}"
    done
    if [ "x${DNS_SEARCH}" != "x" ];then
        echo "search ${DNS_SEARCH}"
    fi
}
if [[ -z ${DNS_SERVERS} ]];then
    echo empty DNS_SERVERS
    exit 1
fi
if [[ -z ${DNS_SEARCH} ]];then
    echo empty DNS_SEARCH
    exit 1
fi
if hash resolvconf >/dev/null 2>&1;then
    HAS_RESOLVCONF="${HAS_RESOLVCONF-y}"
else
    HAS_RESOLVCONF="${HAS_RESOLVCONF-}"
fi
if [[ -n ${HAS_RESOLVCONF} ]];then
    if [ ! -d /etc/resolvconf/resolv.conf.d ];then
        mkdir -pv /etc/resolvconf/resolv.conf.d
    fi
    if [ -f /etc/resolv.conf ] && [ ! -L /etc/resolv.conf ];then
        cp /etc/resolv.conf /etc/resolvconf/resolv.conf.d/original
    fi
fi
if [ "x${HAS_RESOLVCONF}" != "x" ];then
    RESOLVCONF=/run/resolvconf/resolv.conf
    RESOLVCONFS="${RESOLVCONF} /etc/resolvconf/resolv.conf.d/head"
else
    RESOLVCONF=/etc/resolv.conf
    RESOLVCONFS="${RESOLVCONF}"
fi
for i in ${RESOLVCONFS};do
    if [ ! -e $(dirname ${i}) ];then
        mkdir -pv "$(dirname ${i})"
    fi
    gen_resolvconf > "${i}"
done
if hash resolvconf >/dev/null 2>&1;then
    if test -e /etc/resolv.conf &&\
        test -e "${RESOLVCONF}" &&\
        [ "x${RESOLVCONF}" != "x/etc/resolv.conf" ] &&\
        [ "x$(readlink -f "/etc/resolv.conf")" != "x${RESOLVCONF}" ];then
        rm "/etc/resolv.conf"
        ln -sf "${resolvconf}" "/etc/resolv.conf"
    fi
    if hash systemctl >/dev/null 2>&1;then
        systemctl enable resolvconf
    fi
    if hash update-rc.d >/dev/null 2>&1;then
        if [ -e /etc/init.d/resolvconf ];then
            update-rc.d -f resolvconf defaults 99
        fi
    fi
    service resolvconf restart
fi
# vim:set et sts=4 ts=4 tw=80:
