#
# Setup for makina/vms vagrant development machines
#
#  - For VM using external mounts we may need to delay
#     some upstart services until the mounts are ready.
#     for example, on a Vagrant vm, we need to wait for /srv mounted late
#     via NFS
# and most pieces of the LAMP stack needs this /srv directory
#
# To register a service as something needing to wait for this NFS mount
# include this file and add you service name in the
# makina-file_delay_services_for_srv file.accumulated "list_of_services"
# accumulator this way:
#makina-add-apache-in-waiting-for-nfs-services:
#  file.accumulated:
#    - name: list_of_services
#    - filename: /etc/init/delay_services_for_vagrant_nfs.conf
#    - text: apache2
#    - require_in:
#      - file: makina-file_delay_services_for_srv
# where the text part is the name of the service as shown in upstart
# You can see an example of that in the phpfpm.sls or the apache.sls

{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}

{{ nodetypes.register('vagrantvm') }}

include:
  - {{ nodetypes.statesPref }}devhost
  - {{ nodetypes.funcs.statesPref }}services.virt.lxc
  - {{ nodetypes.funcs.statesPref }}services.virt.docker

{% if grains['os'] in ['Ubuntu'] %}
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
