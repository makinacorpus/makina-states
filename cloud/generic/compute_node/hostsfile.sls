{% set vmsdata = salt['mc_cloud_vm.settings']() %}
{% set domains = [] %}

configure-cloud-{{opts.id}}-hostfiles:
  mc_proxy.hook: []

{% for vmname, data in vmsdata.vms.items() -%}
{%  for domain in data['domains'] %}
{%    if not domain in domains%}
{%      do domains.append(domain)%}
avirt-{{vmname}}{{domain}}-makina-append-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- start virt dns {{domain}}:: DO NOT EDIT --'
    - marker_end: '#-- end virt dns {{domain}}:: DO NOT EDIT --'
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
{%    endif %}
{%  endfor %}
{% endfor %}
