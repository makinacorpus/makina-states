#!/usr/bin/env bash
set -ex
DAEMON=${DAEMON:-/usr/bin/redis-server}
if [ ! -d /var/run/redis ];then
    mkdir -p /var/run/redis
fi
chown redis:redis /var/run/redis
chmod 755 /var/run/redis
if [ "x$(whoami)" != "xredis" ];then
    exec su -s /bin/bash redis -c "exec $DAEMON $@"
else
    exec "$DAEMON" $@
fi
# vim:set et sts=4 ts=4 tw=80:
