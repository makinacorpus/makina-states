#
# Configure /etc/hosts entries based on pillar informations
# eg in pillar:
#
#toto-makina-hosts:
#    - ip: 10.0.0.8
#      hosts: foo foo.company.com
#    - ip: 10.0.0.3
#      hosts: bar bar.company.com
#others-makina-hosts:
#    - ip: 192.168.1.52.1
#      hosts: foobar foobar.foo.com
#    - ip: 192.168.1.52.2
#      hosts: toto toto.foo.com toto2.foo.com toto3.foo.com
#    - ip: 10.0.0.3
#      hosts: alias alias.foo.com
# If you alter on host IP or if you already used the given hosts string in your /etc/hosts
# this host string will be searched upon the file and removed (the whole line)
# to ensure the same host name is not used with several IPs

{% set makinahosts=[] %}
{% for k, data in pillar.items() %}
  {% if k.endswith('makina-hosts') %}
    {% set dummy=makinahosts.extend(data) %}
  {% endif %}
{% endfor %}
# loop to create a dynamic list of states based on pillar content
{% for host in makinahosts %}

## RLE: commented the host removal stuff, file.blockreplace is maaging the whole dynamic block
## if other entries in manual edit or managed blocks reference the same IP
## it will be the user stuff to debunk it.
# the state name should not contain dots and spaces
#{{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host-cleanup:
#  # detect presence of the same host name with another IP
#  file.replace:
#    - require_in:
#      - file: {{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host
#    - name: /etc/hosts
#    - pattern: ^((?!{{ host['ip'].replace('.', '\.')  }}).)*{{ host['hosts'].replace('.', '\.') }}(.)*$
#    - repl: ""
#    - flags: ['IGNORECASE','MULTILINE', 'DOTALL']
#    - bufsize: file
#    - show_changes: True

# Theses states will use an accumulator to build the dynamic block content in /etc/hosts
# (@see makina-etc-host-vm-management)
# the state name should not contain dots and spaces
{{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host:
    # append new host record
    file.append:
      - name: /etc/hosts
      - text: "{{ host['ip'] }} {{ host['hosts'] }} # entry managed via salt"
    file.accumulated:
      - filename: /etc/hosts
      - name: hosts-accumulator-makina-hosts-entries
      - text: "{{ host['ip'] }} {{ host['hosts'] }}"
      - require_in:
        - file: makina-etc-host-vm-management

{% endfor %}

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
{% set vm_fqdn = grains.get('fqdn','childhost') %}
{% set vm_name = vm_fqdn.replace('.', '_').replace(' ', '_') %}
{% set ips=grains['ip_interfaces'] %}
{% set ip1=ips['eth0'][0] %}
{% set ip2=ips['eth1'][0] %}

makina-parent-etc-host-exists:
  file.exists:
    -name: /mnt/parent_etc/hosts

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
    - filename: /srv/foo
    - name: parent-hosts-accumulator-{{ vm_name}}-entries
    - text: "{{ ip2 }} {{ vm_fqdn }}"
    - require_in:
        - file: makina-parent-etc-host-vm-management
{% endif %}

