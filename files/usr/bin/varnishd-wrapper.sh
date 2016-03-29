#!/usr/bin/env bash
# MANAGED by salt, DO NOT EDIT
# varnish systemd configuration is quite broken, as /usr/share/varnish/reload-vcl
# needs to share settings from /etc/default/varnish, but this file ${DAEMON_OPTS}
# is not well reused on init script. Using a real bash wrapper we get it working
. /etc/default/varnish
/usr/sbin/varnishd ${DAEMON_OPTS} -f /etc/varnish/default.vcl
# vim:set et sts=4 ts=4 tw=80:
