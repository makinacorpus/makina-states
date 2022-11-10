{{ salt['mc_macros.register']('services', 'proxy.haproxy') }}
{% set settings = salt['mc_haproxy.settings']() %}
include:
  - makina-states.localsettings.ssl
  {% if settings.use_rsyslog %}
  - makina-states.services.log.rsyslog
  {% endif%}
  - makina-states.services.proxy.haproxy.prerequisites
  - makina-states.services.proxy.haproxy.configuration
  - makina-states.services.proxy.haproxy.services
