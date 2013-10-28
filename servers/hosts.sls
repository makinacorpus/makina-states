#
# Configure /etc/hosts entries based on pillar informations
# eg in pillar:
#
#toto-makina-hosts:
#    - ip: 10.0.0.8
#      hosts: foo.company.com foo
#    - ip: 10.0.0.3
#      hosts: bar.company.com bar
#others-makina-hosts:
#    - ip: 192.168.1.52.1
#      hosts: foobar.foo.com foobar
#    - ip: 192.168.1.52.2
#      hosts: toto.foo.com toto2.foo.com toto3.foo.com toto
#    - ip: 10.0.0.4
#      hosts: alias alias.foo.com
# All theses entries will be entered inside a block identified by:
# #-- start salt managed zone -- PLEASE, DO NOT EDIT
# (here)
# #-- end salt managed zone --
# It's your job to ensure theses IP will not be used on other
# entries in this file.
#
# If you want to add some data in this block without using the pillar
# you can also use a file.accumulated state and push content in
# an accumulator while targeting /etc/hosts file with filename entry,
# this way:
# this-is-my-custom-state
#    file.accumulated:
#      - filename: /etc/hosts
#      - name: hosts-accumulator-makina-hosts-entries
#      - text: "here your text"
#      - require_in:
#        - file: makina-etc-host-vm-management

{% set makinahosts=[] %}
{% set hosts_list=[] %}
{% for k, data in pillar.items() %}
  {% if k.endswith('makina-hosts') %}
    {% set dummy=makinahosts.extend(data) %}
  {% endif %}
{% endfor %}
# loop to create a dynamic list of states based on pillar content
{% for host in makinahosts %}
  {% set dummy=hosts_list.append( host['ip'] + ' ' + host['hosts'] ) %}
{% endfor %}
{% if hosts_list %}
# spaces are used in the join operation to make this text looks like a yaml multiline text
  {% set separator="\n        "%}
# This state will use an accumulator to build the dynamic block content in /etc/hosts
# you can reuse this accumulator on other states
# (@see makina-etc-host-vm-management)
hosts-accumulator-from-pillar:
  file.accumulated:
    - filename: /etc/hosts
    - name: hosts-accumulator-makina-hosts-entries
    - text: |
        {{ hosts_list|sort|join(separator) }}
    - require_in:
      - file: makina-etc-host-vm-management

{% endif %}

# States editing a block in /etc/hosts
# Accumulators targeted on this file will be used
# TODO: provide a way to select accumulators and distinct blocks
makina-etc-host-vm-management:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: "#-- start salt managed zone -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end salt managed zone --"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True

## -------- DEVELOPMENT VM ZONE --------
{% if grains.get('makina.devhost', false) %}
{% set vm_fqdn = grains.get('fqdn','childhost.local') %}
{% set vm_host = grains.get('host','childhost') %}
{% set vm_name = vm_fqdn.replace('.', '_').replace(' ', '_') %}
{% set vm_nat_fqdn = vm_fqdn.split('.')[:1][0]+'-nat.'+'.'.join(vm_fqdn.split('.')[1:]) %}
{% set ips=grains['ip_interfaces'] %}
{% set ip1=ips['eth0'][0] %}
{% set ip2=ips['eth1'][0] %}

makina-parent-etc-host-exists:
  file.exists:
    - name: /mnt/parent_etc/hosts

makina-parent-etc-host-vm-management:
  file.blockreplace:
    - name: /mnt/parent_etc/hosts
    - marker_start: "#-- start salt managed zone :: VM={{ vm_name}} :: DO NOT EDIT --"
    - marker_end: "#-- end salt managed zone VM {{ vm_name}} --"
    - content: '# Vagrant vm: {{ vm_fqdn }} added this entry via local mount:'
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - require:
        - file: makina-parent-etc-host-exists

# initialize the accumulator with at least the VM private network socket
# Use this accumulator to add any IP managed on this vm that the parent
# host should know about
makina-parent-etc-host-accumulated:
  file.accumulated:
    - filename: /mnt/parent_etc/hosts
    - name: parent-hosts-accumulator-{{ vm_name}}-entries
    - text: |
        {{ ip2 }} {{ vm_fqdn }} {{ vm_host }}
        {{ ip1 }} {{ vm_nat_fqdn }} {{ vm_host }}-nat
    - require_in:
        - file: makina-parent-etc-host-vm-management

{% endif %}

