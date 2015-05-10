#!/usr/bin/env bash
if [ -f /etc/rc.local.d/shorewall.sh ];then
    todo="x"
fi
if [ "${1}" != "x" ];then
    todo="x"
fi
if [ "x${todo}" != "x" ];then
    for i in shorewall shorewall6;do
        update-rc.d -f shorewall remove || /bin/true
        if [ -e /etc/init/${i}.conf ];then
          echo manual>/etc/init/${i}.override
        fi
        # do not touch the rules !
        # too smelly on prod
        #${i} stop || /bin/true
        #service ${i} stop || /bin/true
    done
    rm -f /etc/rc.local.d/shorewall.sh
    # try to remove shorewall failed acquired lock
    ps aux|grep iptables|grep -- -w|awk '{print $2}'|xargs kill -9
    echo 1>/proc/sys/net/ipv4/ip_forward || /bin/true
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
fi
# vim:set et sts=4 ts=4 tw=80:
