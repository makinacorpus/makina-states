{{- salt['mc_macros.register']('services_managers', 'system') }}
include:
  - makina-states.services_managers.system.prerequisites
  - makina-states.services_managers.system.configuration
  - makina-states.services_managers.system.services
