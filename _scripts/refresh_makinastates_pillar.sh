#!/usr/bin/env bash
cd $(dirname "${0}")/..
if [  -f venv ]; then
    . bin/venvactivate
fi
python mc_states/ansible/inventory.py --list --refresh-cache
# vim:set et sts=4 ts=4 tw=80:
