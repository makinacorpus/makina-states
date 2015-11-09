#!/usr/bin/env bash
cd src/salt
git fetch --all
git merge salt/develop
git push
for i in salt-master salt-minion mastersalt mastersalt-minion;do service $i restart;done
