#!/usr/bin/env bash
output " [*] Cleaning vm to reduce disk space usage"
output " [*] Cleaning apt"
apt-get clean -y
apt-get autoclean -y
# cleanup archives to preserve vm SPACE
if [[ $(find /var/cache/apt/archives/ -name *deb|wc -l) != "0" ]];then
    rm -rf /var/cache/apt/archives/*deb
fi
# vim:set et sts=4 ts=4 tw=80:
