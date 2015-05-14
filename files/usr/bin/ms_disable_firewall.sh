#!/usr/bin/env bash
#
# disable firewall but try in first place to make permissive rules
# and policies, thus conserving any mangle or forward rules
# without flushing totally the firewall
#
if [ "x${DEBUG}" != "x" ];then
    set -x
fi
iptables="iptables -w"
iptablest="iptables -w -t"
die() {
    if [ ${?} != "x0" ];then
        if [ x"$@" != "x" ];then
            echo "$@"
            exit 1
        fi
    fi
}
accept_policies() {
    for i in OUTPUT INPUT FORWARD;do
        ${iptablest} filter -P ${i} ACCEPT
    done
    for i in PREROUTING INPUT FORWARD OUTPUT POSTROUTING;do
        ${iptablest} mangle -P ${i} ACCEPT
    done
    for i in PREROUTING INPUT OUTPUT POSTROUTING;do
        ${iptablest} nat -P ${i} ACCEPT
    done
}
ipflush() {
    ret=0
    for i in OUTPUT INPUT FORWARD;do
        ${iptablest} filter -F ${i}
        if [ "x${?}" != "x0" ];then ret=${?};fi
    done
    for i in PREROUTING INPUT FORWARD OUTPUT POSTROUTING;do
        ${iptablest} mangle -F ${i}
        if [ "x${?}" != "x0" ];then ret=${?};fi
    done
    for i in PREROUTING INPUT OUTPUT POSTROUTING;do
        ${iptablest} nat -F ${i}
        if [ "x${?}" != "x0" ];then ret=${?};fi
    done
    return ${ret}
}
permissive_routing() {
    echo 1 > /proc/sys/net/ipv4/ip_forward || /bin/true
}
hard_disable() {
    echo "Hard disabling firewall"
    ret=0
    permissive_routing
    accept_policies
    if [ "x${?}" != "x0" ];then ret=${?};fi
    ipflush
    if [ "x${?}" != "x0" ];then ret=${?};fi
    accept_policies
    if [ "x${?}" != "x0" ];then ret=${?};fi
    return ${ret}
}
s_witch(){
    which $@ 2>/dev/null 1>/dev/null
    return ${?}
}
soft_disable() {
    ret=0
    fic=$(mktemp)
    if s_witch iptables-save && s_witch iptables-restore;then
        doit=""
        iptables-save > "${fic}"
        if [ -e ${fic} ];then
            if grep -q -- "-j DROP" "${fic}";then doit="x";fi
            if grep -q -- "-j REJECT" "${fic}";then doit="x";fi
            sed -i -re "s/-j (DROP|REJECT).*/-j ACCEPT/g" "${fic}"
            sed -i "/-j LOG/ d" "${fic}"
            if [ "x${doit}" != "x" ];then
                iptables-restore < ${fic}
                if [ "x${?}" != "x0" ];then ret=${?};fi
            fi
        else
            ret=1
        fi
    else
        ret=1
    fi
    if [ -e "${fic}" ];then rm -f "${fic}";fi
    return ${ret}
}
ret=0
permissive_routing
accept_policies
if ! soft_disable;then
    ret=${?}
    echo "Soft disabling failed"
    hard_disable
    ret=${?}
fi
exit ${?}
# vim:set et sts=4 ts=4 tw=80:
