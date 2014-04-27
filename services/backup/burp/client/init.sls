{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('services', 'backup.burp.client') }}
include:
  - makina-states.services.backup.burp.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.services.backup.burp.server.prerequisites
{% endif %}
