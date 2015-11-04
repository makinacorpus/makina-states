#!/usr/bin/env bash
if [ "x${DEBUG}" != "x" ];then set -x;fi
DNS_SERVERS="${DNS_SERVERS:-${1:-127.0.0.1 8.8.8.8 4.4.4.4 1.2.3.4}}"
DNS_SEARCH="${DNS_SEARCH:-${2:-$(hostname -f|sed -re "s/[^.]+\.(.*)/\1/g")}}"
export DEBIAN_FRONTEND=noninteractive
gen_resolvconf() {
    echo '# dnsservers setted by makina-states'
    for i in ${DNS_SERVERS};do
        echo "nameserver ${i}"
    done
    if [ "x${DNS_SEARCH}" != "x" ];then
        echo "search ${DNS_SEARCH}"
    fi
}
is_apt_installed() {
    if [ "x$(dpkg-query -s ${@} 2>/dev/null|egrep "^Status:"|grep installed|wc -l|sed -e "s/ //g")"  = "x0" ];then
        return 1
    else
        return 0
    fi
}
lazy_apt_get_install() {
    to_install=""
    for i in ${@};do
         if ! is_apt_installed ${i};then
             to_install="${to_install} ${i}"
         fi
    done
    if [ "x${to_install}" != "x" ];then
        bs_log "Installing ${to_install}"
        apt-get install -y --force-yes ${i}
        return 1
    fi
    return 0
}
if [ -f /etc/debian_version ];then
    HAS_RESOLVCONF="y"
    if apt-mark showhold | egrep -q ^resolvconf;then
        apt-mark unhold resolvconf
        apt-get install --reinstall resolvconf
    else
        lazy_apt_get_install resolvconf
    fi
fi
if [ ! -d /etc/resolvconf/resolv.conf.d ];then
    mkdir -pv /etc/resolvconf/resolv.conf.d
fi
HAS_RESOLVCONF=""
if which resolvconf >/dev/null 2>&1;then
    HAS_RESOLVCONF="x"
fi
if [ -f /etc/resolv.conf ] && [ ! -L /etc/resolv.conf ];then
    cp /etc/resolv.conf /etc/resolvconf/resolv.conf.d/original
fi
resolvconfs=""
if [ "x${HAS_RESOLVCONF}" != "x" ];then
    resolvconf=/run/resolvconf/resolv.conf
    resolvconfs="${resolvconfs} /etc/resolvconf/resolv.conf.d/head"
else
    resolvconf=/etc/resolv.conf
fi
resolvconfs="${resolvconfs} ${resolvconf}"

for i in ${resolvconfs};do
    if [ -e "${i}" ];then
        sed -i -re "/search \(none\)/d" "${i}"
    fi
done
if [ ! -d "$(dirname ${resolvconf})"  ];then
    mkdir -pv "$(dirname ${resolvconf})"
fi
if [ "x${resolvconf}" != "x/etc/resolv.conf" ];then
    rm "/etc/resolv.conf"
    ln -sf "${resolvconf}" "/etc/resolv.conf"
fi
for i in ${resolvconfs};do
    if [ ! -e $(dirname ${i}) ];then
        mkdir -pv "$(dirname ${i})"
    fi
    gen_resolvconf > "${i}"
done
if which resolvconf >/dev/null 2>&1;then
    if which systemctl >/dev/null 2>&1;then
        systemctl enable resolvconf
    fi
    if which update-rc.d >/dev/null 2>&1;then
        if [ -e /etc/init.d/resolvconf ];then
            update-rc.d -f resolvconf defaults 99
        fi
    fi
    service resolvconf restart
fi
# vim:set et sts=4 ts=4 tw=80:
