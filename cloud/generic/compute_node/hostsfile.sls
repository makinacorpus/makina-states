{% load_json as compute_node_settings %}{{pillar.scnSettings}}{%endload%}
{% load_json as cloudSettings %}{{pillar.scloudSettings}}{%endload%}

{% set localsettings = salt['mc_localsettings.settings']() %}
{% set domains = [] %}
{% set tdata = compute_node_settings.cn %}

{% for vmname, data in tdata.vms.items() -%}
{%  for domain in data['domains'] %}
{%    if not domain in domains%}
{%      do domains.append(domain)%}
avirt-{{vmname}}-makina-append-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- start virt dns {{domain}}:: DO NOT EDIT --'
    - marker_end: '#-- end virt dns {{domain}}:: DO NOT EDIT --'
    - content: '# Vagrant vm: {{domain}} added this entry via local mount:'
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
amakina-parent-append-etc.computenode.accumulated-virt-{{vmname}}:
  file.accumulated:
    - watch_in:
       - file: avirt-{{vmname}}-makina-append-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-append-accumulator-virt-{{vmname}}-entries
    - text: |
            {{ data.ip }} {{domain}}
virt-{{vmname}}-makina-prepend-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- bstart virt dns {{domain}}:: DO NOT EDIT --'
    - marker_end: '#-- bend virt dns {{domain}}:: DO NOT EDIT --'
    - content: '# bVagrant vm: {{domain}} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
makina-parent-prepend-etc.computenode.accumulated-virt-{{vmname}}:
  file.accumulated:
    - watch_in:
       - file: virt-{{vmname}}-makina-prepend-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-prepend-accumulator-virt-{{vmname}}-entries
    - text: |
            {{ data.ip }} {{domain}}
{%      if salt['mc_nodetypes.registry']()['is']['devhost'] %}
avirt-{{vmname}}-makina-append-parent-etc.computenode.management-devhost-touch:
  file.touch:
    - name: /etc/devhosts.{{domain}}
virt-{{vmname}}-makina-prepend-parent-etc.computenode.management-devhost:
  file.blockreplace:
    - name: /etc/devhosts.{{domain}}
    - marker_start: '#-- start devhost -- bstart virt dns {{domain}}:: DO NOT EDIT --'
    - marker_end: '#-- end devhost -- bend virt dns {{domain}}:: DO NOT EDIT --'
    - content: '# bVagrant vm: {{domain}} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - watch:
      - file: avirt-{{vmname}}-makina-append-parent-etc.computenode.management-devhost-touch
makina-parent-prepend-etc.computenode.accumulated-virt-{{vmname}}-devhost:
  file.accumulated:
    - watch_in:
       - file: virt-{{vmname}}-makina-prepend-parent-etc.computenode.management-devhost
    - filename: /etc/devhosts.{{domain}}
    - name: parent-hosts-prepend-accumulator-virt-{{vmname}}-entries
    - text: |
            {{ localsettings.devhost_ip }} {{domain}}
{%      endif %}
{%    endif %}
{%  endfor %}
{% endfor %}
