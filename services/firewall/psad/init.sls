{%- set locs = salt['mc_locations.settings']()%}
{{ salt['mc_macros.register']('services', 'firewall.psad') }}
include:
  - makina-states.services.firewall.psad.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services.firewall.psad.prerequisites
  - makina-states.services.firewall.psad.configuration
  - makina-states.services.firewall.psad.services
{% endif %}
