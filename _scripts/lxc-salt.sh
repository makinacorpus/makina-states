#!/usr/bin/env bash
export LXC_NAME="$1"
export SALT_BOOT="$2"
LXC_PATH="/var/lib/lxc/$LXC_NAME/rootfs"
MASTERSALT_DEFAULT="mastersalt.makina-corpus.net"
if [[ "$SALT_BOOT" == "mastersalt" ]];then
    export SALT_BOOT=server
    export MASTERSALT_BOOT=minion
    export MASTERSALT="${MASTERSALT:-$MASTERSALT_DEFAULT}"
fi
export MASTERSALT="$MASTERSALT"
export MAKINA_STATES_NOCONFIRM="1"
mark="$LXC_PATH/srv/salt/makina-states/.salt-lxc-bootstrapped"
if [[ -f $mark ]];then exit 0;fi
if [[ -d "$LXC_PATH" ]];then
    lxc-attach -n "$LXC_NAME" --keep-env -- /srv/salt/makina-states/_scripts/boot-salt.sh
    bootret=$?
    if [[ $bootret != 0 ]];then
        echo "Failed LXC SALT bootstrap for $LXC_NAME"
        exit $bootret
    fi
    if [[ $(hostname) == "cloud-admin" ]];then
        mastersalt-key -A -y
        ret=$?
        if [[ $ret != 0 ]];then
            echo "Failed LXC Mastersalt  key communication for $LXC_NAME"
            exit $ret
        fi
    fi
    if [[ $bootret == 0 ]];then
        touch $mark
        echo "changed=yes comment='salt bootstrapped in $LXC_NAME'"
    fi
fi
# vim:set et sts=4 ts=4 tw=80:
