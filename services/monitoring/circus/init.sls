{{- salt['mc_macros.register']('services', 'monitoring.circus') }}
include:
  - makina-states.services.monitoring.circus.prerequisites
  - makina-states.services.monitoring.circus.configuration
  - makina-states.services.monitoring.circus.services
