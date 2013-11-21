#!/usr/bin/env bash
for i in salt-master salt-minion;do
    service $i restart
done
if [[ -e /etc/mastersalt ]];then
    for i in mastersalt-master mastersalt-minion;do
        service $i restart
    done
fi
