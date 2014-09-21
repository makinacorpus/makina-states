#!/usr/bin/env bash
set -e
set -x
VER="${BURP_VER:-"1.3.48"}"
cd $HOME
if [ ! -d burp ];then
    git clone https://github.com/grke/burp.git
fi
cd burp
git reset --hard remotes/origin/$VER
apt-get install -y build-essential  librsync-dev libz-dev libssl-dev uthash-dev libacl1-dev libncurses5-dev
./configure  && make && make install
