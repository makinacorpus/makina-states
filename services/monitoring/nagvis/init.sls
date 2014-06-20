{{- salt['mc_macros.register']('services', 'monitoring.nagvis') }}
{% set data = salt['mc_nagvis.settings']() %}

include:
  - makina-states.services.monitoring.nagvis.nginx
  - makina-states.services.monitoring.nagvis.prerequisites
  - makina-states.services.monitoring.nagvis.configuration
  - makina-states.services.monitoring.nagvis.services
