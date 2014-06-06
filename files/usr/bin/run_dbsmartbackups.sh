#!/usr/bin/env bash
#
# Search in /etc/db_smart_backup.sh for postgresql and mysql configuration
# Run db_smart_backup.sh whenever it is applicable on those configurations
#
__NAME__="RUN_DB_SMARTBACKUPS"
if [ x"${DEBUG}" != "x" ];then
    set -x
fi
PORTS=$(egrep -h "^port\s=\s" /etc/postgresql/*/*/post*.conf 2>/dev/null|awk -F= '{print $2}'|awk '{print $1}'|sort -u)
DB_SMARTBACKUPS_CONFS="/etc/dbsmartbackup"
# try to run postgresql backup to any postgresql version if we found
# a running socket in the standard debian location
CONF="${DB_SMARTBACKUPS_CONFS}/postgresql.conf"
for port in ${PORTS};do
    socket_path="/var/run/postgresql/.s.PGSQL.$port"
    if [ -e "${socket_path}" ];then
        # search back from which config the port comes from
        for i in  /etc/postgresql/*/*/post*.conf;do
            if [ x"${port}" = x"$(egrep -h "^port\s=\s" "$i"|awk -F= '{print $2}'|awk '{print $1}')" ];then
                # search the postgres version to export binaries
                export PGVER="$(basename $(dirname $(dirname ${i})))"
                export PGVER="${PGVER:-9.3}"
                break
            fi
        done
        if [ -e "${CONF}" ];then
            export PGHOST="/var/run/postgresql"
            export HOST="${PGHOST}"
            export PGPORT="$port"
            export PORT="${PGPORT}"
            export PATH="/usr/lib/postgresql/${PGVER}/bin:${PATH}"
            echo "$__NAME__: Running backup for postgresql ${socket_path}: ${VER} (${CONF} $(which psql))"
            db_smart_backup.sh "${CONF}"
            unset PGHOST HOST PGPORT PORT
        fi
    fi
done
# try to run mysql backups if the config file is present
# and we found a mysqld process
CONF="${DB_SMARTBACKUPS_CONFS}/mysql.conf"
if [ x"$(ps aux|grep mysqld|grep -v grep|wc -l)" != "x0" ] &&  [ -e "${CONF}" ];then
    echo "$__NAME__: Running backup for mysql: $(mysql --version) (${CONF} $(which mysql))"
    db_smart_backup.sh "${CONF}"
fi
if [ x"${DEBUG}" != "x" ];then
    set +x
fi
# try to run mongodb backups if the config file is present
# and we found a mysqld process
CONF="${DB_SMARTBACKUPS_CONFS}/mongod.conf"
if [ x"$(ps aux|grep mongod|grep -v grep|wc -l)" != "x0" ] &&  [ -e "${CONF}" ];then
    echo "$__NAME__: Running backup for mongod: $(mongod --version|head -n1) (${CONF} $(which mongod))"
    db_smart_backup.sh "${CONF}"
fi
if [ x"${DEBUG}" != "x" ];then
    set +x
fi
exit 0
# vim:set et sts=4 ts=4 tw=00:
