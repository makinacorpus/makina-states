#!/usr/bin/env bash
# echo 1>/proc/sys/net/ipv4/ip_forward || /bin/true
for i in OUTPUT INPUT FORWARD;do
    iptables -t filter -P ${i} ACCEPT
    iptables -t filter -F ${i}
done
for i in PREROUTING INPUT FORWARD OUTPUT POSTROUTING;do
    iptables -t mangle -P ${i} ACCEPT
    iptables -t mangle -F ${i}
done
for i in PREROUTING INPUT OUTPUT POSTROUTING;do
    iptables -t nat -P ${i} ACCEPT
    iptables -t nat -F ${i}
done
# vim:set et sts=4 ts=4 tw=80:
