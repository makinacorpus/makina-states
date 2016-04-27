#!/usr/bin/env bash
# this can be used:
# - as a wrapper to test the inventory
# - as a cron for using to refresh the whole salt infra  to ansible pillar data
#   # /etc/cron.d/refresh_ansible
#   15,30,45,00 * * * * root /srv/makina-states/_scripts/refresh_makinastates_pillar.sh
cd $(dirname "${0}")/..
if [  -f venv ]; then
    . bin/venvactivate
fi
if [[ -n ${ANSIBLE_TARGETS-} ]];then
    export ANSIBLE_TARGETS="${ANSIBLE_TARGETS-}"
fi
args=${@:-"--list --refresh-cache"} 
python ansible/inventories/makinastates.py $args
# vim:set et sts=4 ts=4 tw=80:
