{% set localsettings = salt['mc_localsettings.settings']() %}
{% set vmname = pillar.mccloud_svmname %}
{% set target = pillar.mccloud_stargetname %}
{% set devhost = pillar.sisdevhost %}
{% load_json as compute_node_settings%}{{scnSettings}}{%endload%}
{% load_json as data%}{{lxcVmData}}{%endload%}
{% load_json as cloudSettings%}{{scloudSettings}}{%endload%}
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
