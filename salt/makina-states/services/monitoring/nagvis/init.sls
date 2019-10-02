{{- salt['mc_macros.register']('services', 'monitoring.nagvis') }}
include:
  - makina-states.services.monitoring.nagvis.hooks
# install of nagvis is done manually in /usr/share
# fpm pool & web vhost  is exposed through icingaweb2 !
  #- makina-states.services.monitoring.nagvis.nginx
  #- makina-states.services.monitoring.nagvis.prerequisites
  #- makina-states.services.monitoring.nagvis.configuration
#  - makina-states.services.monitoring.nagvis.services
{% import "makina-states/services/monitoring/nagvis/macros.sls"  as macros %}
{% set add_map = macros.add_map %}
{% set add_geomap = macros.add_geomap %}
