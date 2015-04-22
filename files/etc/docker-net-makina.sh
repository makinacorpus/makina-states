#!/usr/bin/env bash
USE_DOCKER_BRIDGE="True"
DOCKER_MAKINA_BRIDGE="docker1"
DOCKER_MAKINA_ADDR="10.7.0.1"
DOCKER_MAKINA_NETMASK="255.255.0.0"
DOCKER_MAKINA_NETWORK="10.7.0.0/16"
varrun="/var/run/docker"
DOCKER_DOMAIN=""
DOCKER_MAKINA_DOMAIN=""

if [ -f /etc/default/docker ];then
    . /etc/default/docker
fi
if [ -f /etc/default/docker-net-makina ];then
    . /etc/default/docker-net-makina
fi

cleanup() {
    # dnsmasq failed to start, clean up the bridge
    iptables -t nat -D POSTROUTING -s ${DOCKER_MAKINA_NETWORK} ! -d ${DOCKER_MAKINA_NETWORK} -j MASQUERADE || true
    ifconfig ${DOCKER_MAKINA_BRIDGE} down || true
    brctl delbr ${DOCKER_MAKINA_BRIDGE} || true
}

start() {
    if [ "x${USE_DOCKER_BRIDGE}" != "xTrue" ];then
        stop
        exit 0
    fi
	if [ -d "/sys/class/net/${DOCKER_MAKINA_BRIDGE}" ]; then
		if [ ! -f "${varrun}/network_up" ]; then
			# bridge exists, but we didn't start it
			stop;
		fi
		exit 0;
	fi
	# set up the docker network
    if ! brctl addbr "${DOCKER_MAKINA_BRIDGE}";then
        echo "Missing bridge support in kernel"
        stop
        exit 0
    fi
    echo 1 > /proc/sys/net/ipv4/ip_forward
    mkdir -p "${varrun}"
	ifconfig ${DOCKER_MAKINA_BRIDGE} ${DOCKER_MAKINA_ADDR} netmask ${DOCKER_MAKINA_NETMASK} up
	iptables -t nat -A POSTROUTING -s ${DOCKER_MAKINA_NETWORK} ! -d ${DOCKER_MAKINA_NETWORK} -j MASQUERADE
	DOCKER_MAKINA_DOMAIN_ARG=""
    if [ "x${DOCKER_MAKINA_DOMAIN}" != "x" ];then
        DOCKER_MAKINA_DOMAIN_ARG="-s ${DOCKER_MAKINA_DOMAIN}"
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
	if [ -d "/sys/class/net/${DOCKER_MAKINA_BRIDGE}" ]; then
		ifconfig ${DOCKER_MAKINA_BRIDGE} down
		iptables -t nat -D POSTROUTING -s "${DOCKER_MAKINA_NETWORK}" ! -d "${DOCKER_MAKINA_NETWORK}" -j MASQUERADE || true
		brctl delbr "${DOCKER_MAKINA_BRIDGE}"
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
