{#-
# Configure machine physical network based on pillar information
#
# This state will only apply if you set to true the config value (grain or pillar): **makina-states.localsettings.network_managed**
#
# The template is shared with the lxc state, please also look it
#
# makina-states.localsettings.network.managed : true
# *-makina-network:
#   ifname:
#   - auto: (opt) (default: True)
#   - mode: (opt) (default: dhcp or static if address)
#   - address: (opt)
#   - netmask: (opt)
#   - gateway: (opt)
#   - dnsservers: (opt)
#
# EG:
# makina-states.localsettings.network.managed : true
# myhost-makina-network:
#   etho: # manually configured interface
#     - address: 8.1.5.4
#     - netmask: 255.255.255.0
#     - gateway: 8.1.5.1
#     - dnsservers: 8.8.8.8
#   em1: {} # -> dhcp based interface
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'network') }}
{%- set locs = localsettings.locations %}
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
