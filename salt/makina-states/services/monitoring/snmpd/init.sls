{{ salt['mc_macros.register']('services', 'monitoring.snmpd') }}
include:
  - makina-states.services.monitoring.snmpd.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services.monitoring.snmpd.prerequisites
  - makina-states.services.monitoring.snmpd.configuration
  - makina-states.services.monitoring.snmpd.services
{% endif %}
