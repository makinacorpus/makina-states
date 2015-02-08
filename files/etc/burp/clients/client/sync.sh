#!/usr/bin/env bash
{% set settings = salt['mc_burp.settings']() %}
{% if client != 'server_conf' %}{% set settings=settings['clients']%}{%endif%}
{% set data=settings[client] %}
echo "Syncing {{client}}"
{% for dir in ['burp', 'default', 'init.d', 'cron.d'] -%}rsync -azv -e '{{cdata['rsh_cmd']}}' /etc/burp/clients/{{client}}/etc/{{dir}}/ {{cdata['rsh_dst']}}:/etc/{{dir}}/ &&\
{% endfor -%}
/bin/true
{% if not cdata.activated -%}
{{cdata['ssh_cmd']}} rm -f /etc/cron.d/burp
{% endif %}
exit ${?}
# vim:set et sts=4 ts=4 tw=80:
