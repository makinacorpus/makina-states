{{- salt['mc_macros.register']('services', 'monitoring.icinga2') }}
{% set data = salt['mc_icinga2.settings']() %}
include:
{#
  - makina-states.services.monitoring.icinga2.mysql
  - makina-states.services.monitoring.icinga2.nginx
#}
  - makina-states.services.monitoring.client
{% if data.has_pgsql %}
  - makina-states.services.monitoring.icinga2.icingadb_mysql
{% endif %}
  - makina-states.services.monitoring.icinga2.prerequisites
  - makina-states.services.monitoring.icinga2.configuration
  - makina-states.services.monitoring.icinga2.services
  - makina-states.services.monitoring.icinga2.ircbot
{% import "makina-states/services/monitoring/icinga2/macros.sls"  as macros %}
{% set configuration_add_auto_host = macros.configuration_add_auto_host %}
{% set configuration_add_object = macros.configuration_add_object %}
{% set configuration_remove_object = macros.configuration_remove_object %}


