#!/usr/bin/env bash
# start a container and wait for eth0 ip to be available
set -ex
action=$1
container="{{lxc_container_name}}"
mainif=eth0
lxcp=$(echo $(dirname $(dirname $(readlink -f $0))))
case $action in
    stop|restart)
        if lxc-ls --fancy|egrep "^$container "|awk '{print $2}'\
            |grep -qi running;then
            lxc-stop -P "$lxcp" -k -n "$container"
        fi
    ;;
esac
case $action in
    start|restart)
        if ! lxc-ls --fancy|egrep "^$container "|awk '{print $2}'\
            |grep -qi running;then
            lxc-start -P "$lxcp" -d -n "$container"
            ret=$?
        else
            ret=0
        fi
        if [ "x${ret}" != "x0" ];then
            echo "cant start $container"
            exit 1
        fi
        ip=""
        for i in $(seq 60);do
            if [ "x${ip}" != "x" ];then
                break
            fi
            ip=$(lxc-attach -P "$lxcp" -n $container -- \
                 ip addr show $mainif|grep inet|grep -v : \
                 |awk '{print $2}'|sed "s|/.*||g")
            if [ "x${ip}" = "x" ];then
                sleep 1
            fi
        done
        if [ "${ip}" = "x" ];then
            echo "cant get ip of $container"
            exit 1
        else
            echo "container ip: $ip"
        fi
    ;;
esac
# vim:set et sts=4 ts=4 tw=80:
