#!/usr/bin/env bash
USE_LXC_BRIDGE="True"
LXC_MAKINA_BRIDGE="lxcbr1"
LXC_MAKINA_ADDR="10.5.0.1"
LXC_MAKINA_NETMASK="255.255.0.0"
LXC_MAKINA_NETWORK="10.5.0.0/16"
varrun="/var/run/lxc"
LXC_DOMAIN=""
LXC_MAKINA_DOMAIN=""

if [ -f /etc/default/lxc ];then
    . /etc/default/lxc
fi
if [ -f /etc/default/lxc-net-makina ];then
    . /etc/default/lxc-net-makina
fi

cleanup() {
    # dnsmasq failed to start, clean up the bridge
    iptables -t nat -D POSTROUTING -s ${LXC_MAKINA_NETWORK} ! -d ${LXC_MAKINA_NETWORK} -j MASQUERADE || true
    ifconfig ${LXC_MAKINA_BRIDGE} down || true
    brctl delbr ${LXC_MAKINA_BRIDGE} || true
}

start() {
    if [ "x${USE_LXC_BRIDGE}" != "xTrue" ];then
        stop
        exit 0
    fi
	if [ -d "/sys/class/net/${LXC_MAKINA_BRIDGE}" ]; then
		if [ ! -f "${varrun}/network_up" ]; then
			# bridge exists, but we didn't start it
			stop;
		fi
		exit 0;
	fi
	# set up the lxc network
    if ! brctl addbr "${LXC_MAKINA_BRIDGE}";then
        echo "Missing bridge support in kernel"
        stop
        exit 0
    fi
    echo 1 > /proc/sys/net/ipv4/ip_forward
    mkdir -p "${varrun}"
	ifconfig ${LXC_MAKINA_BRIDGE} ${LXC_MAKINA_ADDR} netmask ${LXC_MAKINA_NETMASK} up
	iptables -t nat -A POSTROUTING -s ${LXC_MAKINA_NETWORK} ! -d ${LXC_MAKINA_NETWORK} -j MASQUERADE
	LXC_MAKINA_DOMAIN_ARG=""
    if [ "x${LXC_MAKINA_DOMAIN}" != "x" ];then
        LXC_MAKINA_DOMAIN_ARG="-s ${LXC_MAKINA_DOMAIN}"
	fi
    # relink interfaces with their bridges if the script exists
    relink_script=""
    for i in /etc/network/if-up.d/reset-net-bridges /etc/reset-net-bridges;do
        if [ -e "${i}" ];then
            relink_script="${i}"
            break
        fi
    done
    if [ "x${relink_script}" != "x" ];then
        "${relink_script}"
    fi
}

stop() {
	if [ -d "/sys/class/net/${LXC_MAKINA_BRIDGE}" ]; then
		ifconfig ${LXC_MAKINA_BRIDGE} down
		iptables -t nat -D POSTROUTING -s "${LXC_MAKINA_NETWORK}" ! -d "${LXC_MAKINA_NETWORK}" -j MASQUERADE || true
		brctl delbr "${LXC_MAKINA_BRIDGE}"
	fi
}

set -e
if [ "x${1}" = "xstart" ];then
    start
elif [ "x${1}" = "xstop" ];then
    stop
elif [ "x${1}" = "xrestart" ] || [ "x${1}" = "xreload" ];then
    stop
    start
else
    exit 1
fi
