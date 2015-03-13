#!/usr/bin/env bash
cd $(dirname $0)
rsync -azv ../mc_states/ mc_states/
find mc_states -type f|while read f
do
    sed -i -re "/from __future/d" "$f"
done
# vim:set et sts=4 ts=4 tw=80:
