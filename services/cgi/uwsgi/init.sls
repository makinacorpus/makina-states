{{- salt['mc_macros.register']('services', 'cgi.uwsgi') }}
include:
  - makina-states.services.cgi.uwsgi.prerequisites
  - makina-states.services.cgi.uwsgi.configuration
  - makina-states.services.cgi.uwsgi.services
{% import "makina-states/services/cgi/uwsgi/macros.sls"  as macros %}
{% set app = macros.app %}

