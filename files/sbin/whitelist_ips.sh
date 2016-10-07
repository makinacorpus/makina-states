#!/usr/bin/env bash
set -xe
ip="${1}"
die(){ echo "$@" >&2 ; exit 1; }
is_container() {
    if cat -e /proc/1/cgroup 2>/dev/null|egrep -q 'docker|lxc'; then
        return 0
    else
        return 1
    fi
}
filter_host_pids() {
    pids=""
    if is_container;then
        pids="${pids} $(echo "${@}")"
    else
        for pid in ${@};do
            if ! egrep -q "/(docker|lxc)/" /proc/${pid}/cgroup 2>/dev/null;then
                pids="${pids} $(echo "${pid}")"
            fi
         done
    fi
    echo "${pids}" | sed -e "s/\(^ \+\)\|\( \+$\)//g"
}
[[ -z "${@}" ]] && die "NO IPs"
if ! hash service;then
    SERVICE_PREF_COMMAND=/etc/init.d/
else
    SERVICE_PREF_COMMAND="service "
fi
for ip in $@;do
  if [ -e /etc/fail2ban/jail.conf ];then
      if egrep -q "ignoreip = 127.0.0.1.*${ip}" /etc/fail2ban/jail.conf;then
          echo "patching ip: $ip" >&2
          sed -i -re \
            "s/ignoreip = 127.0.0.1(.*)/ignoreip = 127.0.0.1\1 $ip/g" \
            /etc/fail2ban/jail.conf
      fi
  fi
  if test $(filter_host_pids $(ps afux|grep fail2ban|grep -v grep|awk '{print $2}')|wc -w) -gt 0;then
      ${SERVICE_PREF_COMMAND}fail2ban restart
  fi
  if hash shorewall &>/dev/null;then
    shorewall allow $ip || $(which true)
  fi
  if iptables -L -n | grep DROP | grep -q $ip;then
    die "IP still banned: $ip" >&2
  fi
done
# vim:set et sts=4 ts=4 tw=80:
