{% set data = salt['mc_cloud_vm.vm_settings']() %}
{% set vmname = data.name %}
{% set devhost = salt['mc_nodetypes.is_devhost']() %}
{% set domains = [] %}
{# only for extra domains, we map to localhost
   the main domain is mapped to the local ip via another state #}
{% for domain in data.get('domains', []) %}
{%  if not domain in domains and not domain == grains['id'] %}
{%    do domains.append(domain) %}
{%  endif %}
{% endfor %}
{% set sdomains = ' '.join(domains) %}
{% if devhost %}
adocker-{{vmname}}-makina-append-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- start docker dns {{vmname}}:: DO NOT EDIT --'
    - marker_end: '#-- end docker dns {{vmname}}:: DO NOT EDIT --'
    - content: '# Vagrant vm: {{vmname }} added this entry via local mount:'
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
amakina-parent-append-etc.computenode.accumulated-docker-{{vmname}}:
  file.accumulated:
    - watch_in:
       - file: adocker-{{vmname}}-makina-append-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-append-accumulator-docker-{{ vmname }}-entries
    - text: |
            {{ data.gateway }} {{ data.target }} {{grains['id'] }}
            {% if sdomains.strip() %}127.0.0.1 {{sdomains}}{% endif%}
docker-{{vmname}}-makina-prepend-parent-etc.computenode.management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: '#-- bstart docker dns {{vmname}}:: DO NOT EDIT --'
    - marker_end: '#-- bend docker dns {{vmname}}:: DO NOT EDIT --'
    - content: '# bVagrant vm: {{ vmname }} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
makina-parent-prepend-etc.computenode.accumulated-docker-{{vmname}}:
  file.accumulated:
    - watch_in:
       - file: docker-{{vmname}}-makina-prepend-parent-etc.computenode.management
    - filename: /etc/hosts
    - name: parent-hosts-prepend-accumulator-docker-{{ vmname }}-entries
    - text: |
            {{ data.gateway }} {{ data.target }}
            {% if sdomains.strip() %}127.0.0.1 {{sdomains}}{% endif%}
{% else %}
c{{vmname}}-docker.computenode.sls-generator-for-hostnode:
  mc_proxy.hook: []
{% endif %}