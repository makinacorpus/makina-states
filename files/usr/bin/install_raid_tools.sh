#!/usr/bin/env bash
RELEASE="wheezy"
if [ "x$(lsb_release --id 2>/dev/null|grep -q Ubuntu;echo $?)" = "x0" ];then
    RELEASE="precise"
fi
install_debian() {
    if [ "x$(grep -q "hwraid.le-vert.net" $(find /etc/apt/sources.list* -type f);echo ${?})" = "x0" ];then
        if [ ! -e /etc/apt/sources.list.d/ ];then
            mkfir /etc/apt/sources.list.d/
        fi
        echo "deb http://hwraid.le-vert.net/debian ${RELEASE} main" >> /etc/apt/sources.list/hwraid.list
    fi
    wget -O - http://hwraid.le-vert.net/debian/hwraid.le-vert.net.gpg.key | sudo apt-key add -
}

if test -e /etc/debian_version;then
    install_debian
fi
