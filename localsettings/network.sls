{#-
# network configuration
#}
{% set mcnet = salt['mc_network.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'network') }}
{% if salt['mc_controllers.mastersalt_mode']() %}

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
      data: |
            {{salt['mc_utils.json_dump'](mcnet)}}

{% for ifc in mcnet.interfaces_order %}
{% set ifn = mcnet.interfaces[ifc]['ifname'] %}
network-cfg-{{ifc}}:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - makedirs: true
    - template: jinja
    - name: {{ locs.conf_dir }}/network/interfaces.d/interface.{{ifn}}.cfg
    - source: salt://makina-states/files/etc/network/interface
    - context:
      ifname: {{ifc}}
      data: |
            {{salt['mc_utils.json_dump']( mcnet)}}

network-services-{{ifc}}:
  cmd.watch:
    - name: ifdown {{ifn}};ifup {{ifn}}
#    - watch_in:
#      - service: network-services
    - watch:
      - file: network-cfg
      - file: network-cfg-{{ifc}}
{% endfor %}

#network-services:
#  service.running:
#    - enable: True
#    - names:
#      {% if grains.get('oscodename:') not in ['trusty'] %}- networking{% endif %}
#      {% if grains['os'] in ['Ubuntu'] %}- resolvconf{% endif %} {% endif %}

{% endif %}
{% endif %}
{# be sure to have at least one state #}
network-last-hook:
  mc_proxy.hook:
    - order: last

