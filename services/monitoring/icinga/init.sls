{{- salt['mc_macros.register']('services', 'monitoring.icinga') }}
include:
  - makina-states.services.monitoring.icinga.prerequisites
  - makina-states.services.monitoring.icinga.configuration
  - makina-states.services.monitoring.icinga.services
