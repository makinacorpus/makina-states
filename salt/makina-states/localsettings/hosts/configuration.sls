{#-
# Configure /etc/hosts entries based on pillar informations
# see:
#   - makina-states/doc/ref/formulaes/localsettings/hosts.rst
#}
include:
  - makina-states.localsettings.hosts.hooks

{% set mcn = salt['mc_network.settings']() %}
{# atomic file is not supported for /etc/hosts on a readonly layer (docker)
 # where the file can be written but not moved #}
{% if not salt['mc_nodetypes.is_docker']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set hosts_list = mcn.hosts_list %}
{%- if hosts_list %}
# spaces are used in the join operation to make this text looks like a yaml multiline text
{%- set separator="\n            " %}
{#- This state will use an accumulator to build the dynamic block content in {{ locs.conf_dir }}/hosts
# you can reuse this accumulator on other states
# (@see makina-etc-host-vm-management)
#}
prepend-hosts-accumulator-from-pillar:
  file.accumulated:
    - require_in:
      - file: makina-prepend-etc-hosts-management
    - filename: {{ locs.conf_dir }}/hosts
    - text: |
            {{ hosts_list|sort|join(separator) }}
    - watch:
      - mc_proxy: makina-hosts-hostfiles-pre
    - watch_in:
      - mc_proxy: makina-hosts-hostfiles-post

append-hosts-accumulator-from-pillar:
  file.accumulated:
    - require_in:
      - file: makina-append-etc-hosts-management
    - filename: {{ locs.conf_dir }}/hosts
    - text: |
            #end
            {{ hosts_list|sort|join(separator) }}
    - watch:
      - mc_proxy: makina-hosts-hostfiles-pre
    - watch_in:
      - mc_proxy: makina-hosts-hostfiles-post
{% endif %}

{#- States editing a block in {{ locs.conf_dir }}/hosts
# Accumulators targeted on this file will be used
# TODO: provide a way to select accumulators and distinct blocks
#}
makina-prepend-etc-hosts-management:
  file.blockreplace:
    - name: {{ locs.conf_dir }}/hosts
    - marker_start: "#-- start salt managed zonestart -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end salt managed zonestart --"
    - content: ''
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - watch:
      - mc_proxy: makina-hosts-hostfiles-pre
    - watch_in:
      - mc_proxy: makina-hosts-hostfiles-post

makina-append-etc-hosts-management:
  file.blockreplace:
    - name: {{ locs.conf_dir }}/hosts
    - marker_start: "#-- start salt managed zoneend -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end salt managed zoneend --"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - watch:
      - mc_proxy: makina-hosts-hostfiles-pre
    - watch_in:
      - mc_proxy: makina-hosts-hostfiles-post
{% endif %}
