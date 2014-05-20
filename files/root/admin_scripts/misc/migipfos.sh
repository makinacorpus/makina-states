#!/usr/bin/env bash
# helper for online FO migration
set -x
while true;do
        ifdown eth0:0
        ifdown eth0
        dhclient eth0
        ps aux|grep dhclient|awk '{print $2}'|xargs kill -9
        ifdown eth0
        ifdown eth0:0
        ifup eth0
        ifup eth0:0
        shorewall restart
        sleep 60
done

