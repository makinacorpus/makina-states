#!/usr/bin/env bash
BURPDIR="${BURPDIR:-/data/burp}"
KEEPCOUNT=${KEEPCOUNT:-1}
cleanup_backup() {
    bdir="${1}"
    cd "${bdir}"
    if [ -f .todelete ] ;then
        find "${bdir}" -type d -mindepth 1 -maxdepth 1  -printf "%T@  %p\n" |grep -v /current|sort -n|awk '{print $2}' > .todelete
        exit 1
        cat .todelete|while read f;do 
            echo "echo ${f}"
            echo rm -rf "${f}"}
        done
        rm -f .todelete
    fi  
}
if [ "x${@}" = "x" ];then
    echo "give ids to delete"
    exit 1
fi
if [ ! -d "${BURPDIR}" ];then
    echo "no $BURPDIR"
    exit 1
fi
for i in "${@}";do
    backup="${BURPDIR}/${i}"
    if [ ! -d "${backup}" ];then 
        echo "no $i"
    else
        cleanup_backup "${backup}"
    fi 
done
# vim:set et sts=4 ts=4 tw=80:
