#!/usr/bin/env bash
{% set settings = salt['mc_ssl.settings']() %}
set -eux
# fail if not existing !
cd "{{settings.config_dir}}/trust"
d="/usr/local/share/ca-certificates/ms_cloud"
if [ -e "${d}" ];then rm -rf "${d}";fi
mkdir -p "${d}"
find -name "*crt" -type f | while read i
    do
        # Debian scripts does not like filenames  with '*'
        fd=$(echo "${i}" | sed -re 's/\*/star/g')
        cp -f "${i}" "${d}/${fd}"
    done
# certificates refreshing is not very, very accurate
# Most reliable way is to use --fresh at the prize of performance cost
# we can pass --fresh to the script to force refresh
update-ca-certificates ${@}
# vim:set et sts=4 ts=4 tw=80:
