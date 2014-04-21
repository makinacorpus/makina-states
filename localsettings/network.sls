{#-
# network configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/network.rst
#}
{% set mcnet = salt['mc_network.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'network') }}
{%- set locs = salt['mc_locations.settings']() %}
{%- if mcnet.networkManaged %}
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
      network_interfaces: |
                          {{salt['mc_utils.json_dump']( mcnet.interfaces)}}

network-services:
  service.running:
    - enable: True
    - names:
      {% if grains.get('oscodename:') not in ['trusty'] %}- networking{% endif %}
      {% if grains['os'] in ['Ubuntu'] %}- resolvconf{% endif %}
    - watch:
      - file: network-cfg
{%- endif %}
{% endif %}
{# be sure to have at least one state #}
network-last-hook:
  mc_proxy.hook:
    - order: last
