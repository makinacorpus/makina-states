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
fi
# vim:set et sts=4 ts=4 tw=80: