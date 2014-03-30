#!/usr/bin/env bash
#
# Mount all running lxc containers under a prefix in /srv/lxc to each developers
# access to underlying filesystem to do liveedit
#
TYPE=$(cat /etc/makina-states/nodetype 2>/dev/null;/bin/true)
sshfs=$(which sshfs 2>/dev/null)
FUSERMOUNT="fusermount"
RED="\\e[0;31m"
CYAN="\\e[0;36m"
YELLOW="\\e[0;33m"
YELLOW="\\e[0;33m"
NORMAL="\\e[0;0m"

if [ "x${NO_COLORS}" != "x" ];then
    YELLOW=""
    RED=""
    CYAN=""
    NORMAL=""
fi

log(){
    printf "${RED} [devhost] ${@}${NORMAL}\n" 1>&2
}


get_sshfs_ps() {
    # be sure to test for the end of the path not to
    # umount near by or in-folder sub-VMs
    ps aux|egrep "sshfs.*${VM}\$"|grep -v grep
}

get_sshfs_pids() {
    get_sshfs_ps|awk '{print $2}'
}

get_lsof_pids() {
    LSOF=$(which lsof)
    lsof_pids=""
    if [ -e "${LSOF}" ];then
        lsof_pids="$(${LSOF} "${VM}" 2> /dev/null|awk '{print $2}')"
    fi
    echo $lsof_pids
}

is_mounted() {
    mounted=""
    if [ "x$(mount|awk '{print $3}'|egrep "${VM}$" |grep -v grep| wc -l|sed -e "s/ //g")" != "x0" ]\
        || [ "x$(get_sshfs_ps| wc -l|sed -e "s/ //g")" != "x0" ];then
        mounted="1"
    fi
    echo ${mounted}
}


do_umount() {
    args="-f -l"
    for arg in ${args};do
        if [ "x$(is_mounted)" != "x" ] && [ "x${noumount}" = "x" ];then
            sudo umount ${arg} "${VM}" 2>&1
        fi
    done
}

do_fusermount () {
    fuseropts="-u"
    lret=$(${FUSERMOUNT} ${fuseropts} "${VM}" 2>&1)
    # let a little time to fusermount to do his art
    sleep 2
    noumount=""
    for i in ${@};do
        if [ "x${i}" = "noumount" ];then
            noumount="1"
        fi
    done
    if [ "x$(echo "${lret}"|grep -q "not found";echo ${?})" = "x0" ] && [ "x$(is_mounted)" != "x" ];then
        if [ "x${noumount}" = "x" ];then
            do_umount
        fi
    fi
    if [ "x$(is_mounted)" != "x" ] || [ "x$(echo ${lret}|grep -q "Permission denied";echo ${?})" = "x0" ];then
        # let a little time to fusermount to do his art
        sleep 2
        sudo ${FUSERMOUNT} ${fuseropts} "${VM}" 2>&1
    fi
    if [ "x${noumount}" = "x" ];then
        do_umount
    fi
}

smartkill_() {
    PIDS=$@
    for pid in ${PIDS};do
        while [ "x$(get_pid_line ${pid}|wc -l|sed -e "s/ //g")" != "x0" ];do
            NO_INPUT="${NO_INPUT:-1}"
            if [ "x${NO_INPUT}" = "x" ] || [ "x${input}" = "xy" ];then
                log "Do you really want to kill:"
                log "$(get_pid_line ${pid})"
                log "[press y+ENTER, or CONTROL+C to abort, or ignore to continue]";read input
            fi
            if [ "x${NO_INPUT}" != "x" ] || [ "x${input}" = "xy" ];then
                log "killing ${pid}"
                kill -9 $pid
            fi
            if [ "x${input}" = "xignore" ];then
                log "ignoring ${pid}"
                break
            fi
        done
    done
}

umount_vm() {
    if [ "x$(is_mounted)" != "x" ];then
        log "Umounting of ${VM}"
        do_fusermount noumount
    fi
    if [ "x$(is_mounted)" != "x" ];then
        log "Forcing umounting of ${VM}"
        smartkill
        do_fusermount
    fi
    if [ "x${?}" != "x0" ];then
        log "Can't umount vm"
        exit "${?}"
    fi
}

mount_vm() {
    # something is wrong with the mountpath, killing it
    test_not_connected="$(LANG=C ls ${VM} 2>&1)"
    if [ ! -e "${VM}/root" ]\
        || [ "x$(echo "${test_not_connected}"|grep -q "is not connected";echo ${?})" = "x0" ];then
        umount_vm
    fi
    if [ ! -e "${VM}/root" ];then
        if [ ! -e "${VM}" ];then
            mkdir "${VM}"
        fi
        log "Mounting ${TARGET} --sshfs--> ${VM}"
        sshopts="-o transform_symlinks,reconnect,BatchMode=yes"
        sshopts="${sshopts} -o USERKNOWNHOSTSFILE=/dev/null"
        sshopts="${sshopts} -o STRICTHOSTKEYCHECKING=no"
        sshopts="${sshopts} -o PASSWORDAUTHENTICATION=no"
        sshopts="${sshopts} -o IDENTITIESONLY=yes"
        sshopts="${sshopts} -o LOGLEVEL=FATAL"
        if [ "x$(egrep "^user_allow_other" /etc/fuse.conf 2>/dev/null|wc -l|sed -e "s/ //g")" = "x0" ];then
            log "Adding allow_other to fuse"
            echo user_allow_other>>/etc/fuse.conf
        fi
        if [ "x$(egrep "^user_allow_root" /etc/fuse.conf 2>/dev/null|wc -l|sed -e "s/ //g")" = "x0" ];then
            log "Adding allow_root to fuse"
            echo user_allow_root>>/etc/fuse.conf
        fi 
        if [ "x$(egrep "^user_allow_root" /etc/fuse.conf 2>/dev/null|wc -l|sed -e "s/ //g")" != "x0" ];then
            sshopts="${sshopts},allow_other,nonempty"
        fi
        sshfs ${sshopts} "${TARGET}" "${VM}"
    fi
}

toggle_mount() {
    action=$1
    for container in $(ls /etc/lxc/auto/* 2>/dev/null);do
        if [ -e $container ];then
            name=$(basename $container)
            ip=$(egrep "lxc.network.ipv4[ ]*=" $container|head -n1|awk '{print $3}'|sed -re "s/\/.*//g")
            ccontinue="x"
            running="$(lxc-list|grep RUNNING|grep ${ip}|wc -l|sed -e "s/ //g")"
            if [ "x${running}" = "x0" ] && [ x${action} = "xmount" ];then
                log "$container is not running, not mounting"
                ccontinue=""
            fi
            if [ "x${ccontinue}" != "x" ];then
                mp="/guest/srv/lxc/${name//.conf/}"
                if [ -e "${sshfs}" ];then
                    if [ ! -e "${mp}" ];then
                        mkdir -p "${mp}"
                    fi
                    if [ -e "${mp}" ];then
                        TARGET="root@localhost:/"
                        TARGET="root@${ip}:/"
                        VM="${mp}"
                        ${action}_vm
                    fi
                fi
            fi
        fi
    done
}
if [ "x${TYPE}" != "xvagrantvm" ];then
    echo "only avalaible on devhost"
    exit 0
fi
if [ ! -e ${sshfs} ];then
    echo "You must install sshfs"
    exit 0
fi
if [ "x${1}" = "xmount" ];then
    toggle_mount mount
elif [ "x${1}" = "xumount" ];then
    toggle_mount umount
elif [ "x${1}" = "xremount" ];then
    toggle_mount umount
    toggle_mount mount
else
    echo "usage: $0 mount|umount"
fi
exit 0
# vim:set et sts=4 ts=4 tw=80:
