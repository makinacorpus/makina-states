#!/usr/bin/env bash
YELLOW='\e[1;33m'
RED="\\033[31m"
CYAN="\\033[36m"
NORMAL="\\033[0m"
DEBUG=${BOOT_SALT_DEBUG:-}
output() { echo -e "${YELLOW}$@${NORMAL}" >&2; }
output " [*] Cleaning vm to reduce disk space usage"
output " [*] Cleaning apt"
apt-get clean -y
apt-get autoclean -y
# cleanup archives to preserve vm SPACE
if [[ $(find /var/cache/apt/archives/ -name *deb|wc -l) != "0" ]];then
    rm -rf /var/cache/apt/archives/*deb
fi
# vim:set et sts=4 ts=4 tw=80:
