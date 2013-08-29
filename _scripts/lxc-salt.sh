#!/usr/bin/env bash
LXC_NAME="$1"
LXC_TEMPLATE="$2"
LXC_PATH="/var/lib/lxc/$LXC_NAME/rootfs"
mark="$LXC_PATH/srv/salt/makina-states/.salt-lxc-bootstrapped"
bootstrap="makina-states.services.bootstrap"
if [[ -n $2 ]];then
    bootstrap="${bootstrap}_${2}"
fi
if [[ -f $mark ]];then exit 0;fi
if [[ -d "$LXC_PATH" ]];then
    lxc-attach -n "$LXC_NAME" -- /srv/salt/makina-states/_scripts/boot-salt.sh $2 \
    && if [[ $(hostname) == "cloud-admin" ]];then
        mastersalt-key -A -y
    fi
    ret=$?
    if [[ $ret == 0 ]];then
        touch $mark
        echo "changed=yes comment='salt bootstrapped in $LXC_NAME'"
     else
        echo "there were errors bootstrapping salt !!!"
        exit $ret
    fi
fi
# vim:set et sts=4 ts=4 tw=80:
