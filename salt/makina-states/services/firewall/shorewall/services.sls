{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.services.firewall.shorewall.hooks
shorewall-e:
  service.dead:
    - names:
      - shorewall
      - shorewall6
    - enable: False
    - watch_in:
      - mc_proxy: shorewall-prerestart

shorewall-d:
  service.disabled:
    - names:
      - shorewall
      - shorewall6
    - watch_in:
      - mc_proxy: shorewall-prerestart

shorewall-restart:
  cmd.run:
    - name: {{ locs.conf_dir }}/rc.local.d/shorewall.sh fromsalt
    - stateful: True
    - watch:
      - mc_proxy: shorewall-prerestart
    - watch_in:
      - mc_proxy: shorewall-postrestart
{#-
# Disabled as we now use {{ locs.conf_dir }}/rc.local
# shorewall-upstart:
#   file.managed:
#     - name: {{ locs.upstart_dir}}/shorewall-upstart.conf
#     - source : salt://makina-states/files/etc/init/shorewall-upstart.conf
#     - template: jinja
#     - user: root
#     - group: root
#   service.running:
#     - watch:
#       - file: shorewall-upstart
#       - service: shorewall-d
#       - service: shorewall-e
#     - enable: True
#     - watch:
#       - file: shorewall-test-cfg
#}
