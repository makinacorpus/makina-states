{#-
# Configure /etc/hosts entries based on pillar informations
# see:
#   - makina-states/doc/ref/formulaes/localsettings/hosts.rst
#}
{% set mcn = salt['mc_network.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'hosts') }}
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

append-hosts-accumulator-from-pillar:
  file.accumulated:
    - require_in:
      - file: makina-append-etc-hosts-management
    - filename: {{ locs.conf_dir }}/hosts
    - text: |
            #end
            {{ hosts_list|sort|join(separator) }}
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

makina-append-etc-hosts-management:
  file.blockreplace:
    - name: {{ locs.conf_dir }}/hosts
    - marker_start: "#-- start salt managed zoneend -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end salt managed zoneend --"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True

/etc/hostname-set:
  cmd.run:
    - name: |
            echo {{mcn.hostname}} > /etc/hostname;
            chown root:root /etc/hostname;
            chmod 644 /etc/hostname;
            hostname {{mcn.hostname}}
    - user: root
    - unless: test "x$(cat /etc/hostname)" = "x{{mcn.hostname}}"
{% endif %}
