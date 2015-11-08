{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('services', 'backup.burp.server') }}
include:
  - makina-states.services.backup.burp.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services.backup.burp.server.prerequisites
  - makina-states.services.backup.burp.server.configuration
  - makina-states.services.backup.burp.server.cron
  - makina-states.services.backup.burp.server.services
  - makina-states.services.firewall.firewall
{% endif %}
