{#- Compat wrapper to shorewall services
# use now directlyh the 2 states
#}
include:
  - makina-states.services.virt.docker
  - makina-states.services.firewall.firewall
{{ salt['mc_macros.register']('services', 'virt.docker-shorewall') }}
