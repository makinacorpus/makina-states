#!/usr/bin/env bash
set -e

export PATH=/srv/makina-states/bin:$PATH
service memcached restart
sls() {
    ret=0
    for i in $@;do
        if ! ( salt-call --local  -lall --retcode-passthrough state.sls $i ) ;then
            echo "sls $1 failed"
            ret=1
        fi
    done
    return $ret
}
sls \
    makina-states.services.monitoring.pnp4nagios.nginx \
    makina-states.services.monitoring.icinga_web2.nginx



# vim:set et sts=4 ts=4 tw=80:
