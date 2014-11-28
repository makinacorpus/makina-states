{#-
# network configuration
#}
include:
  - makina-states.localsettings.network.hooks
{% if salt['mc_services.registry']().has['firewall.shorewall'] %}
# be sure to reconfigure firewall on network
# reconfiguration
  - makina-states.services.firewall.shorewall
  - makina-states.localsettings.grub
{% endif %}


{% set mcnet = salt['mc_network.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'network') }}
{%  if salt['mc_controllers.mastersalt_mode']() %}
{%- if mcnet.networkManaged %}
{%- if grains['os_family'] in ['Debian'] %}

network-cfg-reset:
  file.managed:
    - require_in:
      - mc_proxy: network-last-hook
    - user: root
    - group: root
    - mode: '0755'
    - template: jinja
    - name: {{ locs.conf_dir }}/network/if-up.d/reset-net-bridges
    - source: salt://makina-states/files/etc/network/if-up.d/reset-net-bridges

network-cfg:
  file.managed:
    - watch_in:
      - file: network-cfg-reset
      - mc_proxy: network-last-hook
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
    - watch_in:
      - mc_proxy: network-last-hook
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
    - name: ifdown {{ifn}};ifconfig {{ifn}} down;ifup {{ifn}};ret=${?};ifup {{ifn}};exit ${ret}
    - watch_in:
      - mc_proxy: network-last-hook
    - watch:
      - file: network-cfg
      - file: network-cfg-{{ifc}}
{# restart bridges after getting real nic ifs in static mode #}
{% if 'br' in ifc %}
{% for ifcinner in mcnet.interfaces_order %}
{% if not 'br' in ifcinner %}
      - file: network-cfg-{{ifcinner}}
      - cmd: network-services-{{ifcinner}}
{%endif %}
{%endfor %}
{%endif %}
{%endfor %}

{% endif %}
{% endif %}
{% endif %}
