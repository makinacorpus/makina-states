#!/usr/bin/env bash
set -x
ADDR="{{addr}}"
IFACE="{{ifn}}"
ip addr show dev "${IFACE}" 1>/dev/null 2>/dev/null
ret=${?}
if [ "x${ret}" = "x0" ];then
  if [ "x${ADDR}" != "x" ];then
    test "x$(ip addr show dev "${IFACE}"|egrep "inet.*${ADDR}.*scope"|wc -l|sed "s/ //g")" != "x0"
    ret=${?}
  else
    test "x$(ip addr show dev "${IFACE}"|egrep "inet.*scope"|wc -l|sed "s/ //g")" = "x0"
    ret=${?}
  fi
fi
if [ "x${ret}" = "x0" ];then
  # already configured & everything is fine
  exit 0
fi
ifdown "${IFACE}"
ifconfig "${IFACE}" down
if [ "x${ADDR}" = "x" ];then
  for cip in $(ip addr show dev "${IFACE}"|grep "inet "|awk '{print $2}');do
    ip addr del "${cip}" dev "${IFACE}"
  done
fi
ifup "${IFACE}"
ret=${?}
ifup "${IFACE}"
if [ "x${1}"  = "xnofail" ];then
  ret=0
fi
exit ${ret}
