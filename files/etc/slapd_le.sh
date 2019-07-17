#!/usr/bin/env bash
set -e
# set -x
rsync -azv /home/certbot/mastersalt/live/ /etc/ssl/le/
chown -Rf openldap:openldap /etc/ssl/le/
/srv/makina-states/bin/salt-call --retcode-passthrough -lall state.sls makina-states.services.dns.slapd
systemctl restart slapd
# vim:set et sts=4 ts=4 tw=80:
