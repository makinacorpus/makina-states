{{- salt['mc_macros.register']('services_managers', 'supervisor') }}
include:
  - makina-states.services_managers.supervisor.prerequisites
  - makina-states.services_managers.supervisor.configuration
  - makina-states.services_managers.supervisor.services
