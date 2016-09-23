#!/usr/bin/env bash
set -ex
echo "cn: $cn"
echo "vm: $vm"
echo "vm_tmpl: $vm_tmpl"
MS_REFRESH_CACHE=y ANSIBLE_TARGETS="$cn" ansible-playbook -vvvv ansible/plays/cloud/compute_node.yml
ANSIBLE_TARGETS="$cn,$vm" bin/ansible-playbook -vvvvv  ansible/plays/cloud/create_container.yml -e "lxc_from_container=$vm_tmpl"
# vim:set et sts=4 ts=4 tw=80:
