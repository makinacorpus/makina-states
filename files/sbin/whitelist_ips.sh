#!/usr/bin/env bash
set -xe
ip="${1}"
die(){ echo "$@" >&2 ; exit 1; }
[[ -z "${@}" ]] && die "NO IPs"
for ip in $@;do
  if [ -e /etc/fail2ban/jail.conf ];then
      if egrep -q "ignoreip = 127.0.0.1.*${ip}" /etc/fail2ban/jail.conf;then
          echo "patching ip: $ip" >&2
          sed -i -re \
            "s/ignoreip = 127.0.0.1(.*)/ignoreip = 127.0.0.1\1 $ip/g" \
            /etc/fail2ban/jail.conf
      fi
  fi
  if [ -e /etc/init.d/fail2ban ];then
      /etc/init.d/fail2ban restart
  fi
  if hash shorewall &>/dev/null;then
    shorewall allow $ip || $(which true)
  fi
  if iptables -L -n | grep DROP | grep -q $ip;then
    die "IP still banned: $ip" >&2
  fi
done
# vim:set et sts=4 ts=4 tw=80:
