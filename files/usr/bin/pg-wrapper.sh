#!/usr/bin/env bash
bin="$1"
binary="$(which $bin 2>/dev/null)"
version={{version}}
die() {
    echo $@
    exit 1
}
# get pgsql pid
pid=$(ps aux|grep "$version/bin/postgres"|grep -v grep|awk '{print $2}')
if [[ -z $pid ]];then
    die "$version: invalid pid"
fi
# from the pid, get the running port
socket_port=$(netstat -pnlt 2>/dev/null|grep $pid|grep -v tcp6|awk '{print $4}'|awk -F: '{print $2}')
if [[ -z $socket_port ]];then
    die "$version: invalid socket port"
fi
socket_path=/var/run/postgresql/.s.PGSQL.$socket_port
if [[ ! -e "$binary" ]];then
    die "$version: invalid binary: $bin"
fi
if [[ ! -e "$socket_path" ]];then
    die "$version: invalid socket path: $socket_path"
fi
export PGHOST="/var/run/postgresql"
export PGPORT="$socket_port"
shift
export PATH=/usr/lib/postgresql/$version/bin:$PATH
exec $binary $@
