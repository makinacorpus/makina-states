#!/usr/bin/env bash
set -x
cluster_code_sync() {
    # code sync
    mastersalt '*' cmd.run "boot-salt.sh --synchronize-code"
    exit 0
    mastersalt '*' "saltutil.sync_all"
    mastersalt '*' "saltutil.refresh_pillar"
    mastersalt '*' "cmd.run" "boot-salt.sh -C -S --only-buildout-rebootstrap"

    if [ "x${SALT_BOOT_NOCONFIRM}" = "x" ];then
        echo "OK or C-C";read
        echo "really OK or C-C";read
        echo "really really OK or C-C";read
    fi

    # restart services
    service mastersalt-master restart
    sleep 10
    mastersalt '*' cmd.run "service mastersalt-minion restart"


    mastersalt '*' cmd.run "service salt-master restart"
    sleep 7
    mastersalt '*' cmd.run "service salt-minion restart"
    mastersalt '*' cmd.run "salt-call saltutil.sync_all"
    mastersalt '*' cmd.run "salt-call saltutil.refresh_pillar"
}

cluster_code_upgrade() {
    # core local upgrade
    # up nodetypes + localsettings + controllers from mastersalt
    mastersalt '*' state.sls "makina-states.controllers"
}

if [ "x${SALT_BOOT_AS_FUNCS}" = "x" ];then
    cluster_code_sync
    cluster_code_upgrade
fi
