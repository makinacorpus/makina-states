#!/usr/bin/env bash
{% set data = salt['mc_burp.settings']() %}
{% set ssdata = data.server_conf %}
if [ ! -e /etc/burp/CA/.done ];then
    rm -rf /etc/burp/CA &&\
        if [ ! -e /etc/burp ]
        then
            mkdir -p /etc/burp
        fi &&\
            burp_ca --dhfile {{ssdata.ssl_dhfile}} &&\
            burp_ca --ca_days 365000 -D 365000 -i --ca {{ssdata.ca_name}} &&\
            burp_ca --key --request --name {{ssdata.fqdn}} &&\
            burp_ca --days 365000 \
            --batch --sign --ca {{ssdata.ca_name}} --name {{ssdata.fqdn}} \
            touch /etc/burp/CA/.done
fi
rm -f /tmp/burpcagen.sh
# vim:set et sts=4 ts=4 tw=80:
