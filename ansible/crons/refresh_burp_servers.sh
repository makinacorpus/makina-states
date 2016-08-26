#!/usr/bin/env bash
# this can be used:
# - as a wrapper to test the inventory
# - as a cron for using to refresh the whole salt infra  to ansible pillar data
#   # /etc/cron.d/refresh_ansible
#   15,30,45,00 * * * * root /srv/makina-states/_scripts/refresh_makinastates_pillar.sh
cd $(dirname "$(readlink -f "${0}")")/../..
if [  -f venv ]; then
    . venv/bin/activate
fi
bn=$(basename $0)
lock="$(pwd)/var/ansible/${bn}.lock"
log="$(pwd)/var/ansible/${bn}.log"
find "${lock}" -type f -mmin +30 -delete 1>/dev/null 2>&1
if [ "x${NO_LOCK-}" = "x" ];then
    if  [ -e "${lock}" ];then
        echo "Locked ${0} ($lock)";exit 1
    fi
    touch "${lock}"
fi
if [[ -n ${ANSIBLE_TARGETS-} ]];then
    export ANSIBLE_TARGETS="${ANSIBLE_TARGETS-}"
fi
export MS_REFRESH_CACHE="${MS_REFRESH_CACHE-y}"
args=${@:-"--list"}
ANSIBLE_TARGETS="burp_servers" bin/ansible-playbook -vvvvv ansible/plays/makinastates/pillar.yml 1>$log 2>&1
ret=${?}
if [ "x${ret}" != "x0" ];then
  cat "${log}"
fi
if [ "x${NO_LOCK-}" = "x" ];then
    rm -f "${lock}"
fi
# vim:set et sts=4 ts=4 tw=80:
