{#
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
#}

{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ salt['mc_macros.register']('nodetypes', 'travis') }}
{% set localsettings = nodetypes.localsettings %}

include:
  - makina-states.nodetypes.devhost
