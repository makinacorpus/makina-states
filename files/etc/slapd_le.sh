#!/usr/bin/env bash
set -e
# set -x
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games
rsync -azv /home/certbot/mastersalt/live/ /etc/ssl/le/
chown -Rf openldap:openldap /etc/ssl/le/
if [[ -z ${NO_RECONFIGURE-} ]];then
    /srv/makina-states/bin/salt-call --retcode-passthrough -lall state.sls makina-states.services.dns.slapd
    if ( which systemctl &>/dev/null );then
        systemctl restart slapd
    else
        service slapd restart
    fi
fi
# vim:set et sts=4 ts=4 tw=80:
