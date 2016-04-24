#!/usr/bin/env bash
# cron for using to refresh salt to ansible pillar data
# like
# /etc/cron.d/refresh_ansible
# 15,30,45,00 * * * * root /srv/makina-states/_scripts/refresh_makinastates_pillar.sh

cd $(dirname "${0}")/..
if [  -f venv ]; then
    . bin/venvactivate
fi
python ansible/inventories/makinastates.py --list --refresh-cache
# vim:set et sts=4 ts=4 tw=80:
