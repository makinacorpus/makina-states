#!/usr/bin/env bash
{% if grains.get('os_family', '') in ['Debian'] %}
    if [[ $1 == "fromsalt" ]];then 
        shorewall -qqqqqq restart  > /dev/null
    else
        shorewall -qqqqqq restart
    fi
{% endif %}
if [[ $1 == "fromsalt" ]];then 
    echo 'changed="yes" comment="firewall started"'
fi
exit $?
# vim:set et sts=4 ts=4 tw=80:
