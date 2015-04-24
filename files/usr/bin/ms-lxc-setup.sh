#!/usr/bin/env bash
FAKED="apport acpid udevtrigger udevmount-all"
# docker specific
if [ -f "/.dockerinit" ];then
    FAKED="$FAKED resolvconf networking hostname tty{1,2,3,4,5,6,7,8,9}"
    # configuring network is done by lxc / docker
    cat > /etc/network/interfaces << EOF
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
# auto eth0
# iface eth0 inet dhcp

EOF
fi
mount -t tmpfs none  /dev/shm || /bin/true
if [ -f /sbin/lxc-cleanup.sh ];then
    chmod +x /sbin/lxc-cleanup.sh || /bin/true
    /sbin/lxc-cleanup.sh &2>/dev/null || /bin/true
fi
if [ ! -e /etc/ssh/ssh_host_rsa_key ];then
    dpkg-reconfigure openssh-server || /bin/true
fi
if [ "x${1}" = "xupstart" ];then
    /sbin/initctl emit started JOB=console --no-wait
fi
touch /var/run/utmp || /bin/true
chown root:utmp /var/run/utmp || /bin/true
chmod 664 /var/run/utmp || /bin/true
if [ "x${1}" = "xupstart" ];then
    for j in;do
        for l in waiting starting pre-start spawned post-start running;do
            /sbin/initctl emit --no-wait $l JOB=$j || /bin/true
        done
    done
    /sbin/initctl emit --no-wait container CONTAINER=lxc || /bin/true
    for j in mounting mounted all-swaps filesystem virtual-filesystems net-device-up local-filesystems remote-filesystems;do
        /sbin/initctl emit --no-wait $j || /bin/true
    done
fi
service container-detect restart || /bin/true
service rc-sysinit start || /bin/true
/bin/true
# vim:set et sts=4 ts=4 tw=80:
