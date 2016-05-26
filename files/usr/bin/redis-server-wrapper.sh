#!/usr/bin/env bash
set -ex
echo $(whoami)
if [ ! -d /var/run/redis ];then 
    mkdir -p /var/run/redis
    chown redis:redis /var/run/redis
    chmod 755 /var/run/redis
fi
if [ "x$(whoami)" != "xredis" ];then
    exec su -s /bin/bash redis -c "exec /usr/bin/redis-server $@"
else
    exec /usr/bin/redis-server $@
fi
# vim:set et sts=4 ts=4 tw=80:
