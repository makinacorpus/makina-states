#!/usr/bin/env bash
set -ex
cd $(dirname $0)/../..
usage() {
    set +x
    echo "Usage":
    echo "  [no_cn_setup=1] [no_controller_setup=1] [no_wait=1] [no_vm=1] [no_cn=1] [no_controller=1] vm=x cn=y controller=z create_vm.sh"
    exit 1
}
for i in $@;do
    case $i in
        -h|--help)
            usage;;
    esac
done
for i in controller vm cn vm_tmpl;do
    if [[ -z "${!i}" ]];then
        echo "Please define $i"
        usage
    fi
    echo "$i: ${!i}"
done
if [[ -z "${no_wait}" ]];then
    echo "Think to no_controller=1 no_cn=1 no_vm=1 switches"
    echo "Press any key to continue or <C-C> to interrupt within 10 sec"
    read -t 10 || true
fi
if [[ -n "${no_controller}" ]];then
    echo "Skip controller $controller step"
else
    if [[ -n "${no_controller_setup}" ]];then
        echo "Skip controller setup"
    else
        service memcached restart
        salt-call -lall state.sls makina-states.services.dns.bind
    fi
    if [[ -n "${no_sync}" ]];then
        echo "skip sync container to image"
    else
        ANSIBLE_TARGETS="$controller" bin/ansible-playbook \
            ansible/plays/cloud/snapshot_container.yml \
            -e "lxc_template=$vm_tmpl lxc_container_name=lxc$vm_tmpl"
    fi
fi
if [[ -n "${no_cn}"  ]];then
    echo "Skip cn $cn step"
else
    if [[ -n "${no_sync}" ]];then
        echo "skip sync to dest"
    else
        ANSIBLE_TARGETS="$cn" ansible-playbook ansible/plays/cloud/sync_container.yml -e "lxc_orig_host=$controller lxc_container_name=$vm_tmpl"
    fi
    if [[ -n "${no_cn_setup}" ]];then
        echo "Skip cn $cn setup"
    else
        MS_REFRESH_CACHE=y ANSIBLE_TARGETS="$cn" ansible-playbook -vvvv ansible/plays/cloud/compute_node.yml
    fi
fi
if [[ -n "${no_vm}" ]];then
    echo "Skip vm $cn setup"
else
    ANSIBLE_TARGETS="$cn,$vm" bin/ansible-playbook -vvvvv  ansible/plays/cloud/create_container.yml -e "lxc_from_container=$vm_tmpl" $vm_args_create
fi
# vim:set et sts=4 ts=4 tw=80:
