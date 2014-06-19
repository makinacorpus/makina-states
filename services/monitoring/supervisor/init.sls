{{- salt['mc_macros.register']('services', 'monitoring.supervisor') }}
include:
  - makina-states.services.monitoring.supervisor.prerequisites
  - makina-states.services.monitoring.supervisor.configuration
  - makina-states.services.monitoring.supervisor.services
