{{- salt['mc_macros.register']('services', 'monitoring.icinga_web2') }}
include:
  - makina-states.services.monitoring.icinga_web2.pgsql
  - makina-states.services.monitoring.icinga_web2.nginx
  - makina-states.services.monitoring.icinga_web2.prerequisites
  - makina-states.services.monitoring.icinga_web2.configuration
  - makina-states.services.monitoring.icinga_web2.services
