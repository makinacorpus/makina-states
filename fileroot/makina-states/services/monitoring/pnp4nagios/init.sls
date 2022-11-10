{{- salt['mc_macros.register']('services', 'monitoring.pnp4nagios') }}
include:
  - makina-states.services.monitoring.pnp4nagios.fpm
  - makina-states.services.monitoring.pnp4nagios.nginx
  - makina-states.services.monitoring.pnp4nagios.prerequisites
  - makina-states.services.monitoring.pnp4nagios.configuration
  - makina-states.services.monitoring.pnp4nagios.services
