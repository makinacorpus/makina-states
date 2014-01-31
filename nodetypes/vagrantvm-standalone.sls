{#
# separate file to to the vagrant vm setup, to be reused in other states
# while not reimporting the whole makina-states stack.
#}
{#
# extra setup on a vagrant vm box
#}

{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% set localsettings = nodetypes.localsettings %}
{{ salt['mc_macros.register']('nodetypes', 'vagrantvm') }}

include:
  - makina-states.services.virt.lxc
  - makina-states.services.virt.docker

{# not needed anymore as the core files are not anymore on NFS
{# if grains['os'] in ['Ubuntu'] %}
# Delay start on vagrant dev host by adding to upstart delayers
makina-file_waiting_for_vagrant:
  file.managed:
    - name: /etc/init/waiting_for_vagrant_nfs.conf
    - source: salt://makina-states/files/etc/init/delay_services_for_vagrant_nfs.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja

makina-file_delay_services_for_srv:
  file.managed:
    - require:
      - file: makina-file_waiting_for_vagrant
    - name: /etc/init/delay_services_for_vagrant_nfs.conf
    - source: salt://makina-states/files/etc/init/delay_services_for_vagrant_nfs.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
{% endif %}
#}

# add vagrant to editor
addvagrant-to-editor:
  user.present:
    - name: vagrant
    - optional_groups:
      - {{localsettings.group}}
    - remove_groups: false

vagrantvm-zerofree:
  file.managed:
    - name: /sbin/zerofree.sh
    - source: salt://makina-states/files/sbin/zerofree.sh
    - user: root
    - group: root
    - mode: 750
    - template: jinja
    - rootdev: {{salt['mc_utils.get']('makina-states.zerofree_dev', '/dev/sda1')}}

vagrantvm-systemcleanup:
  file.managed:
    - name: /sbin/system-cleanup.sh
    - source: salt://makina-states/files/sbin/system-cleanup.sh
    - user: root
    - group: root
    - mode: 750
    - template: jinja
    - rootdev: {{salt['mc_utils.get']('makina-states.zerofree_dev', '/dev/sda1')}}


{% if grains['os'] in ['Ubuntu'] %}
disable-vagrant-useless-services:
  cmd.run:
    - name: |
            PLYMOUTH_SERVICES=$(find /etc/init -name 'plymouth*'|grep -v override|sed -re "s:/etc/init/(.*)\.conf:\1:g");
            UPSTART_DISABLED_SERVICES="$PLYMOUTH_SERVICES";
            for service in $UPSTART_DISABLED_SERVICES;do
                sf=/etc/init/$service.override;
                if [[ "$(cat $sf 2>/dev/null)" != "manual" ]];then
                    echo "manual" > "$sf";
                    service $service stop;
                fi;
            done
    - onlyif: |
              PLYMOUTH_SERVICES=$(find /etc/init -name 'plymouth*'|grep -v override|sed -re "s:/etc/init/(.*)\.conf:\1:g");
              UPSTART_DISABLED_SERVICES="$PLYMOUTH_SERVICES";
              exit=0;
              for service in $UPSTART_DISABLED_SERVICES;do
                  sf=/etc/init/$service.override;
                  if [[ "$(cat $sf 2>/dev/null)" != "manual" ]];then
                      exit=1;
                  fi;
              done;
              exit $exit
{% endif %}

{#- -------- DEVELOPMENT VM DNS ZONE -------- #}
{%- set vmNum = grains.get('makina.devhost_num', '') %}
{%- set vm_fqdn = grains.get('fqdn','childhost.local') %}
{%- set vm_host = grains.get('host','childhost') %}
{%- set vm_name = vm_fqdn.replace('.', '_').replace(' ', '_') %}
{%- set vm_nat_fqdn = vm_fqdn.split('.')[:1][0]+'-nat.'+'.'.join(vm_fqdn.split('.')[1:]) %}
{%- set ips=grains['ip_interfaces'] %}
{%- set ip1=ips['eth0'] and ips['eth0'][0] or None %}
{%- set ip2=ips['eth1'] and ips['eth1'][0] or None %}
{%- set hostsf='/etc/devhosts' %}
{%- if vmNum and ip1 and ip2 and vm_fqdn and vm_nat_fqdn and vm_host and ips -%}
makina-parent-etc-hosts-absent:
  file.absent:
    - name: {{hostsf}}
    - require_in:
      - file: makina-parent-etc-hosts-exists

{#-
# delete old stalled from import /etc/devhosts
# handle the double zone cases
#}
makina-parent-etc-hosts-exists:
  file.touch:
    - name: {{hostsf}}

makina-append-parent-etc-hosts-management:
  file.blockreplace:
    - name: {{hostsf}}
    - marker_start: '#-- start devhost {{vmNum }} :: DO NOT EDIT --'
    - marker_end: '#-- end devhost {{vmNum }} :: DO NOT EDIT --'
    - content: '# Vagrant vm: {{ vm_fqdn }} added this entry via local mount:'
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - require:
      - file: makina-parent-etc-hosts-exists

{#-
# initialize the accumulator with at least the VM private network socket
# Use this accumulator to add any IP managed on this vm that the parent
# host should know about
#}
makina-parent-append-etc-hosts-accumulated:
  file.accumulated:
    - filename: {{hostsf}}
    - name: parent-hosts-append-accumulator-{{ vm_name }}-entries
    - text: |
            {{ ip2 }} {{ vm_fqdn }} {{ vm_host }}
            {{ ip1 }} {{ vm_nat_fqdn }} {{ vm_host }}-nat
    - require_in:
      - file: makina-append-parent-etc-hosts-management
{% endif %}
