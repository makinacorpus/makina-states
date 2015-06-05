#!/usr/bin/env bash
# managed via salt, do not edit
# freeze hostile packages
is_docker=""
from_systemd="y"
for i in ${@};do
    if [ "x${i}" = "xsystemd" ];then
        from_systemd="y"
    fi
done
for i in /.dockerinit /.dockerenv;do
    if [ -f "${i}" ];then
        is_docker="1"
        break
    fi
done
if [ "x${is_docker}" != "x" ];then
    if [ "x$(grep -q "system.slice/docker-" /proc/1/cgroup 2>/dev/null;echo ${?})" = "x0" ];then
        is_docker="1"
    fi
fi
FROZEN_PACKAGES="udev whoopsie ntp fuse grub-common grub-pc grub-pc-bin grub2-common"
# specific to docker
# if [ "x${is_docker}" != "x" ];then
#     FROZEN_PACKAGES="${FROZEN_PACKAGES} resolvconf"
# fi
for i in ${FROZEN_PACKAGES};do
    echo ${i} hold | dpkg --set-selections || /bin/true
done
# on docker, disable dhcp on main if unless we explicitly configure the image to
if [ ! -f /etc/docker_custom_network ] && [ "x${is_docker}" != "x" ];then
    sed -i  -re "/(auto.*eth0)(eth0.*dhcp)/d" /etc/network/interfaces || /bin/true
fi
# disabling fstab
for i in /lib/init/fstab /etc/fstab;do
    echo > ${i} || /bin/true
done
#pruning old logs & pids
rm -rf /var/run/network/* || /bin/true
# comment out the ntpdate ifup plugin inside a container
if [ -f /etc/network/if-up.d/ntpdate ];then
    sed -re "s/^(([^#].*)|)$/#\\1/g" -i /etc/network/if-up.d/ntpdate
fi
for i in /var/run/*.pid /var/run/dbus/pid /etc/nologin;do
    if [ -e "${i}" ];then
        rm -f "${i}" || /bin/true
    fi
done
# disabling useless and harmfull services
#    $(find /etc/init -name dbus.conf)\
# instead of delete the proccps service, reset it to do nothing by default
#    $(find /etc/init -name procps.conf)\
syscfgs="/etc/sysctl.conf"
if [ -e /etc/sysctl.d ];then
    syscfgs="${syscfgs} $(ls /etc/sysctl.d/*conf)"
fi
for syscfg in ${syscfgs};do
    if [ "x$(grep -q mastersalt-cleanup "${syscfg}";echo ${?})" != "x0" ];then
        sed -i -e "s/^/#/g" "${syscfg}" ||/bin/true
        echo "# mastersalt-cleanup" >> "${syscfg}" ||/bin/true
    fi
done
# reacticated services
reactivated_services="procps"
for reactivated_service in ${reactivated_services};do
    if [ -e "/etc/init/${reactivated_service}.conf.orig" ];then
        mv -f "/etc/init/${reactivated_service}.conf.orig" "/etc/init/${reactivated_service}.conf" ||/bin/true
    fi
    if [ -e "/etc/init/${reactivated_service}.override" ];then
        rm -f "${reactivated_service}.override" ||/bin/true
    fi
done
# - we must need to rely on direct file system to avoid relying on running process
#    manager (pid: 1)
# do not activate those evil services in a container context
for s in\
    acpid\
    apparmor\
    apport\
    atop\
    console-setup\
    control-alt-delete\
    cryptdisks-enable\
    cryptdisks-udev\
    dmesg\
    failsafe\
    hwclock\
    module\
    mountall-net\
    mountall-reboot\
    ufw\
    pppd-dns\
    systemd-remount-fs\
    lvm2-monitor\
    dns-clean\
    lvm2-lvmetad\
    mountall-shell\
    mounted-debugfs\
    mounted-dev\
    mounted-proc\
    mounted-run\
    mounted-tmp\
    mounted-var\
    ondemand\
    plymouth\
    setvtrgb\
    smartd\
    smartmontools\
    systemd-modules-load\
    udev\
    udev-finish\
    umountfs\
    umountroot\
    ureadahead\
    systemd-udevd.service\
    systemd-udev-trigger\
    vnstat\
   ;do
    # upstart
    for i in /etc/init/${s}*.conf;do
        if [ -e "${i}" ];then
            echo manual>"/etc/init/$(basename ${i} .conf).override" || /bin/true
            mv -f "${i}" "${i}.orig" || /bin/true
        fi
    done
    # systemd
    for d in /lib/systemd /etc/systemd /usr/lib/systemd;do
        rm -vf "${d}/"*/*.wants/${s}.service || /bin/true
    done
    # sysV
    for i in 0 1 2 3 4 5 6;do
       rm -vf /etc/rc${i}.d/*${s} || /bin/true
    done
done
# disabling useless and harmfull sysctls
for i in \
    vm.mmap_min_addr\
    fs.protected_hardlinks\
    fs.protected_symlinks\
    kernel.yama.ptrace_scope\
    kernel.kptr_restrict\
    kernel.printk;do
    sed -re "s/^(${i})/#\1/g" -i \
    /etc/sysctl*/* /etc/sysctl.conf || /bin/true
done
# uid accouting is broken in lxc, breaking in turn pam_ssh login
sed -re "s/^(session.*\spam_loginuid\.so.*)/#\\1/g" -i /etc/pam.d/* || /bin/true
# specific to docker
if [ "x${is_docker}" != "x" ];then
    # redirecting console to docker log
    for i in console tty0 tty1 tty2 tty3 tty4 tty5 tty6 tty7;do
        rm -f /dev/${i} || /bin/true
        ln -s /dev/tty /dev/${i} || /bin/true
    done
    # disable resolvconf
    # en="/etc/network"
    # if [ -f ${en}/if-up.d/000resolvconf ];then
    #     mv -f ${en}/if-up.d/000resolvconf ${en}/if-up.d_000resolvconf.bak || /bin/true
    # fi
    # if [ -f ${en}/if-down.d/resolvconf ];then
    #     mv -f ${en}/if-down.d/resolvconf ${en}/if-down.d_resolvconf.bak || /bin/true
    # fi
fi
if [ -f /etc/lsb-release ];then
    . /etc/lsb-release
fi
# if this isn't lucid, then we need to twiddle the network upstart bits :(
if [ -f /etc/network/if-up.d/upstart ] &&\
   [ ${DISTRIB_CODENAME} != "lucid" ];then
        sed -i 's/^.*emission handled.*$/echo Emitting lo/' /etc/network/if-up.d/upstart
fi
exit 0
# vim:set et sts=4 ts=4 tw=80:
