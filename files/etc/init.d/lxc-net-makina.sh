#!/bin/sh

### BEGIN INIT INFO
# Provides:             lxc-net-amkina
# Required-Start:       $syslog $remote_fs lxc
# Required-Stop:        $syslog $remote_fs lxc
# Should-Start:
# Should-Stop:
# Default-Start:        2 3 4 5
# Default-Stop:         0 1 6
# Short-Description:    Linux Containers Network Configuration (makina)
# Description:          Linux Containers Network Configuration (makina)
# X-Start-Before:
# X-Stop-After:
# X-Interactive:        true
### END INIT INFO

# Taken from ubuntu's lxc-net upstart config and adopted to init script
# original author: Serge Hallyn <serge.hallyn@canonical.com>

USE_LXC_BRIDGE="{{use_bridge}}"
USE_LXC_BRIDGE="{{use_bridge}}"
LXC_MAKINA_BRIDGE="{{bridge}}"
LXC_MAKINA_ADDR="{{gateway}}"
LXC_MAKINA_NETMASK="{{netmask_full}}"
LXC_MAKINA_NETWORK="{{network}}/{{netmask}}"
varrun="/var/run/lxc"
LXC_DOMAIN=""
LXC_MAKINA_DOMAIN=""

. /lib/lsb/init-functions

start() {
    [ -f /etc/default/lxc ] && . /etc/default/lxc

    [ "x$USE_LXC_BRIDGE" = "xtrue" ] || { exit 0; }

    if [ -d /sys/class/net/${LXC_MAKINA_BRIDGE} ]; then
        if [ ! -f ${varrun}/network_up ]; then
            # bridge exists, but we didn't start it
            exit 0;
        fi
        exit 0;
    fi

    cleanup() {
        # dnsmasq failed to start, clean up the bridge
        iptables -t nat -D POSTROUTING -s ${LXC_MAKINA_NETWORK} ! -d ${LXC_MAKINA_NETWORK} -j MASQUERADE || true
        ifconfig ${LXC_MAKINA_BRIDGE} down || true
        brctl delbr ${LXC_MAKINA_BRIDGE} || true
    }

    # set up the lxc network
    brctl addbr ${LXC_MAKINA_BRIDGE} || { echo "Missing bridge support in kernel"; exit 0; }
    echo 1 > /proc/sys/net/ipv4/ip_forward
    mkdir -p ${varrun}
    ifconfig ${LXC_MAKINA_BRIDGE} ${LXC_MAKINA_ADDR} netmask ${LXC_MAKINA_NETMASK} up
    iptables -t nat -A POSTROUTING -s ${LXC_MAKINA_NETWORK} ! -d ${LXC_MAKINA_NETWORK} -j MASQUERADE

    LXC_MAKINA_DOMAIN_ARG=""
    if [ -n "$LXC_MAKINA_DOMAIN" ]; then
        LXC_MAKINA_DOMAIN_ARG="-s $LXC_MAKINA_DOMAIN"
    fi
    touch ${varrun}/network_up
}

stop() {
    [ -f /etc/default/lxc ] && . /etc/default/lxc
    [ -f "${varrun}/network_up" ] || exit 0;
    # if $LXC_MAKINA_BRIDGE has attached interfaces, don't shut it down
    ls /sys/class/net/${LXC_MAKINA_BRIDGE}/brif/* > /dev/null 2>&1 && exit 0;

    if [ -d /sys/class/net/${LXC_MAKINA_BRIDGE} ]; then
        ifconfig ${LXC_MAKINA_BRIDGE} down
        iptables -t nat -D POSTROUTING -s ${LXC_MAKINA_NETWORK} ! -d ${LXC_MAKINA_NETWORK} -j MASQUERADE || true
        brctl delbr ${LXC_MAKINA_BRIDGE}
    fi
    rm -f ${varrun}/network_up
}

case "${1}" in
    start)
        log_daemon_msg "Starting Linux Containers"

        start
        ;;

    stop)
        log_daemon_msg "Stopping Linux Containers"

        stop
        ;;

    restart|force-reload)
        log_daemon_msg "Restarting Linux Containers"

        stop
        start
        ;;
esac
# vim:set et sts=4 ts=4 tw=80:
