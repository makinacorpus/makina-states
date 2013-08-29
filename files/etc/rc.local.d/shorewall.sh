#!/usr/bin/env bash
{% if grains.get('os_family', '') in ['Debian'] %}
    /etc/init.d/shorewall start
{% endif %}
exit $?
# vim:set et sts=4 ts=4 tw=80:
