#!/usr/bin/env bash
. /etc/profile
LOG="/var/log/burpcron.log"
lock="${0}.lock"
if [ -e "${lock}" ];then
  echo "Locked ${0}";exit 1
fi
touch "${lock}"
mastersalt-call --out-file="${LOG}" --retcode-passthrough -lall \
   state.sls makina-states.services.backup.burp.server 1>/dev/null 2>/dev/null
ret="${?}"
rm -f "${lock}"
if [ "x${ret}" != "x0" ];then
  cat "${LOG}"
fi
exit "${ret}" 
# vim:set et sts=4 ts=4 tw=80:
