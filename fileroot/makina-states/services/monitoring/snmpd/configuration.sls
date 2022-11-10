{% set locs = salt['mc_locations.settings']() %}
{% set sdata = salt['mc_salt.settings']() %}
{% set data = salt['mc_snmpd.settings']() %}
include:
  - makina-states.services.monitoring.snmpd.hooks
  - makina-states.services.monitoring.snmpd.services
{#- Configuration #}
{% for f in [
  '/etc/default/snmpd',
  '/etc/snmp/snmpd.conf',
  '/etc/snmp/snmp.conf',
  ] %}

snmpd-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files{{f}}
    - template: jinja
    - user: root
    - makedirs: true
    - group : root
    - mode: {{ 'default' in f and 644 or 600 }}
    - watch_in:
      - mc_proxy: snmpd-post-conf-hook
    - watch:
      - mc_proxy: snmpd-pre-conf-hook
    - defaults:
        data: |
              {{salt['mc_utils.json_dump'](data)}}
{% endfor %}
{% set m = '/usr/share/mibs' %}
{% set dodl=True %}
{% if grains['os'] in ['Debian'] %}
{% if grains["osrelease"][0] < "6" %}
{% set dodl=False %}
{% endif %}
{% endif %}

{% if dodl %}
snmpd-mibs-download:
  cmd.run:
    - name: download-mibs
    - watch_in:
      - mc_proxy: snmpd-post-conf-hook
    - watch:
      - mc_proxy: snmpd-pre-conf-hook
    - unless: >
              test -e {{m}}/iana/IANA-ADDRESS-FAMILY-NUMBERS-MIB &&
              test -e {{m}}/ietf/SONET-MIB

{% endif%}
{% if grains['os'] in ['Ubuntu'] %}
# fix missing script if any
fix-snmpd-user-packaging:
  cmd.run:
    - watch_in:
      - mc_proxy: snmpd-post-conf-hook
    - watch:
      - mc_proxy: snmpd-pre-conf-hook
    - unless: test -e /usr/bin/net-snmp-create-v3-user
    - name: >
            cp -v
            {{sdata.msr}}/files/usr/bin/net-snmp-create-v3-user
            /usr/bin/net-snmp-create-v3-user;
            chmod +x /usr/bin/net-snmp-create-v3-user
{% endif %}
snmpd-user:
  cmd.run:
    - watch:
      - mc_proxy: snmpd-pre-conf-hook
{% if grains['os'] in ['Ubuntu'] %}
      - cmd: fix-snmpd-user-packaging
{% endif %}
    - watch_in:
      - mc_proxy: snmpd-post-conf-hook
    - unless: |
             export LC_ALL="C" LANG="C"
             output=$(snmpgetnext -t 0.5 -v 3 -n "" -u "{{data.default_user}}" -a SHA -A "{{data.default_password}}" -x DES -X "{{data.default_key}}" -l authPriv localhost:161 system 2>&1)
             ret=$?
             if [ "x${ret}" = "x0" ];then
              if [ "x$(echo "${output}"|grep -q Error;echo "${?}")" = "x0" ];then
                ret=1
              fi
              if [ "x$(echo "${output}"|grep -q authorizationError;echo "${?}")" = "x0" ];then
                ret=1
              fi
              if [ "x$(echo "${output}"|grep -q denied;echo "${?}")" = "x0" ];then
                ret=1
              fi
             fi
             exit ${ret}
    - name: |
            is_lxc() {
                echo  "$(cat -e /proc/1/environ |grep container=lxc|wc -l|sed -e "s/ //g")"
            }
            filter_host_pids() {
                if [ "x$(is_lxc)" != "x0" ];then
                    echo "${@}"
                else
                    for pid in ${@};do
                        if [ "x$(grep -q lxc /proc/${pid}/cgroup 2>/dev/null;echo "${?}")" != "x0" ];then
                             echo ${pid}
                         fi
                     done
                fi
            }
            for i in $(filter_host_pids $(ps aux|grep /usr/bin/snmpd|grep -v grep|awk '{print $2}'));do kill -9 $i;done
            for i in $(filter_host_pids $(ps aux|grep /usr/sbin/snmpd|grep -v grep|awk '{print $2}'));do kill -9 $i;done
            service snmpd stop;
            net-snmp-config --create-snmpv3-user -A SHA \
              -a {{data['default_password']}} \
              -X DES -x {{data['default_key']}} {{data['default_user']}}

            service snmpd start;
