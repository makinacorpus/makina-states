{#-
# network configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/network.rst
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'network') }}
{%- set locs = salt['mc_localsettings.settings']()['locations'] %}
{%- if localsettings.networkManaged %}
{%- if grains['os_family'] in ['Debian'] %}
network-cfg:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - name: {{ locs.conf_dir }}/network/interfaces
    - source: salt://makina-states/files/etc/network/interfaces
    - context:
      {#- tradeof to make the lxc state work with us #}
      network_interfaces: {{ localsettings.networkInterfaces|yaml }}

network-services:
  service.running:
    - enable: True
    - names:
      - networking
      {% if grains['os'] in ['Ubuntu'] %}- resolvconf{% endif %}
    - watch:
      - file: network-cfg
{%- endif %}
{% endif %}
{# be sure to have at least one state #}
network-last-hook:
  mc_proxy.hook:
    - order: last
