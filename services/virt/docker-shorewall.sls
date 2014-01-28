{#-
# LXC and shorewall integration, be sure to add
# docker guests to shorewall running state
# upon creation
# A big sentence to say, restart shorewall
# after each docker creation to enable
# the container network
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'virt.docker-shorewall') }}
{%- set localsettings = services.localsettings %}
{%- set locs = localsettings.locations %}
include:
  - makina-states.services.firewall.shorewall
  - makina-states.services.virt.docker

docker-shorewall-post-inst:
  cmd.run:
    - name: /bin/true
    - unless: /bin/true
    - require:
      - cmd:  docker-post-inst
    - watch_in:
      - cmd: shorewall-restart
