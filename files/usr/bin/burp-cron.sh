#!/usr/bin/env bash
. /etc/profile
cd $(dirname ${0})
{% set p = salt['mc_locations.msr']() %}
cd "{{p}}"
LOG="/var/log/burpcron.log"
lock="${0}.lock"
find "${lock}" -type f -mmin +15 -delete 1>/dev/null 2>&1
if [ -e "${lock}" ];then
  echo "Locked ${0}";exit 1
fi
touch "${lock}"
bin/salt-call --out-file="${LOG}" --retcode-passthrough -lall \
   state.sls makina-states.services.backup.burp.server 1>/dev/null 2>/dev/null
ret="${?}"
rm -f "${lock}"
if [ "x${ret}" != "x0" ];then
  cat "${LOG}"
fi
exit "${ret}" 
# vim:set et sts=4 ts=4 tw=80:
