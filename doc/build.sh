#!/usr/bin/env bash
cd $(dirname $0)
rsync -azv ../mc_states/ mc_states/
find mc_states -type f|while read f
do
    sed -i -re "/from __future/d" "$f"
done
if [ "x${1}" != "nobuild" ];then
    make html
fi
# vim:set et sts=4 ts=4 tw=80:
