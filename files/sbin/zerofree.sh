#!/usr/bin/env bash
echo " [*] Zerofreeing"
apt-get install -y --force-yes zerofree
echo s > /proc/sysrq-trigger
echo s > /proc/sysrq-trigger
echo u > /proc/sysrq-trigger
mount -o remount,ro /
zerofree -v {{rootdev}}
mount -o remount,rw /
# vim:set et sts=4 ts=4 tw=80:
