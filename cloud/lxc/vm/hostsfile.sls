{% set localsettings = salt['mc_localsettings.settings']() %}
{% set vmname = pillar.mccloud_vmname %}
{% set target = pillar.mccloud_targetname %}
{% set devhost = pillar.sisdevhost %}
{% set compute_node_settings = salt['mc_utils.json_load'](pillar.scnSettings) %}
{% set data = salt['mc_utils.json_load'](pillar.slxcVmData) %}
{% set cloudSettings = salt['mc_utils.json_load'](pillar.scloudSettings) %}
{% if devhost %}
alxc-{{vmname}}-makina-append-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- start lxc dns {{vmname}}:: DO NOT EDIT --'
    - marker_end: '#-- end lxc dns {{vmname}}:: DO NOT EDIT --'
    - content: '# Vagrant vm: {{vmname }} added this entry via local mount:'
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
amakina-parent-append-etc.computenode.accumulated-lxc-{{vmname}}:
  file.accumulated:
    - watch_in:
       - file: alxc-{{vmname}}-makina-append-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-append-accumulator-lxc-{{ vmname }}-entries
    - text: |
            {{ data.gateway }} {{ target }} {{grains['id'] }}
lxc-{{vmname}}-makina-prepend-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- bstart lxc dns {{vmname}}:: DO NOT EDIT --'
    - marker_end: '#-- bend lxc dns {{vmname}}:: DO NOT EDIT --'
    - content: '# bVagrant vm: {{ vmname }} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
makina-parent-prepend-etc.computenode.accumulated-lxc-{{vmname}}:
  file.accumulated:
    - watch_in:
       - file: lxc-{{vmname}}-makina-prepend-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-prepend-accumulator-lxc-{{ vmname }}-entries
    - text: |
            {{ data.gateway }} {{ target }} {{grains['id'] }}
{% else %}
c{{vmname}}-lxc.computenode.sls-generator-for-hostnode:
  mc_proxy.hook: []
{% endif %}
