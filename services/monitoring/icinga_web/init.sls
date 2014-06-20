{{- salt['mc_macros.register']('services', 'monitoring.icinga_web') }}
{% set data = salt['mc_icinga_web.settings']() %}

include:
  - makina-states.services.monitoring.icinga_web.pgsql
  - makina-states.services.monitoring.icinga_web.mysql
  - makina-states.services.monitoring.icinga_web.nginx
  - makina-states.services.monitoring.icinga_web.prerequisites
  - makina-states.services.monitoring.icinga_web.configuration
  - makina-states.services.monitoring.icinga_web.services
