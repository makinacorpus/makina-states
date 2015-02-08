#!/usr/bin/env bash
set -e
cd /etc/ssl/cloud/separate/
d="/usr/local/share/ca-certificates/ms_cloud"
if [ -e "${d}" ];then rm -rf "${d}";fi
mkdir -p "${d}"
find -name "*bundle.crt"\
  | grep -v -- "-full.crt"\
  | grep -v -- ".full.crt"\
  | grep -v -- "-auth.crt"\
  | grep -v -- ".auth.crt"\
  | grep -v -- "-authr.crt"\
  | grep -v -- ".authr.crt"\
  | while read i
do
  #fd="${i}"
  fd=$(echo "${i}" | sed -re 's/\*/star/g')
  cp "${i}" "${d}/${fd}"
done
update-ca-certificates --fresh 
rm -f "{{f}}"
# vim:set et sts=4 ts=4 tw=80:
