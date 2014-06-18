{% set data = salt['mc_cloud_compute_node.cn_settings']() %}
{% set compute_node_settings = data.cnSettings %}
{% set cloudSettings = data.cloudSettings %}
{% set domains = [] %}
{% set tdata = compute_node_settings.cn %}

configure-cloud-{{opts.id}}-hostfiles:
  mc_proxy.hook: []

{% for vmname, data in tdata.vms.items() -%}
{%  for domain in data['domains'] %}
{%    if not domain in domains%}
{%      do domains.append(domain)%}
avirt-{{vmname}}{{domain}}-makina-append-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- start virt dns {{domain}}:: DO NOT EDIT --'
    - marker_end: '#-- end virt dns {{domain}}:: DO NOT EDIT --'
    - content: '# Vagrant vm: {{domain}} added this entry via local mount:'
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
amakina-parent-append-etc.computenode.accumulated-virt-{{vmname}}{{domain}}:
  file.accumulated:
    - watch_in:
       - file: avirt-{{vmname}}{{domain}}-makina-append-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-append-accumulator-virt-{{vmname}}-entries
    - text: |
            {{ data.ip }} {{domain}}
virt-{{vmname}}{{domain}}-makina-prepend-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- bstart virt dns {{domain}}:: DO NOT EDIT --'
    - marker_end: '#-- bend virt dns {{domain}}:: DO NOT EDIT --'
    - content: '# bVagrant vm: {{domain}} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
makina-parent-prepend-etc.computenode.accumulated-virt-{{vmname}}{{domain}}:
  file.accumulated:
    - watch_in:
       - file: virt-{{vmname}}{{domain}}-makina-prepend-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-prepend-accumulator-virt-{{vmname}}{{domain}}-entries
    - text: |
            {{ data.ip }} {{domain}}
{%      if salt['mc_nodetypes.registry']()['is']['devhost'] %}
avirt-{{vmname}}{{domain}}-makina-append-parent-etc.computenode.management-devhost-touch:
  file.touch:
    - name: /etc/devhosts.{{domain}}
virt-{{vmname}}{{domain}}-makina-prepend-parent-etc.computenode.management-devhost:
  file.blockreplace:
    - name: /etc/devhosts.{{domain}}
    - marker_start: '#-- start devhost -- bstart virt dns {{domain}}:: DO NOT EDIT --'
    - marker_end: '#-- end devhost -- bend virt dns {{domain}}:: DO NOT EDIT --'
    - content: '# bVagrant vm: {{domain}} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - watch:
      - file: avirt-{{vmname}}{{domain}}-makina-append-parent-etc.computenode.management-devhost-touch
makina-parent-prepend-etc.computenode.accumulated-virt-{{vmname}}{{domain}}-devhost:
  file.accumulated:
    - watch_in:
       - file: virt-{{vmname}}{{domain}}-makina-prepend-parent-etc.computenode.management-devhost
    - filename: /etc/devhosts.{{domain}}
    - name: parent-hosts-prepend-accumulator-virt-{{vmname}}{{domain}}-entries
    - text: |
            {{ salt['mc_network.settings']().devhost_ip }} {{domain}}
{%      endif %}
{%    endif %}
{%  endfor %}
{% endfor %}
