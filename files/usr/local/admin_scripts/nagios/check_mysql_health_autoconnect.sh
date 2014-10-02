#!/usr/bin/env bash
# wrapper to the mysql_check_health nagios probe
# autoconnect as a mysql administrator on debian based system
# default mode is connection time
set -e
if [ "x${SH_DEBUG}" = "x1" ];then
    set -x
fi
LOCK="${TMPLOCK:-"/tmp/mysqlautoconnect.lock"}"
# wait for a lock to diseappear 
# but autodelete this lock when it is
# older than 1 minute
while /bin/true;do
    if [ -e "${LOCK}" ];then
        find "$LOCK" -mmin +1 -print 2>/dev/null|while read i;do
            rm -f "${LOCK}"
        done
    else
        break
    fi
done
if [ ! -e "${LOCK}" ];then
    # we can acquire the lock
    touch "${LOCK}"
else
    # should not happen
    echo ${LOCKED}
    exit 255
fi
cd "$(dirname $0)"
CONFDIR="${CONFDIR:-/etc/mysql}"
CNF="${CNF:-"${CONFDIR}/debian.cnf"}"
if [ -e  $CBF ];then
    if [ "x$(echo "${@}"|grep -q -- --hostname;echo $?)" != "x0" ];then
        ARGS="$ARGS --hostname ${MYSQL_HOST:-$(grep host $CNF|head -n1|awk '{print $3}')}"
    fi
    if [ "x$(echo "${@}"|grep -q -- --socket;echo $?)" != "x0" ];then
        ARGS="$ARGS --socket ${MYSQL_SOCKET:-$(grep socket $CNF|head -n1|awk '{print $3}')}"
    fi
    if [ "x$(echo "${@}"|grep -q -- --username;echo $?)" != "x0" ];then
        ARGS="$ARGS --username ${MYSQL_USER:-$(grep user $CNF|head -n1|awk '{print $3}')}"
    fi
    if [ "x$(echo "${@}"|grep -q -- --password;echo $?)" != "x0" ];then
        ARGS="$ARGS --password ${MYSQL_PASSWORD:-$(grep password $CNF|head -n1|awk '{print $3}')}"
    fi
fi
if [ "x$(echo "${@}"|grep -q -- --mode;echo $?)" != "x0" ];then
    ARGS="$ARGS --mode ${MODE:-"connection-time"}"
fi
./check_mysql_health $ARGS "${@}"
ret=${?}
rm -f "${LOCK}"
exit ${ret}
