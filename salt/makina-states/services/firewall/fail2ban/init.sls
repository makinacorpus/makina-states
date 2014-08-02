
{# Shorewall configuration
# Documentation
# - doc/ref/formulaes/services/firewall/fail2ban.rst
#}
{%- set locs = salt['mc_locations.settings']()%}
{{ salt['mc_macros.register']('services', 'firewall.fail2ban') }}
include:
  - makina-states.services.firewall.fail2ban.hooks
  - makina-states.services.firewall.fail2ban.prerequisites
  - makina-states.services.firewall.fail2ban.configuration
  - makina-states.services.firewall.fail2ban.services
