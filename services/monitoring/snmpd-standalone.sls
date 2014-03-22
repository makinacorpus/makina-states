{#- snmpd configuration
#
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = salt['mc_localsettings']()['locations'] %}
{%- set data = salt['mc_snmpd.settings']() %}
{{ salt['mc_macros.register']('services', 'monitoring.snmpd') }}

{% macro do(full=True) %}
{% if full %}
snmpd-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - snmp
      - libsensors4
      - libsnmp-base
      - libsnmp15
      - libsnmp-perl
      - nagios-plugins-basic
      - snmpd
{%- endif %}

{#- Configuration #}
snmpd-default-snmpd:
  file.managed:
    - name: {{ locs.conf_dir }}/default/snmpd.conf
    - source: salt://makina-states/files/etc/default/snmpd.conf
    - template: jinja
    - user: root
    - group : root
    - mode: 644

snmpd-snmd-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/snmp/snmpd.conf
    - source: salt://makina-states/files/etc/snmpd.conf
    - template: jinja
    - user: root
    - group: root
    - mode: 600
    - watch_in:
      - mc_proxy: snmpd-pre-restart

{#- Run #}
snmpd-start:
service.running:
  - name: snmpd
  - enable: True
  - watch:
    - mc_proxy: snmpd-pre-restart
  - watch_in:
    - mc_proxy: snmpd-post-restart

{% endmacro %}
{{ do(full=False) }}
