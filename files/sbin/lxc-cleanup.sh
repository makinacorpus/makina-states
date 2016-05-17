#!/usr/bin/env bash
# managed via salt, do not edit
# freeze hostile packages
if [ -f /etc/lsb-release ];then . /etc/lsb-release;fi
is_upstart="$(echo $(/sbin/init --version || /bin/true) | sed "s/.*upstart.*/matched/g")"
is_docker=""
from_systemd="y"
for i in ${@};do
    if [ "x${i}" = "xsystemd" ];then
        from_systemd="y"
    fi
done
echo $is_upstart
if [ "x${is_upstart}" = "xmatched" ];then
    is_upstart="y"
else
    is_upstart=""
fi
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
FROZEN_PACKAGES="whoopsie ntp fuse grub-common grub-pc grub-pc-bin grub2-common"
RELEASE=$(lsb_release -s -r||echo "14.04")
if [[ "${RELEASE}" -lt "16.04" ]];then
    FROZEN_PACKAGES="${FROZEN_PACKAGES} udev"
fi
# specific to docker
# if [ "x${is_docker}" != "x" ];then
#     FROZEN_PACKAGES="${FROZEN_PACKAGES} resolvconf"
# fi
for i in ${FROZEN_PACKAGES};do
    echo ${i} hold | dpkg --set-selections || /bin/true
done
# on docker, disable dhcp on main if unless we explicitly configure the image to
if [ "x${is_docker}" != "x" ];then
    if [ -f /etc/docker_custom_network ] || [ "x${DOCKER_CUSTOM_NETWORK}" != "x" ];then
        echo "asked not to unwire dhcp on eth0"
    else
        sed -i -re "/(auto.*eth0)|(eth0.*dhcp)/d" /etc/network/interfaces || /bin/true
    fi
    # remove /dev/xconsole PIPE from lxc template
    if [ -p /dev/xconsole ];then
        rm -f /dev/xconsole
    fi
fi
# disabling fstab
for i in /lib/init/fstab /etc/fstab;do
    echo > ${i} || /bin/true
done
#pruning old logs & pids
rm -rf /var/run/network/* || /bin/true
rm -f /var/run/rsyslogd.pid || /bin/true
# comment out the ntpdate ifup plugin inside a container
if [ -f /etc/network/if-up.d/ntpdate ];then
    sed -re "s/^(([^#].*)|)$/#\\1/g" -i /etc/network/if-up.d/ntpdate
fi
for i in /var/run/*.pid /var/run/dbus/pid /etc/nologin;do
    if [ -e "${i}" ];then
        rm -f "${i}" || /bin/true
    fi
done
# disable rsyslog console logging
if [ -e /etc/rsyslog.d/50-default.conf ];then
    sed -i -re '/^\s*daemon.*;mail.*/ { N;N;N; s/^/#/gm }'\
        /etc/rsyslog.d/50-default.conf || /bin/true
fi
# reacticated services that were disabled in an earlier time
for reactivated_service in procps;do
    if [ -e "/etc/init/${reactivated_service}.conf.orig" ];then
        mv -f "/etc/init/${reactivated_service}.conf.orig" "/etc/init/${reactivated_service}.conf" ||/bin/true
    fi
    if [ -e "/etc/init/${reactivated_service}.override" ];then
        rm -f "${reactivated_service}.override" ||/bin/true
    fi
done
if [ -f /etc/systemd/logind.conf ];then
    for i in NAutoVTs ReserveVT;do
        sed -i -re "/${i}/ d" /etc/systemd/logind.conf
        echo "${i}=0">>/etc/systemd/logind.conf
    done
fi
# disabling useless and harmfull services
#    $(find /etc/init -name dbus.conf)\
# instead of delete the proccps service, reset it to do nothing by default
#    $(find /etc/init -name procps.conf)\
# - we must need to rely on direct file system to avoid relying on running process
#    manager (pid: 1)
# do not activate those evil services in a container context
# tty units (systemd) are only evil if the lock the first console
disable_service() {
    s="$1"
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
    if [ -e /etc/systemd/system ];then
        ln -sfv /dev/null "/etc/systemd/system/${s}.service"
    fi
    # sysV
    for i in 0 1 2 3 4 5 6;do
       rm -vf /etc/rc${i}.d/*${s} || /bin/true
    done
}
systemd_reactivated="
    systemd-update-utmp\
    systemd-update-utmp-runlevel\
    udev\
    udev-finish\
"
for s in\
    acpid\
    alsa-restore\
    alsa-state\
    alsa-store\
    apparmor\
    apport\
    atop\
    control-alt-delete\
    cryptdisks-enable\
    cryptdisks-udev\
    debian-fixup\
    display-manager\
    dmesg\
    dns-clean\
    failsafe\
    hwclock\
    kmod-static-nodes\
    lvm2-lvmetad\
    lvm2-monitor\
    module\
    mountall-net\
    mountall-reboot\
    mountall-shell\
    mounted-debugfs\
    mounted-dev\
    mounted-proc\
    mounted-run\
    mounted-tmp\
    mounted-var\
    ondemand\
    plymouth\
    plymouth-halt\
    plymouth-kexec\
    plymouth-read-write\
    plymouth-start\
    plymouth-switch-root\
    pppd-dns\
    setvtrgb\
    smartd\
    smartmontools\
    systemd-binfmt\
    systemd-hwdb-update\
    systemd-journal-flush\
    systemd-machine-id-commit\
    systemd-modules-load\
    systemd-remount-fs\
    systemd-timesyncd\
    ufw\
    umountfs\
    umountroot\
    ureadahead\
    vnstat\
    accounts-daemon\
    systemd-ask-password-wall\
    systemd-ask-password-console\
    serial-getty@\
    autovt@\
    getty@\
    console-setup\
    container-getty@\
    getty-static\
    console-getty\
    user@\
    systemd-logind\
    getty@tty1\
   ;do
    disable_service "${s}"
done
if [ "x${is_docker}" != "x" ];then
    # redirecting console to docker log
    for i in systemd-update-utmp ifup-wait-all-auto;do
        disable_service ${i}
    done
fi
for s in\
    tmp.mount\
    sys-kernel-config.mount\
    multi-user.target.wants/systemd-ask-password-wall.path\
    systemd-journald-audit.socket\
    ;do
    for d in /lib/systemd /etc/systemd /usr/lib/systemd;do
        if [ -e "${d}/system/${s}" ];then
            rm -vf "${d}/"*/*.wants/${s} || /bin/true
            ln -sfv /dev/null "/etc/systemd/system/${s}"
        fi
    done
done
if [ -e /run/systemd/journal/dev-log ] || [ -e /lib/systemd/systemd ];then
    if [ -e /dev/log ];then rm -f /dev/log;fi
    ln -fs /run/systemd/journal/dev-log /dev/log
fi
# disable harmful sysctls
syscfgs="/etc/sysctl.conf"
if [ -e /etc/sysctl.d ];then
    syscfgs="${syscfgs} $(ls /etc/sysctl.d/*conf)"
fi
for syscfg in ${syscfgs};do
    if [ "x$(grep -q salt-cleanup "${syscfg}";echo ${?})" != "x0" ];then
        sed -i -e "s/^/#/g" "${syscfg}" ||/bin/true
        echo "# salt-cleanup" >> "${syscfg}" ||/bin/true
    fi
    for i in \
        vm.mmap_min_addr\
        fs.protected_hardlinks\
        fs.protected_symlinks\
        kernel.yama.ptrace_scope\
        kernel.kptr_restrict\
        kernel.printk;do
        sed -i -re "s/^(${i})/#\1/g" -i "${syscfg}" || /bin/true
    done
done
# if ssh keys were removed, be sure to have new keypairs before sshd (re)start
ssh_keys=""
find /etc/ssh/ssh_host_*_key -type f || ssh_keys="1"
if [ -e /etc/ssh ] && [ "x${ssh_keys}" != "x" ];then
    ssh-keygen -f /etc/ssh/ssh_host_rsa_key -N '' -t rsa -b 4096 || /bin/true
    ssh-keygen -f /etc/ssh/ssh_host_dsa_key -N '' -t dsa -b 1024 || /bin/true
    ssh-keygen -f /etc/ssh/ssh_host_ed25519_key -N '' -t ed25519 || /bin/true
    ssh-keygen -f /etc/ssh/ssh_host_ecdsa_key   -N '' -t  ecdsa  || /bin/true
fi
# uid accouting is broken in lxc, breaking in turn pam_ssh login
sed -re "s/^(session.*\spam_loginuid\.so.*)/#\\1/g" -i /etc/pam.d/* || /bin/true
# specific to docker
if [ "x${is_docker}" != "x" ];then
    # redirecting console to docker log
    for i in console tty0 tty1 tty2 tty3 tty4 tty5 tty6 tty7;do
        rm -f /dev/${i} || /bin/true
        ln -s /dev/tty /dev/${i} || /bin/true
    done
fi
# if this isn't lucid, then we need to twiddle the network upstart bits :(
if [ -f /etc/network/if-up.d/upstart ] &&\
   [ ${DISTRIB_CODENAME} != "lucid" ];then
    sed -i 's/^.*emission handled.*$/echo Emitting lo/' /etc/network/if-up.d/upstart
fi
# if we found the acl restore flag, apply !
if which setfacl >/dev/null 2>&1 && test -e /acls.restore && test -e /acls.txt;then
    cd / && setfacl --restore="/acls.txt" || /bin/true
fi
# uber important: be sure that the notify socket is writable by everyone
# as systemd service like rsyslog notify about their state this way
# and debugging notiication failure is really hard
if [ -e /var/run/systemd/notify ];then chmod 777 /var/run/systemd/notify;fi
# dbus will need the directory to start
for i in /run/systemd/system /run/uuid;do
    if [ "x${is_upstart}" = "x" ];then
        if [ ! -d ${i} ];then mkdir -p ${i};fi
    else
        if [ "x${i}" = "x/run/systemd/system" ];then
            if [ -d ${i} ];then
                rm -rf "${i}"
            fi
        fi
    fi
done
# if we found the password reset flag, reset any password found
if [ -e /.reset_passwords ];then /sbin/reset-passwords.sh || /bin/true;fi
exit 0
# vim:set et sts=4 ts=4 tw=80:
