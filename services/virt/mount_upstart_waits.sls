#
# For VM using external mounts we may need to delay some upstart services until the mounts are Ready
#
# For example, on a Vagrant vm, we need to wait for /srv mounted late via NFS
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

{% if grains['makina.nodetype.devhost'] %}

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