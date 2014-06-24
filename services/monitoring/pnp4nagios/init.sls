{{- salt['mc_macros.register']('services', 'monitoring.pnp4nagios') }}
{% set data = salt['mc_pnp4nagios.settings']() %}

include:
  - makina-states.services.monitoring.icinga
  - makina-states.services.monitoring.pnp4nagios.nginx
  - makina-states.services.monitoring.pnp4nagios.prerequisites
  - makina-states.services.monitoring.pnp4nagios.configuration
  - makina-states.services.monitoring.pnp4nagios.services
