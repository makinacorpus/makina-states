#!/usr/bin/env bash
LXC_NAME="$1"
LXC_TEMPLATE="$2"
LXC_PATH="/var/lib/lxc/$LXC_NAME"
if [[ ! -d "$LXC_PATH" ]];then
    lxc-create -t $LXC_TEMPLATE  -n "$LXC_NAME"
    ret=$?
    if [[ $ret != 1 ]];then
        echo "changed=yes comment='$LXC_NAME created'"
    else
        exit $ret    
    fi
fi
