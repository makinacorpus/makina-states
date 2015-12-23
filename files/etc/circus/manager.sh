#!/usr/bin/env bash
set -e
CIRCUS_REGISTER_TEMPO=${CIRCUS_REGISTER_TEMPO:-30}
CIRCUS_START_TEMPO=${CIRCUS_START_TEMPO:-60}
CIRCUS_STOP_TEMPO=${CIRCUS_START_TEMPO:-30}

is_container() {
    cat -e /proc/1/environ 2>/dev/null|grep -q container=
    echo "${?}"
}

filter_host_pids() {
    pids=""
    if [ "x$(is_container)" = "x0" ];then
        pids="${pids} $(echo "${@}")"
    else
        for pid in ${@};do
            if [ "x$(grep -q /lxc/ /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ];then
                pids="${pids} $(echo "${pid}")"
            fi
         done
    fi
    echo "${pids}" | sed -e "s/\(^ \+\)\|\( \+$\)//g"
}

daemon_pids() {
    filter_host_pids $(\
        ps aux|egrep "bin/circusd|circusweb|from circus import import stats" \
        | egrep -v 'grep|vim' | grep -v circusctl | awk '{print $2}')
}

is_running() {
    pids=$(daemon_pids)
    if [ "x$(echo ${pids}|wc -w|sed -e "s/  //g")" != "x0" ];then
        return 0
    fi
    return 1
}

register_watcher() {
    if ! circusctl status|egrep -q "^$CIRCUS_WATCHER:";then
        echo "$CIRCUS_WATCHER not registered, try to reload cfg"
        for i in $(seq 10);do
            if circusctl reloadconfig;then
                break
            else
                sleep 1
            fi
        done
        for i in $(seq $CIRCUS_REGISTER_TEMPO);do
            if circusctl status|egrep -q "^$CIRCUS_WATCHER:";then
                echo "$CIRCUS_WATCHER is now registered"
                break
            fi
            echo "$CIRCUS_WATCHER is not yet registered ($i/30s)"
            sleep 1
        done
        if ! circusctl status|egrep -q "^$CIRCUS_WATCHER:";then
            echo "$CIRCUS_WATCHER is not registered"
            return 150
        fi
    fi
}

retry_stop() {
    for i in $(seq $CIRCUS_STOP_TEMPO);do
        ret=$(circusctl stop $@)
        if [ "x${ret}" = "xok" ];then
            echo "stopped $CIRCUS_WATCHER"
            return 0
        else
            echo "circus return $ret" >&2
        fi
        echo "retry to stop $@ $i/$CIRCUS_STOP_TEMPO"
        sleep 1
    done
    echo "Impossible to stop $@ in $i sec"
    return 130
}

retry_reload() {
    for i in $(seq $CIRCUS_START_TEMPO);do
        ret=$(circusctl reload $@)
        if [ "x${ret}" = "xok" ];then
            echo "reloaded $CIRCUS_WATCHER"
            return 0
        else
            echo "circus return $ret" >&2
        fi
        echo "retry to reload $@ $i/$CIRCUS_START_TEMPO"
        sleep 1
    done
    echo "Impossible to reload $@ in $i sec"
    return 130
}

retry_restart() {
    for i in $(seq $CIRCUS_START_TEMPO);do
        ret=$(circusctl restart $@)
        if [ "x${ret}" = "xok" ];then
            echo "restarted $CIRCUS_WATCHER"
            return 0
        else
            echo "circus return $ret" >&2
        fi
        echo "retry to restart $@ $i/$CIRCUS_START_TEMPO"
        sleep 1
    done
    echo "Impossible to restart $@ in $i sec"
    return 130
}

retry_start() {
    for i in $(seq $CIRCUS_START_TEMPO);do
        ret=$(circusctl start $@)
        if [ "x${ret}" = "xok" ];then
            echo "started $CIRCUS_WATCHER"
            return 0
        else
            echo "circus return $ret" >&2
        fi
        echo "retry to start $@ $i/$CIRCUS_START_TEMPO"
        sleep 1
    done
    echo "Impossible to start $@ in $i sec"
    return 130
}

start_watcher() {
    retry_start $CIRCUS_WATCHER
}

restart_watcher() {
    retry_restart $CIRCUS_WATCHER
}

stop_watcher() {
    retry_stop $CIRCUS_WATCHER
}

reload_watcher() {
    retry_reload $CIRCUS_WATCHER
}

retry_circusctl() {
    for i in $(seq ${circus_retries:-10});do
        if true;then
            echo
            break
        fi
    done
}
check_running() {
    if [ "x${CIRCUS_WATCHER}" = "x" ];then
        echo "Please export \$CIRCUS_WATCHER to act on"
        exit 130
    fi
    if ! is_running;then
        echo "circus is not running"
        exit 140
    fi
}

main() {
    local action="${1}"
    check_running
    register_watcher
    ${action}_watcher
}

case $1 in
    start|stop|reload|restart|register)
        main ${1}
        exit ${?}
        ;;
    *)
        echo "$0 start|restart|stop|reload|register"
        exit 1
        ;;
esac
# vim:set et sts=4 ts=4 tw=0:
