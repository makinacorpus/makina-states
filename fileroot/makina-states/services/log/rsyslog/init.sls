{{ salt['mc_macros.register']('services', 'log.rsyslog') }}
include:
  - makina-states.services.log.rsyslog.hooks
{% if (
not salt['mc_nodetypes.is_docker']()) %}
  - makina-states.services.log.rsyslog.prerequisites
  - makina-states.services.log.rsyslog.configuration
  - makina-states.services.log.rsyslog.services
{%endif%}
