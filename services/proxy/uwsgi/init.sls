{{- salt['mc_macros.register']('services', 'proxy.uwsgi') }}
include:
  - makina-states.services.proxy.uwsgi.prerequisites
  - makina-states.services.proxy.uwsgi.configuration
  - makina-states.services.proxy.uwsgi.services
{% import "makina-states/services/proxy/uwsgi/macros.sls"  as macros %}
{% set config = macros.config %}

