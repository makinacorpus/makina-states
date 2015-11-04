#!/usr/bin/env bash
{% set data = salt['mc_icinga2.settings']() %}
#/usr/bin/printf '%b' "{{data.irc.channel}} Monitoring alert"| nc -w 1 localhost 5050
/usr/bin/printf '%b' "{{data.irc.channel}} MonitoringAlert: ${HOSTDISPLAYNAME}/${HOSTADDRESS}: ${HOSTSTATE} - ${NOTIFICATIONTYPE} "| nc -w 1 localhost 5050
# vim:set et sts=4 ts=4 tw=80:
