{{- salt['mc_macros.register']('services', 'monitoring.icinga') }}
include:
  - makina-states.services.monitoring.icinga.pgsql
  - makina-states.services.monitoring.icinga.mysql
  - makina-states.services.monitoring.icinga.nginx
  - makina-states.services.monitoring.icinga.prerequisites
  - makina-states.services.monitoring.icinga.configuration
  - makina-states.services.monitoring.icinga.services
{% import "makina-states/services/monitoring/icinga/macros.sls"  as macros %}
{% set configuration_add_auto_host = macros.configuration_add_auto_host %}
{% set configuration_add_object = macros.configuration_add_object %}
{% set configuration_remove_object = macros.configuration_remove_object %}
{% set configuration_edit_object = macros.configuration_edit_object %}
