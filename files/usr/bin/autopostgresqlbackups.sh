#!/usr/bin/env bash
if [[ -n $AUTOPGBACKUP ]];then
    set -x
fi
PGVER=9.3
PORTS=$(egrep -h "^port\s=\s" /etc/postgresql/*/*/post*.conf 2>/dev/null|awk -F= '{print $2}'|awk '{print $1}'|sort -u)
for port in $PORTS;do
    socket_path="/var/run/postgresql/.s.PGSQL.$port"
    if [[ -e "$socket_path" ]];then
        # search back from which config the port comes from
        for i in  /etc/postgresql/*/*/post*.conf;do
            if [[ "$port" == "$(egrep -h "^port\s=\s" "$i"|awk -F= '{print $2}'|awk '{print $1}')" ]];then
                # search the postgres version to export binaries
                export PGVER="$(basename $(dirname $(dirname $i)))"
                break
            fi
        done
        export PGPORT="$port"
        export PATH=/usr/lib/postgresql/$PGVER/bin:$PATH
        autopostgresqlbackup-globals.sh
        autopostgresqlbackup.sh
    fi
done
if [[ -n $AUTOPGBACKUP ]];then
    set +x
fi
# vim:set et sts=4 ts=4 tw=00:
