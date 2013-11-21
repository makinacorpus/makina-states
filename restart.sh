#!/usr/bin/env bash
for i in salt-master salt-minion;do
    service $i stop
    sleep 1
    service $i start
done
if [[ -e /etc/mastersalt ]];then
    for i in mastersalt-master mastersalt-minion;do
        service $i stop
        sleep 1
        service $i start
    done
fi
