#!/usr/bin/env bash
{% set data = salt['mc_supervisor.settings']() %}
. /etc/profile || /bin/true
export TMPDIR=/tmp
. {{ data.venv }}/bin/activate
exec su -c '{{ data.venv }}/bin/supervisord -c "{{data.conf}}" --nodaemon' 
# vim:set et sts=4 ts=4 tw=80:
