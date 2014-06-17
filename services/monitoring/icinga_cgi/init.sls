{{- salt['mc_macros.register']('services', 'monitoring.icinga_cgi') }}
include:
  - makina-states.services.monitoring.icinga_cgi.nginx
  - makina-states.services.monitoring.icinga_cgi.prerequisites
  - makina-states.services.monitoring.icinga_cgi.configuration
  - makina-states.services.monitoring.icinga_cgi.services
