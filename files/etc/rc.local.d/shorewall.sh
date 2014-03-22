#!/usr/bin/env bash
# do not return error code not to mess upstart 
{% if grains.get('os_family', '') in ['Debian'] %}
    if [[ "x${1}" = "xfromsalt" ]];then 
        shorewall -qqqqqq restart  > /dev/null
        ret="${?}"
    else
        shorewall -qqqqqq restart
        ret="${?}"
    fi
{% endif %}
if [ "x${1}" = "xfromsalt" ];then 
    if [ "${ret}" = "x0" ];then
        echo 'changed="yes" comment="firewall started"'
    else
        exit ${ret}
    fi
fi
/bin/true
exit 0
# vim:set et sts=4 ts=4 tw=80:
