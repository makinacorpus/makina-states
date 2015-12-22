{{- salt['mc_macros.register']('services_managers', 'circus') }}
include:
  - makina-states.services_managers.circus.prerequisites
  - makina-states.services_managers.circus.configuration
  - makina-states.services_managers.circus.services
