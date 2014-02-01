{#- Compat wrapper to shorewall services
# use now directlyh the 2 states
#}
include:
  - makina-states.services.virt.docker
  - makina-states.services.firewall.shorewall
{%- import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'virt.docker-shorewall') }}
