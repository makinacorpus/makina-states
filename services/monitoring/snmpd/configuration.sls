{% set locs = salt['mc_locations.settings']() %}
{% set sdata = salt['mc_salt.settings']() %}
{% set data = salt['mc_snmpd.settings']() %}
include:
  - makina-states.services.monitoring.snmpd.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
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
            {{sdata.c.minion.msr}}/files/usr/bin/net-snmp-create-v3-user
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
    - unless: grep -q  {{data['default_user']}} /usr/share/snmp/snmpd.conf
    - name: >
            service snmpd stop;
            net-snmp-config --create-snmpv3-user -A SHA
            -a {{data['default_password']}}
            -X DES -x {{data['default_key']}} {{data['default_user']}}

{% endif %}
