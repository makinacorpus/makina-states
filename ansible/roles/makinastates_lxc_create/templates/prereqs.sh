#!/usr/bin/env bash
set -ex
cd $(dirname $0)
lxcp=$(echo $(dirname $(dirname $(readlink -f $0))))
if [ -e reset-host.py ];then
    cat reset-host.py| lxc-attach -P "$lxcp" -n {{lxc_container_name}} -- \
        tee /usr/bin/reset-host.py
fi
cat init.sh | lxc-attach -P "${lxcp}" -n {{lxc_container_name}} -- tee /tmp/init.sh
lxc-attach -P "${lxcp}" -n {{lxc_container_name}} -- bash /tmp/init.sh
cat /tmp/ansible_master.pub | \
    lxc-attach -P "${lxcp}" -n {{lxc_container_name}} -- tee -a /root/.ssh/authorized_keys
# vim:set et sts=4 ts=4 tw=80:
