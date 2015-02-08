#!/usr/bin/env bash
{% set settings = salt['mc_burp.settings']() %}
{% set ssdata = settings.server_conf %}
{% if client != 'server_conf' %}{% set settings=settings['clients']%}{%endif%}
{% set data=settings[client] %}
{% set cdata=data %}
if test -e /etc/burp/CA/.{{client}}done;then exit 0;fi
if test -e /etc/burp/CA/{{cdata.cname}}.crt;then exit 0;fi
burp_ca --key --request --name {{cdata.cname}} &&\
    burp_ca --days 365000 --batch --sign --ca {{ssdata.ca_name}} --name {{cdata.cname}} &&\
    touch /etc/burp/CA/.{{client}}done
ret=${?}
rm -f /tmp/burpclient{{client}}cagen.sh
exit ${ret}
# vim:set et sts=4 ts=4 tw=0:
