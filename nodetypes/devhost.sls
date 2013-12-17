#
# Flag the machine as a development box
#

{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}

{{ nodetypes.register('devhost') }}

include:
 - {{ nodetypes.statesPref }}vm
 - makina-states.services.mail.postfix
 {% if not 'dockercontainer' in nodetypes.registry['actives'] %}
 - makina-states.services.mail.dovecot
 {% endif %}
 - makina-states.localsettings.hosts

# -------- DEVELOPMENT VM ZONE --------
{% set vm_fqdn = grains.get('fqdn','childhost.local') %}
{% set vm_host = grains.get('host','childhost') %}
{% set vm_name = vm_fqdn.replace('.', '_').replace(' ', '_') %}
{% set vm_nat_fqdn = vm_fqdn.split('.')[:1][0]+'-nat.'+'.'.join(vm_fqdn.split('.')[1:]) %}
{% set ips=grains['ip_interfaces'] %}
{% set ip1=ips['eth0'][0] %}
{% set ip2=ips['eth1'][0] %}

makina-parent-etc-hosts-exists:
  file.exists:
    - name: /mnt/parent_etc/hosts

makina-prepend-parent-etc-hosts-management:
  file.blockreplace:
    - name: /mnt/parent_etc/hosts
    - marker_start: "#-- start salt managed zonestart :: VM={{ vm_name }} :: DO NOT EDIT --"
    - marker_end: "#-- end salt managed zonestart VM {{ vm_name }} --"
    - content: '# Vagrant vm: {{ vm_fqdn }} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - require:
      - file: makina-parent-etc-hosts-exists

makina-append-parent-etc-hosts-management:
  file.blockreplace:
    - name: /mnt/parent_etc/hosts
    - marker_start: "#-- start salt managed zoneend :: VM={{ vm_name }} :: DO NOT EDIT --"
    - marker_end: "#-- end salt managed zoneend VM {{ vm_name }} --"
    - content: '# Vagrant vm: {{ vm_fqdn }} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - require:
      - file: makina-parent-etc-hosts-exists

# initialize the accumulator with at least the VM private network socket
# Use this accumulator to add any IP managed on this vm that the parent
# host should know about
makina-parent-prepend-etc-hosts-accumulated:
  file.accumulated:
    - filename: /mnt/parent_etc/hosts
    - name: parent-hosts-prepend-accumulator-{{ vm_name }}-entries
    - text: |
            {{ ip2 }} {{ vm_fqdn }} {{ vm_host }}
            {{ ip1 }} {{ vm_nat_fqdn }} {{ vm_host }}-nat
    - require_in:
      - file: makina-prepend-parent-etc-hosts-management

makina-parent-append-etc-hosts-accumulated:
  file.accumulated:
    - filename: /mnt/parent_etc/hosts
    - name: parent-hosts-aapend-accumulator-{{ vm_name }}-entries
    - text: |
            {{ ip2 }} {{ vm_fqdn }} {{ vm_host }}
            {{ ip1 }} {{ vm_nat_fqdn }} {{ vm_host }}-nat
    - require_in:
      - file: makina-append-parent-etc-hosts-management
