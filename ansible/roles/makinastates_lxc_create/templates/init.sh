#!/usr/bin/env bash
export DEBIAN_FRONTEND noninteractive
if [ ! -d /root/.ssh ];then mkdir -p /root/.ssh;fi
if [ ! -e /root/.ssh/authorized_keys ];then touch /root/.ssh/authorized_keys;fi
retry() {
    tries=$1
    step=$2
    shift;shift
    while true;do
        "${@}"
        ret=$?
        if [ "x${ret}" = "x0" ];then
            break
        else
            sleep $step
            tries=$(($tries -1))
            if [[ ${tries} -lt 0 ]];then
                break
            fi
        fi
    done
    return $ret
}
retry 15 1 ping -q -W 4 -c 1 8.8.8.8
if ! which python >/dev/null 2>/dev/null;then
    if lsb_release -i -s | egrep -iq "ubuntu|debian";then
      retry 15 1 apt-get update
      retry 15 1 apt-get install -y --force-yes python
    fi
fi
# vim:set et sts=4 ts=4 tw=80:
