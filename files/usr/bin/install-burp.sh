#!/usr/bin/env bash
cd $(dirname $0)
build_uthash=""
configure_opts=""
if [ "x$(cat /etc/debian_version 2>/dev/null)" = "x5.0.3" ];then
    PATH="/var/makina/minitage/dependencies/git-1.7/parts/part/bin:$PATH"
    build_uthash="y"
    configure_opts="$configure_opts --disable-acl"
fi
apt-get install -y --force-yes librsync-dev libz-dev libssl-dev libacl1-dev
if [ ! -e burp/README ];then
    rm -rf burp
    git clone https://github.com/grke/burp.git
fi
cd burp
git reset --hard remotes/origin/1.3.48
if [ "x$build_uthash" != "x" ];then
    if [ "x$(dpkg -l uthash-dev|grep "1.9.7-1"|wc -l|sed -e "s/ //g")" = "x0" ];then
        wget http://ftp.us.debian.org/debian/pool/main/u/uthash/uthash-dev_1.9.7-1_all.deb
        dpkg -i uthash-dev_1.9.7-1_all.deb
    fi
else
   apt-get install uthash-dev
fi
./configure $configure_opts && make && make install
if [ ! -e /etc/burp ];then
    mkdir /etc/burp
fi
