#!/usr/bin/env bash
export DEBIAN_FRONTEND noninteractive
if [ ! -d /root/.ssh ];then mkdir -p /root/.ssh;fi
if [ ! -e /root/.ssh/authorized_keys ];then touch /root/.ssh/authorized_keys;fi
if ! which python 2>/dev/null;then
    if lsb_release -i -s | egrep -iq "ubuntu|debian";then
      apt-get update
      apt-get install -y --force-yes python
    fi
fi
# vim:set et sts=4 ts=4 tw=80:
