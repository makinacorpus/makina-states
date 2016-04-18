#!/usr/bin/env bash
set -ex
cd $(dirname $0)
cat init.sh | lxc-attach -n {{lxc_container_name}} -- tee /tmp/init.sh
lxc-attach -n {{lxc_container_name}} -- bash /tmp/init.sh
cat /tmp/ansible_master.pub | \
    lxc-attach -n {{lxc_container_name}} -- tee -a /root/.ssh/authorized_keys
# vim:set et sts=4 ts=4 tw=80:
