#!/usr/bin/env bash
{% set data = salt['mc_burp.settings']() %}
set -e
to_delete=""
managed="{% for c in data.clients%}{{c}} {%endfor%}"
cd /etc/burp/clients
for i in $(find -mindepth 1 -maxdepth 1 -type d|sed "s/.\///g");do
  found=""
  for client in ${managed};do
    if [ "x${client}" = "x${i}" ];then
      found="1"
      break
    fi
  done
  if [ "x${found}" = "x" ];then
    to_delete="${i} ${to_delete}"
  fi
done
for i in ${to_delete};do
   rm -rf "$i"
done
cd /etc/burp/clientconfdir
for i in $(find -mindepth 1 -maxdepth 1 -type d|sed "s/.\///g");do
  found=""
  for client in ${managed};do
    if [ "x${client}" = "x${i}" ] || [ "x${i}" = "xincexc" ];then
      found="1"
      break
    fi
  done
  if [ "x${found}" = "x" ];then
    to_delete="${i} ${to_delete}"
  fi
done
ret=0
for i in ${to_delete};do
  rm -rvf "$i"
  if [ "x${?}" != "x0" ];then
    ret=1
  fi
done
exit ${ret}
# vim:set et sts=4 ts=4 tw=80:
