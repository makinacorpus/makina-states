#!/usr/bin/env bash
if [ "x${1}" = "xupstart" ];then
    for j in filesystem virtual-filesystems net-device-up local-filesystems remote-filesystems;do
        /sbin/initctl emit --no-wait $j || /bin/true
    done
    /sbin/initctl emit --no-wait net-device-added INTERFACE=lo || /bin/true
    /sbin/initctl emit --no-wait container CONTAINER=lxc || /bin/true
    #for j in apport resolvconf acpid udevtrigger udev networking mount-all hostname tty{1,2,3,4,5,6,7,8,9};do
    for j in apport acpid udevtrigger udev mount-all hostname tty{1,2,3,4,5,6,7,8,9};do
        for l in pre-stop stopping killed post-stop;do
            /sbin/initctl emit --no-wait $l JOB=$j || /bin/true
        done
    done
fi
if [ -f /sbin/lxc-cleanup.sh ];then
    chmod +x /sbin/lxc-cleanup.sh || /bin/true
    /sbin/lxc-cleanup.sh || /bin/true
fi
# vim:set et sts=4 ts=4 tw=80:
