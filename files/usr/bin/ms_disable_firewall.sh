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

salt=""
nohard=""
for i in $@;do
    if [ "x${i}" = "xfromsalt" ];then
        salt=1
    fi
    if [ "x${i}" = "xnohard" ];then
        nohard=1
    fi
done

salt_status() {
    if [ "x${salt}" = "x1" ];then
        line="changed=${1}"
        shift
        if [ "x${@}" != "x" ];then
            line="${line} comment='${@}'"
        fi
        echo "${line}"
    else
        shift
        if [ "x${@}" != "x" ];then
            echo ${@}
        fi
    fi
}

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
    if [ "x${?}" = "x0" ];then
        salt_status yes "Firewall disabled"
    else
        salt_status yes "Firewall not disabled"
    fi
    return ${ret}
}
s_witch(){
    which $@ 2>/dev/null 1>/dev/null
    return ${?}
}
soft_disable() {
    echo "Soft disabling firewall"
    ret=0
    fic=$(mktemp)
    if s_witch iptables-save && s_witch iptables-restore;then
        doit=""
        if [ -e "${fic}" ];then rm -f "${fic}";fi
        iptables-save > "${fic}"
        if [ -e ${fic} ];then
            if grep -q -- "-j DROP" "${fic}";then doit="x";fi
            if grep -q -- "-j REJECT" "${fic}";then doit="x";fi
            sed -i -re "s/-j (DROP|REJECT).*/-j ACCEPT/g" "${fic}"
            sed -i "/-j LOG/ d" "${fic}"
            if [ "x${doit}" != "x" ];then
                echo "Applying permissive firewall rules"
                iptables-restore < ${fic}
                if [ "x${?}" != "x0" ];then
                    ret=${?}
                fi
                if [ "x${?}" != "x0" ];then
                    salt_status yes "Firewall not soft disabled"
                else
                    salt_status yes "Firewall soft disabled"
                fi
            else
                salt_status no "No restrictive rules were found"
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

main() {
    gret=0
    permissive_routing
    accept_policies
    disabled=""
    if [ "x${nohard}" != "x" ];then
        for i in $(seq 5);do
            if ! soft_disable;then
                echo "Retrying to soft disabling the firewall (${i})"
                sleep 1
                gret=1
            else
                gret=0
                disabled="x"
                break
            fi
        done
    fi
    if [ "x${disabled}" = "x" ];then
        echo "Soft disabling failed"
        if [ "x${nohard}" = "x" ];then
            hard_disable
            gret=${?}
        fi
    fi
}
main
exit ${gret}
# vim:set et sts=4 ts=4 tw=80:
