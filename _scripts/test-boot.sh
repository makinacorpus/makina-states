#!/usr/bin/env bash
D=$(dirname $0)
rm -vrf /etc/*salt* /etc/*/*salt* /srv/*pillar* /srv/salt/top.sls
ps aux|grep salt|awk '{print $2}'|xargs kill -9
export SALT_BOOT_NOCONFIRM=1 SALT_BOOT_SKIP_CHECKOUTS=1
$D/boot-salt.sh
#eboot=${1:-makina-states.bootstrap.server}
#boot=${2:-makina-states.bootstrap.salt_master}
#args="-lall -m "/srv/salt/_modules" -m "/srv/salt/makina-states/_modules" --local state.sls"
#bin="/srv/salt/makina-states/bin/salt-call"
#$bin $args $eboot && $bin $args $boot
