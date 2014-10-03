#!/usr/bin/env bash
# wrapper to be sure to exec in C locale
export PATH="/usr/lib/nagios/plugins:${PATH}"
export LANG=C LC_ALL=C
bin=check_http
for i in /usr/lib/nagios/plugins;do
    if [ -e "${i}/check_http" ];then
        bin="${i}/check_http"
        break
    fi
done
exec "${bin}" "${@}"
exit ${?}
