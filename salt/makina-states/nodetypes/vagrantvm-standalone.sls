{#Flag the machine as a development vagrant box, setup lxc & k8s #}
{% set ugs = salt['mc_usergroup.settings']() %}
{%- set vmNum = grains.get('makina.devhost_num', '') %}
{%- set vm_fqdn = grains.get('fqdn','childhost.local') %}
{%- set vm_host = grains.get('host','childhost') %}
{%- set vm_name = vm_fqdn.replace('.', '_').replace(' ', '_') %}
{%- set vm_nat_fqdn = vm_fqdn.split('.')[:1][0]+'-nat.'+'.'.join(vm_fqdn.split('.')[1:]) %}
{%- set ips=grains['ip_interfaces'] %}
{%- set ip1 = (ips.get('eth0', [])) and ips['eth0'][0] or None %}
{%- set ip2 = (ips.get('eth1', [])) and ips['eth1'][0] or None %}
{%- set hostsf='/etc/devhosts' %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'vagrantvm') }}
{% if full %}
include:
  - makina-states.localsettings.users
  - makina-states.nodetypes.devhost
{% endif %}
# add vagrant to editor
addvagrant-to-editor:
  user.present:
    - name: vagrant
    - optional_groups:
      - {{ugs.group}}
    - remove_groups: false

sudo-vagrant:
  file.managed:
    - name: /etc/sudoers.d/vagrant
    - source: ''
    - contents: 'vagrant ALL=NOPASSWD: ALL'
    - mode: 0440
    - user: root
    - group: root

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
{% endmacro %}
{{do(full=False)}}
