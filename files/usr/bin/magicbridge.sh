#!/usr/bin/env bash
if [ "x${DEBUG}" != "x" ];then set -x;fi

# Script to:
#   * launch a linux network bridge
#   * setup dnsmasq to serve DHCP addresses and DNS queries forward
#       * behavior of the dhcp/dns configurations can be edited via  /etc/dnsmasq.bridge/*
#         conf files
#   * setup iptables to accept the above traffic but also masquerade access to wide internet
#

# to make up a lxcfoo bridge just
#   - cp $this_script  /some/where/magicbridge_lxcfoo
#   * OPT:
#      - $ED /etc/default/magicbridge_lxcfoo if neccesary
#      - $ED /etc/dnsmasq.lxcfoo/*
#   - /some/where/magicbridge_lxcfoo start | stop

# get_bridge foo
# mgcbr0
# get_bridge /usr/bin/lxc-net-makina.sh
# lxcbr1
# get_bridge /usr/bin/docker-net-makina.sh
# docker1
# get_bridge /usr/bin/magicbridge_tata
# tata
get_bridge() {
    sc=${1}
    # retrocompatible makina-states wrapper
    if [ "x${1}" = "x/usr/bin/lxc-net-makina.sh" ];then
        br="lxcbr1"
    elif [ "x${1}" = "x/usr/bin/docker-net-makina.sh" ];then
        br="docker1"
    else
        if [ "x$(echo "${1}"|egrep -q magicbridge_;echo ${?})" = "x0" ];then
            br=$(echo "${1}"|sed -re "s/.*magicbridge_(.*)/\1/g")
        else
            br="mgcbr0"
        fi
    fi
    echo "${br}"
}

# get_net lxcbr1
# 10.5.0.0
# get_net docker1
# 10.7.0.0
# get_net foo
# 10.4.0.0
get_net() {
    # retrocompatible makina-states wrapper
    br=${1}
    if [ "x${br}" = "xdocker1" ];then
        net="10.7.0.0"
    elif [ "x${br}" = "xlxcbr1" ];then
        net="10.5.0.0"
    else
        net="10.4.0.0"
    fi
    echo "${net}"
}

distrosysconfdir="${distrosysconfdir:-"/etc/default"}"
BRIDGE="${MAGICBRIDGE:-"$(get_bridge ${0})"}"
NET="${MAGICBRIDGE_NET:-"$(get_net ${BRIDGE})"}"
DEFAULTS="${distrosysconfdir}/magicbridge_${BRIDGE}"
DNSMASQ_CONF_DIR="/etc/dnsmasq.${BRIDGE}"
ACTIVATED="True"
LOCALSTATEDIR="/var"
IPTABLES_DISABLED=""
DNSMASQ_DISABLED=""
NETMASK=""
NETWORK=""
ADDR=""
DOMAIN=""
DOMAIN_ARG=""
DHCP_CONF_FILE=""
DHCP_RANGE=""
DHCP_MAX=""
OFFSET=""

if [ -f "${DEFAULTS}" ];then . "${DEFAULTS}";fi

is_container() {
    echo  "$(cat -e /proc/1/environ |grep container=|wc -l|sed -e "s/ //g")"
}

filter_host_pids() {
    pids=""
    if [ "x$(is_container)" != "x0" ];then
        pids="${pids} $(echo "${@}")"
    else
        for pid in ${@};do
            if [ "x$(grep -q /lxc/ /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ];then
                pids="${pids} $(echo "${pid}")"
            fi
         done
    fi
    echo "${pids}" | sed -e "s/\(^ \+\)\|\( \+$\)//g"
}

_netmask2cidr () {
    # Assumes there's no "255." after a non-255 byte in the mask
    local x=${1##*255.}
    set -- 0^^^128^192^224^240^248^252^254^ $(( (${#1} - ${#x})*2 )) ${x%%.*}
    x=${1%%${3}*}
    echo $(( ${2} + (${#x}/4) ))
}

count_ip_zeros() {
    echo "$@" | awk -F. '{count=0; for(i=0;i<=NF;i++){ if ($i==0) {count++} } print count}'
}

count_ip_dots() {
    echo "$@" | awk '{ gsub("[^.]", ""); print length }'
}

filter_network() {
    echo "${1}"|sed -re "s/(^\.)//g" -e "s/(\.$)//g" -e "s/\.\.+//g"
}

gw_from_net() {
    echo "${@}" | sed -e "s/\.[^.]\+$/.1/g"
}

range_begin_from_net() {
    echo "${@}" | sed -e "s/\.[^.]\+$/.$((${OFFSET}+2))/g"
}

range_end_from_net() {
    echo "${@}" \
        | sed -e "s/\.[^.]\+$/.253/g" \
        | sed -re "s/0.0.253$/255.255.253/g"\
        | sed -re "s/0.253$/255.253/g"
}

set_vars() {
    use_iptables_lock="-w"
    iptables -w -L -n > /dev/null 2>&1 || use_iptables_lock=""
    if [ "x${NETMASK}" = "x" ];then
        ipzeros=$(count_ip_zeros ${NET})
        for i in $(seq $((4-${ipzeros})));do
            NETMASK="${NETMASK}.255"
        done
        ipdots=$(count_ip_dots ${NETMASK})
        if [ "x${ipdots}" != "x0" ];then
            for i in $(seq $((4-${ipdots})));do
                NETMASK="${NETMASK}.0"
            done
        fi
    fi
    DNSMASQ_HOSTS_CONFS="${DNSMASQ_CONF_DIR}/hosts.d"
    DNSMASQ_CONFS="${DNSMASQ_CONF_DIR}/conf.d"
    NETMASK="$(filter_network "${NETMASK}")"
    NETWORK_NUM="$(_netmask2cidr ${NETMASK})"
    NETWORK="${NET}/${NETWORK_NUM}"
    if [ "x${OFFSET}" = "x" ];then
        OFFSET=40
    fi
    if [ "x${ADDR}" = "x" ];then
        ADDR=$(gw_from_net ${NET})
    fi
    if [ "x${DHCP_MAX}" = "x" ];then
        DHCP_MAX="$(( $(( 256**$(count_ip_zeros ${NETMASK}) )) - ${OFFSET} ))"
    fi
    if [ "x${DHCP_RANGE}" = "x" ];then
        DHCP_RANGE="${DHCP_RANGE_BEGIN:-"$(range_begin_from_net ${NET})"}"
        DHCP_RANGE="${DHCP_RANGE},${DHCP_RANGE_END:-"$(range_end_from_net ${NET})"}"
    fi
    if [ -d "$LOCALSTATEDIR"/lock/subsys ]; then
        LOCKDIR="$LOCALSTATEDIR"/lock/subsys
    else
        LOCKDIR="$LOCALSTATEDIR"/lock
    fi
    VARRUN="${VARRUN:-"/var/run"}"
    LOCKFILE="${LOCKDIR}/magicbridge-${BRIDGE}"
    # relink interfaces with their bridges if the script exists
    RELINK_SCRIPT=""
    for i in /etc/network/if-up.d/reset-net-bridges /etc/reset-net-bridges;do
        if [ -e "${i}" ];then
            RELINK_SCRIPT="${i}"
            break
        fi
    done
    if [ "x${DOMAIN}" != "x" ];then DOMAIN_ARG="${DOMAIN_ARG} -s ${DOMAIN} -S /${DOMAIN}/";fi
}

iptables_remove() {
    if iptables -C "${@}" 2>/dev/null;then
        iptables ${use_iptables_lock} -D "${@}"
    fi
}

iptables_add() {
    if ! iptables -C "${@}" 2>/dev/null;then
        iptables ${use_iptables_lock} -I "${@}"
    fi
}

teardown_forward() {
    setup
    iptables_remove INPUT -i ${BRIDGE} -p udp --dport 67 -j ACCEPT
    iptables_remove INPUT -i ${BRIDGE} -p tcp --dport 67 -j ACCEPT
    iptables_remove INPUT -i ${BRIDGE} -p udp --dport 53 -j ACCEPT
    iptables_remove INPUT -i ${BRIDGE} -p tcp --dport 53 -j ACCEPT
    iptables_add OUTPUT -o ${BRIDGE} -p udp --sport 67 -j ACCEPT
    iptables_add OUTPUT -o ${BRIDGE} -p tcp --sport 67 -j ACCEPT
    iptables_add OUTPUT -o ${BRIDGE} -p udp --sport 53 -j ACCEPT
    iptables_add OUTPUT -o ${BRIDGE} -p tcp --sport 53 -j ACCEPT
    iptables_remove FORWARD -i ${BRIDGE} -j ACCEPT
    iptables_remove FORWARD -o ${BRIDGE} -j ACCEPT
    iptables_remove POSTROUTING -t mangle -o ${BRIDGE} -p udp -m udp --dport 68 -j CHECKSUM --checksum-fill
    iptables_remove POSTROUTING -t nat -s "${NETWORK}" ! -d "${NETWORK}" -j MASQUERADE
    stop_dnsmasq
    /bin/true
}

stop_dnsmasq() {
    dpids=$(ps aux | grep dnsmasq | grep -v grep | grep "${BRIDGE}" | awk '{print $2}')
    pids=$(filter_host_pids "${dpids}"|sed -re "s/(^ +)|( +$)//g")
    if [ "x${pids}" != "x" ];then
        for pid in ${pids};do
            kill -9 ${pid} || /bin/true
        done
    fi
}

setup_forward() {
    echo 1 > /proc/sys/net/ipv4/ip_forward
    ret=${?}
    if [ "x${IPTABLES_DISABLED}" = "x" ];then
        iptables_add INPUT -i ${BRIDGE} -p udp --dport 67 -j ACCEPT
        iptables_add INPUT -i ${BRIDGE} -p tcp --dport 67 -j ACCEPT
        iptables_add INPUT -i ${BRIDGE} -p udp --dport 53 -j ACCEPT
        iptables_add INPUT -i ${BRIDGE} -p tcp --dport 53 -j ACCEPT
        iptables_add OUTPUT -o ${BRIDGE} -p udp --sport 67 -j ACCEPT
        iptables_add OUTPUT -o ${BRIDGE} -p tcp --sport 67 -j ACCEPT
        iptables_add OUTPUT -o ${BRIDGE} -p udp --sport 53 -j ACCEPT
        iptables_add OUTPUT -o ${BRIDGE} -p tcp --sport 53 -j ACCEPT
        iptables_add FORWARD -i ${BRIDGE} -j ACCEPT
        iptables_add FORWARD -o ${BRIDGE} -j ACCEPT
        iptables_add POSTROUTING -t mangle -o ${BRIDGE} -p udp -m udp --dport 68 -j CHECKSUM --checksum-fill
        iptables_add POSTROUTING -t nat -s "${NETWORK}" ! -d "${NETWORK}" -j MASQUERADE
    fi
    if [ "x${RELINK_SCRIPT}" != "x" ] && [ -x "${RELINK_SCRIPT}"  ];then "${RELINK_SCRIPT}";fi
    # https://lists.linuxcontainers.org/pipermail/lxc-devel/2014-October/010561.html
    for DNSMASQ_USER in lxc-dnsmasq dnsmasq nobody;do
        if getent passwd ${DNSMASQ_USER} >/dev/null;then break;fi
    done
    if [ "x${DNSMASQ_DISABLED}" = "x" ] && which dnsmasq > /dev/null 2>&1;then
        if [ ! -e /var/lib/misc ];then mkdir -pv "/var/lib/misc";fi
        if [ ! -e "${DNSMASQ_HOSTS_CONFS}" ];then mkdir -pv "${DNSMASQ_HOSTS_CONFS}";fi
        if [ ! -e "${DNSMASQ_CONFS}" ];then mkdir -pv "${DNSMASQ_CONFS}";fi
        chown -Rf "${DNSMASQ_USER}" "${DNSMASQ_CONF_DIR}" "${DNSMASQ_CONFS}" "${DNSMASQ_HOSTS_CONFS}"
        stop_dnsmasq
        if [ -e /etc/dnsmasq.d ];then
            cat > /etc/dnsmasq.d/${BRIDGE}<< EOF
bind-interfaces
except-interface=${BRIDGE}
EOF
        fi
        dnsmasq \
            -u ${DNSMASQ_USER} \
            --strict-order \
            --bind-interfaces \
            --pid-file="${VARRUN}"/dnsmasq.pid \
            --interface=${BRIDGE} \
            --listen-address ${ADDR} \
            $(if [ "x${DHCP_RANGE}" != "x" ];then echo "--dhcp-range ${DHCP_RANGE}";fi) \
            $(if [ "x${DHCP_MAX}" != "x" ];then echo "--dhcp-lease-max=${DHCP_MAX}";fi) \
            ${DOMAIN_ARG} \
            --no-hosts \
            --dhcp-no-override \
            --except-interface=lo \
            --dhcp-leasefile=/var/lib/misc/dnsmasq.${BRIDGE}.leases \
            --addn-hosts="${DNSMASQ_HOSTS_CONFS}" \
            --conf-file=${DHCP_CONF_FILE} \
            --conf-dir="${DNSMASQ_CONFS}" \
            --dhcp-authoritative
        if [ "x${ret}" = "x0" ];then ret="${?}";fi
    fi
    test "x${ret}" = "x0"
}

ifup() {
    ret=0
	if [ -d "/sys/class/net/${1}" ]; then
        # bridge exists, but we didn't start it
        # but reset iptables & maskerading
        echo "${1} already created"
    else
        # set up the lxc network
        if ! brctl addbr "${1}";then
            echo "Missing bridge support in kernel"
            stop
            exit ${?}
        fi
    fi
    which ip >/dev/null 2>&1
    if [ "x${?}" = "x0" ]; then
        mask=`_netmask2cidr ${3}`
        cidr_addr="${2}/${mask}"
        ip addr add "${cidr_addr}" dev "${1}"
        ip link set dev ${1} up
        if [ "x${ret}" = "x0" ];then ret=${?};fi
    fi
    which ifconfig >/dev/null 2>&1
    if [ "x${?}" = "x0" ]; then
        ifconfig ${1} ${2} netmask ${3} up
        if [ "x${ret}" = "x0" ];then ret=${?};fi
    fi
    test "x${ret}" = "x0"
}

ifdown() {
    ret=0
    which ip >/dev/null 2>&1
    if [ ${?} = 0 ]; then
        ip link set dev ${1} down >/dev/null 2>&1
    fi
    which ifconfig >/dev/null 2>&1
    if [ ${?} = 0 ]; then
        ifconfig ${1} down >/dev/null 2>&1
    fi
	if [ -d "/sys/class/net/${1}" ]; then
        brctl delbr ${1} >/dev/null 2>&1
        xret=${?}
        if [ "x${ret}" = "x0" ];then
            ret=${xret}
        fi
    fi
    test "x${ret}" = "x0"
}


create_var_run() {
    # if we are run from systemd on a system with selinux enabled,
    # the mkdir will create /run/lxc as init_var_run_t which dnsmasq
    # can't write its pid into, so we restorecon it (to var_run_t)
    if [ ! -d "${VARRUN}" ]; then
        mkdir -p "${VARRUN}"
        which restorecon >/dev/null 2>&1
        if [ ${?} = 0 ]; then
            restorecon "${VARRUN}"
        fi
    fi
}

setup() {
    set_vars
    create_var_run
}

start() {
    setup
    if [ "x${ACTIVATED}" != "xTrue" ];then
        stop
        exit 0
    fi
	ifup ${BRIDGE} ${ADDR} ${NETMASK}
    ret=${?}
    if [ "x${ret}" != "x0" ];then
        echo "Wont activate traffic handling on ${BRIDGE}"
    else
        setup_forward ${BRIDGE} ${NETWORK}
        ret=${?}
    fi
    test "x${ret}" = "x0"
}

stop() {
    setup
    teardown_forward
    ret=${?}
    ifdown ${BRIDGE}
    ret=${?}
    test "x${ret}" = "x0"
}

# See how we were called.
case "${1}" in
    start)
        start
    ;;

    stop)
        stop
    ;;

    restart|reload|force-reload)
        "${0}" stop
        "${0}" start
    ;;

    *)
        echo "Usage: ${0} {start|stop|restart|reload|force-reload}"
        exit 2
esac

exit ${?}
