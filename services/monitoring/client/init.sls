{{- salt['mc_macros.register']('services', 'monitoring.client') }}
include:
  - makina-states.services.monitoring.client.scripts
