#!/usr/bin/env bash
kind="${1}"
shift
MASTERSALT_MS="${MASTERSALT_MS:-/srv/mastersalt/makina-states}"
MS="${MS:-/srv/salt/makina-states}"
SC=""
for p in "${MASTERSALT_MS}" "${MS}";do
    i="${p}/_scripts/boot-salt.sh"
    if [ -e "${i}" ];then
        SC="${i}"
        break
    fi
done
if [ ! -e ${SC} ];then
    exit 1
fi
export SALT_BOOT_AS_FUNCS="y"
. "${SC}"
setup
func=do_pip
if [ "x${kind}" = "xmastersalt" ];then
    func="do_mastersalt_pip"
fi
ret=$(${func})
if [ "x${ret}" != "x" ];then
    exit 1
fi
# vim:set et sts=4 ts=4 tw=80:
