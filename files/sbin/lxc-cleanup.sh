#!/usr/bin/env bash
# managed via salt, do not edit
# freeze hostile packages
FROZEN_PACKAGES="udev whoopsie ntp fuse grub-common grub-pc grub-pc-bin grub2-common"
# specific to docker
if [ -f /.dockerinit ];then
    FROZEN_PACKAGES="$FROZEN_PACKAGES resolvconf"
fi
for i in $FROZEN;do
    echo $i hold | dpkg --set-selections || /bin/true
done
# disabling fstab
for i in /lib/init/fstab /etc/fstab;do
    echo > $i || /bin/true
done
#pruning old logs & pids
rm -rf /var/run/network/* || /bin/true
# comment out the ntpdate ifup plugin inside a container
if [ -f /etc/network/if-up.d/ntpdate ];then
    sed -re "s/^(([^#].*)|)$/#\\1/g" -i /etc/network/if-up.d/ntpdate
fi
for i in /var/run/*.pid /var/run/dbus/pid /etc/nologin;do
    if [ -e $i ];then
        rm -f $i || /bin/true
    fi
done
# no apparmor in container
update-rc.d -f apparmor remove || /bin/true
# disabling useless and harmfull services
for f in\
    $(find /etc/init -name console-setup.conf)\
    $(find /etc/init -name procps.conf)\
    $(find /etc/init -name dbus.conf)\
    $(find /etc/init -name acpid.conf)\
    $(find /etc/init -name apport.conf)\
    $(find /etc/init -name control-alt-delete.conf)\
    $(find /etc/init -name cryptdisks-enable.conf)\
    $(find /etc/init -name cryptdisks-udev.conf)\
    $(find /etc/init -name dmesg.conf)\
    $(find /etc/init -name failsafe.conf)\
    $(find /etc/init -name mountall-net.conf )\
    $(find /etc/init -name mountall-reboot.conf)\
    $(find /etc/init -name mountall-shell.conf)\
    $(find /etc/init -name mounted-debugfs.conf )\
    $(find /etc/init -name mounted-dev.conf)\
    $(find /etc/init -name mounted-proc.conf)\
    $(find /etc/init -name mounted-run.conf)\
    $(find /etc/init -name mounted-tmp.conf)\
    $(find /etc/init -name mounted-var.conf)\
    $(find /etc/init -name setvtrgb.conf)\
    $(find /etc/init -name systemd-logind.conf)\
    $(find /etc/init -name udev*.conf)\
    $(find /etc/init -name ureadahead*.conf)\
    $(find /etc/init -name plymouth*.conf)\
    $(find /etc/init -name hwclock*.conf)\
    $(find /etc/init -name module*.conf)\
    ;do SERVICES_DISABLED="$SERVICES_DISABLED $f";done
# services only harmfull in a docker
if [ -f /.dockerinit ];then
    for f in\
        $(find /etc/init -name resolvconf.conf)\
        $(find /etc/init -name cloud-init-container.conf)\
        $(find /etc/init -name cloud-init.conf)\
        $(find /etc/init -name cloud-init-local.conf)\
        $(find /etc/init -name cloud-init-nonet.conf)\
        $(find /etc/init -name console.conf)\
        $(find /etc/init -name console-setup.conf)\
        $(find /etc/init -name hostname.conf)\
        $(find /etc/init -name networking.conf)\
        $(find /etc/init -name network-interface-security.conf)\
        $(find /etc/init -name tty[1-9].conf)\
        $(find /etc/init -name upstart*.conf)\
        $(find /etc/init -name upstart-dbus-bridge.conf)\
    ;do SERVICES_DISABLED="$SERVICES_DISABLED $f";done
fi
for f in $SERVICES_DISABLED;do
    echo manual>"/etc/init/$(basename $f .conf).override"
    mv -f "$f" "$f.orig"
done
# disabling useless and harmfull sysctls
for i in \
    vm.mmap_min_addr\
    fs.protected_hardlinks\
    fs.protected_symlinks\
    kernel.yama.ptrace_scope\
    kernel.kptr_restrict\
    kernel.printk;do
    sed -re "s/^($i)/#\1/g" -i \
    /etc/sysctl*/* /etc/sysctl.conf || /bin/true
done
# uid accouting is broken in lxc, breaking in turn pam_ssh login
sed -re "s/^(session.*\spam_loginuid\.so.*)/#\\1/g" -i /etc/pam.d/* || /bin/true
# specific to docker
if [ -f /.dockerinit ];then
    # redirecting console to docker log
    for i in console tty0 tty1 tty2 tty3 tty4 tty5 tty6 tty7;do
        rm -f /dev/$i || /bin/true
        ln -s /dev/tty /dev/$i || /bin/true
    done
    en="/etc/network"
    if [ -f $en/if-up.d/000resolvconf ];then
        mv -f $en/if-up.d/000resolvconf $en/if-up.d_000resolvconf.bak || /bin/true
    fi
    if [ -f $en/if-down.d/resolvconf ];then
        mv -f $en/if-down.d/resolvconf $en/if-down.d_resolvconf.bak || /bin/true
    fi
fi
if [ -f /etc/lsb-release ];then
    . /etc/lsb-release
fi
# if this isn't lucid, then we need to twiddle the network upstart bits :(
if [ -f /etc/network/if-up.d/upstart ] &&\
   [ $DISTRIB_CODENAME != "lucid" ];then
        sed -i 's/^.*emission handled.*$/echo Emitting lo/' /etc/network/if-up.d/upstart
fi
exit 0
# vim:set et sts=4 ts=4 tw=80:
