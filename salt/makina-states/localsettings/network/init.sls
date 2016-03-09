{#- # network configuration #}
include:
  - makina-states.localsettings.network.hooks
# be sure to reconfigure firewall on network
# reconfiguration
  - makina-states.services.firewall.firewall.noinstall
  - makina-states.localsettings.grub

{% set mcnet = salt['mc_network.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'network') }}
{%- if mcnet.networkManaged %}
{%- if grains['os_family'] in ['Debian'] %}

network-cfg-reset:
  file.managed:
    - user: root
    - group: root
    - mode: '0755'
    - template: jinja
    - name: {{ locs.conf_dir }}/network/if-up.d/reset-net-bridges
    - source: salt://makina-states/files/etc/reset-net-bridges
    - require_in:
      - mc_proxy: network-cfg-gen

network-cfg:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - name: {{ locs.conf_dir }}/network/interfaces
    - source: salt://makina-states/files/etc/network/interfaces
    - watch_in:
      - mc_proxy: network-cfg-gen

# second chance to bring up failover ips
{% for ifc in mcnet.interfaces_order %}
{% set ifn = mcnet.interfaces[ifc]['ifname'] %}
{% set addr = mcnet.interfaces[ifc].get('address', '')%}
network-cfg-{{ifc}}:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - makedirs: true
    - template: jinja
    - name: "{{ locs.conf_dir }}/network/interfaces.d/interface.{{ifn}}.cfg"
    - source: salt://makina-states/files/etc/network/interface
    - defaults:
        ifname: "{{ifc}}"
    - watch_in:
      - mc_proxy: network-cfg-gen

network-services-{{ifc}}-2nd-gen:
  file.managed:
    - source: "salt://makina-states/files/etc/network/reconfigure_ifc.sh"
    - name: "/etc/network/mc_reconfigure_{{ifc}}.sh"
    - defaults:
        addr: "{{addr}}"
        ifn: "{{ifn}}"
    - user: root
    - group: root
    - mode: 750
    - template: jinja
    - watch_in:
      - mc_proxy: network-cfg-gen
{%endfor %}

{% for ifc in mcnet.interfaces_order %}
{% set ifn = mcnet.interfaces[ifc]['ifname'] %}
# we always exit0 here to let the 2nd chance script to execute in case
network-services-{{ifc}}:
  cmd.watch:
    - name: "/etc/network/mc_reconfigure_{{ifc}}.sh nofail"
    - use_vt: true
    - watch:
      - mc_proxy: network-cfg-gen
    - watch_in:
      - mc_proxy: "network-configured-{{ifc}}"
# restart bridges after getting real nic ifs in static mode
{% if 'br' in ifc %}
{% for ifcinner in mcnet.interfaces_order %}
{% if 'br' not in ifcinner %}
      - mc_proxy: "network-configured-{{ifcinner}}"
{%endif %}
{%endfor %}
{%endif %}

"network-configured-{{ifc}}":
  mc_proxy.hook:
    - require:
      - mc_proxy: network-1nd
    - require_in:
      - mc_proxy: network-2nd
{%endfor %}

# second chance to bring up failover ips
{% for ifc in mcnet.interfaces_order %}
{% set ifn = mcnet.interfaces[ifc]['ifname'] %}
network-services-{{ifc}}-2nd:
  cmd.run:
    - name: "/etc/network/mc_reconfigure_{{ifc}}.sh"
    - use_vt: true
    - watch:
      - mc_proxy: network-2nd
    - watch_in:
      - mc_proxy: network-last-hook
{%endfor %}

{% endif %}
{% endif %}
