#!/usr/bin/env bash
cd "$(dirname "${0}")"
rsync -azv ../mc_states/ mc_states/
rm -rf mc_states/tests
find mc_states -type f|while read f
do
    grep -v 'from __future' "${f}" > "${f}.tmp"
    mv -f "${f}.tmp" "${f}"
done
if [ "x${1}" != "nobuild" ];then
    make html
fi
# vim:set et sts=4 ts=4 tw=80:
