{{- salt['mc_macros.register']('services', 'monitoring.icinga') }}
include:
{#
  - makina-states.services.monitoring.icinga.pgsql
  - makina-states.services.monitoring.icinga.mysql
  - makina-states.services.monitoring.icinga.nginx
  - makina-states.services.monitoring.icinga.prerequisites
#}
  - makina-states.services.monitoring.icinga.configuration
  - makina-states.services.monitoring.icinga.services
{% import "makina-states/services/monitoring/icinga/macros.sls"  as macros %}
{% set add_configuration = macros.add_configuration %}

