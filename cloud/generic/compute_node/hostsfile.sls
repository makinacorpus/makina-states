{% set vmsdata = salt['mc_cloud_vm.settings']() %}
{% set domains = [] %}
{% set hostsfile = [] %}
{% for vmname, data in vmsdata.vms.items() -%}
{%  for domain in data['domains'] %}
{%    if not domain in domains%}
{%      do hostsfile.append((data.ip, domain))%}
{%    endif %}
{%  endfor %}
{% endfor %}

configure-cloud-{{opts.id}}-hostfiles:
  mc_proxy.hook: []


avirt-makina-append-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- start ms virt dns :: DO NOT EDIT --'
    - marker_end: '#-- end ms virt dns :: DO NOT EDIT --'
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
amakina-parent-append-etc.computenode.accumulated-virt:
  file.accumulated:
    - watch_in:
       - file: avirt-makina-append-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-append-accumulator-virt-entries
    - text: |
            {% for ip, text in hostsfile %}{{-ip}} {{text}}
            {% endfor %}

virt-makina-prepend-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- bstart ms virt dns :: DO NOT EDIT --'
    - marker_end: '#-- bend ms virt dns :: DO NOT EDIT --'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
makina-parent-prepend-etc.computenode.accumulated-virt:
  file.accumulated:
    - watch_in:
       - file: virt-makina-prepend-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-prepend-accumulator-virt-entries
    - text: |
            {% for ip, text in hostsfile %}{{-ip}} {{text}}
            {% endfor %}
